"""Pi Dictionary HTTP API."""
import base64
import binascii
import hashlib
import json
import os
import sqlite3
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .corpus import load_corpus
from .encoding import EncodingError, LATIN, PROFILES, encode
from .worker import SearchWorker, WorkerError
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.prefix_index import IndexReader

CORPUS_DIR = Path(os.getenv("PI_CORPUS_DIR", ROOT / "data/corpus"))
ENGINE_BIN = Path(os.getenv("PI_ENGINE_BIN", ROOT / "engine/build/pi_search"))
INDEX_FILE = Path(os.getenv("PI_INDEX_FILE", ROOT / "data/index/pi-prefix-4.sqlite"))
state = {"corpus": None, "worker": None, "index": None, "index_error": None, "error": None}
rate_lock = Lock()
rate_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.update(corpus=None, worker=None, index=None, index_error=None, error=None)
    try:
        corpus = load_corpus(CORPUS_DIR)
        if not ENGINE_BIN.is_file():
            raise FileNotFoundError("Search worker binary is missing. Build the engine first.")
        state.update(corpus=corpus, worker=SearchWorker(ENGINE_BIN, [Path(path) for path in corpus["paths"]]), error=None)
        if state["worker"].command("PING") != ["PONG", str(corpus["digits"])]:
            raise WorkerError("Worker corpus length mismatch.")
        if INDEX_FILE.is_file():
            try:
                state["index"] = IndexReader(CORPUS_DIR, INDEX_FILE)
                state["index_error"] = None
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                state["index"] = None
                state["index_error"] = str(exc)
    except (OSError, ValueError, json.JSONDecodeError, WorkerError) as exc:
        if state["worker"]:
            state["worker"].close()
        state.update(corpus=None, worker=None, error=str(exc))
    yield
    if state["worker"]:
        state["worker"].close()
    if state["index"]:
        state["index"].close()


app = FastAPI(title="Pi Dictionary API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("PI_CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
)


class EncodeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=128)
    profile_id: str = LATIN
    letters_only: bool = True


class SearchRequest(EncodeRequest):
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None


@app.middleware("http")
async def body_limit(request: Request, call_next):
    try:
        length = int(request.headers.get("content-length", "0"))
    except ValueError:
        return JSONResponse({"detail": "Invalid content length."}, status_code=400)
    if length > 4096:
        return JSONResponse({"detail": "Request body is too large."}, status_code=413)
    return await call_next(request)


def ready():
    if not state["worker"] or not state["corpus"]:
        raise HTTPException(503, "Verified corpus or search worker is unavailable.")
    return state["corpus"], state["worker"]


def checked_encoding(text: str, profile_id: str, letters_only: bool):
    try:
        return encode(text, profile_id, letters_only)
    except EncodingError as exc:
        raise HTTPException(422, str(exc)) from exc


def throttle(request: Request):
    address = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with rate_lock:
        if len(rate_state) > 10000:
            for key in list(rate_state):
                if not any(now - item < 60 for item in rate_state[key]):
                    del rate_state[key]
        timestamps = [item for item in rate_state.get(address, []) if now - item < 60]
        if len(timestamps) >= 60:
            raise HTTPException(429, "Search limit reached. Retry in a minute.")
        timestamps.append(now)
        rate_state[address] = timestamps


def cursor_decode(cursor: str, pattern: str, version: str) -> int:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        if data.get("p") != hashlib.sha256(pattern.encode()).hexdigest()[:16] or data.get("v") != version:
            raise ValueError("cursor does not match this query and corpus")
        offset = data["o"]
        if type(offset) is not int or offset < 0 or offset > 100_000_000_000:
            raise ValueError("invalid cursor offset")
        return offset
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, binascii.Error) as exc:
        raise HTTPException(422, "Invalid or stale result cursor.") from exc


def cursor_encode(pattern: str, version: str, offset: int) -> str:
    payload = {"p": hashlib.sha256(pattern.encode()).hexdigest()[:16], "v": version, "o": offset}
    return base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")


@app.get("/api/health")
def health():
    return {"status": "ready" if state["worker"] else "degraded", "corpus_ready": bool(state["corpus"]), "worker_ready": bool(state["worker"]), "index_ready": bool(state["index"]), "index_error": state["index_error"], "detail": state["error"]}


@app.get("/api/corpus")
def corpus_info():
    corpus, _ = ready()
    return {"constant": "pi", "version": corpus["version"], "digits": corpus["digits"], "position_basis": corpus["position_basis"], "sha256": corpus["sha256"], "source": corpus["source"]}


@app.get("/api/encodings")
def encodings():
    return {"profiles": list(PROFILES.values())}


@app.post("/api/encode")
def encode_route(body: EncodeRequest):
    return checked_encoding(body.text, body.profile_id, body.letters_only)


@app.post("/api/search")
def search(body: SearchRequest, request: Request):
    throttle(request)
    corpus, worker = ready()
    query = checked_encoding(body.text, body.profile_id, body.letters_only)
    pattern = query["encoded_pattern"]
    offset = cursor_decode(body.cursor, pattern, corpus["version"]) if body.cursor else 0
    result = None
    if state["index"] and len(pattern) >= state["index"].prefix_length:
        try:
            began = time.perf_counter()
            indexed = state["index"].search(pattern, offset, body.limit)
            result = {"complete": True, "observed_count": indexed["total"], "first_position": indexed["first"], "elapsed_ms": round((time.perf_counter() - began) * 1000, 3), "matches": indexed["matches"]}
            method = f"prefix-{state['index'].prefix_length}"
        except (sqlite3.DatabaseError, OSError, ValueError) as exc:
            state["index_error"] = str(exc)
            state["index"].close()
            state["index"] = None
    if result is None:
        try:
            result = worker.scan(pattern, offset, body.limit)
        except WorkerError as exc:
            raise HTTPException(503, str(exc)) from exc
        method = "kmp-scan"
    complete = result["complete"]
    total = result["observed_count"] if complete else None
    next_cursor = cursor_encode(pattern, corpus["version"], offset + len(result["matches"])) if complete and offset + len(result["matches"]) < total else None
    return {
        "query": query,
        "corpus": {"constant": "pi", "version": corpus["version"], "digits_searched": corpus["digits"], "position_basis": corpus["position_basis"]},
        "result": {"found": bool(result["first_position"]), "first_position": result["first_position"], "matches": result["matches"], "total_matches": total, "count_complete": complete, "positions_complete": complete and next_cursor is None, "next_cursor": next_cursor},
        "execution": {"method": method, "complete": complete, "elapsed_ms": result["elapsed_ms"]},
    }


@app.get("/api/digits")
def digits(start: int = Query(ge=1), count: int = Query(ge=1, le=4096)):
    corpus, worker = ready()
    if start > corpus["digits"] or count > corpus["digits"] - start + 1:
        raise HTTPException(422, "Digit window exceeds verified coverage.")
    try:
        value = worker.digits(start, count)
    except WorkerError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"start": start, "count": count, "digits": value, "version": corpus["version"]}
