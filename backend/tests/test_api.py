import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.corpus import load_corpus
from app.main import app

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    with TestClient(app) as web:
        yield web


def test_real_corpus_search_and_context(client):
    assert client.get("/api/health").json()["status"] == "ready"
    corpus = client.get("/api/corpus").json()
    assert corpus["digits"] == 1_000_000
    result = client.post("/api/search", json={"text": "PI"}).json()
    assert result["query"]["encoded_pattern"] == "1609"
    assert result["execution"]["method"] == "prefix-4"
    assert result["result"]["first_position"] == 396
    assert result["result"]["count_complete"] is True
    assert client.get("/api/digits?start=396&count=4").json()["digits"] == "1609"
    assert client.post("/api/search", json={"text": "A"}).json()["execution"]["method"] == "kmp-scan"


def test_cursor_and_validation(client):
    first = client.post("/api/search", json={"text": "PI", "limit": 2}).json()
    second = client.post("/api/search", json={"text": "PI", "limit": 2, "cursor": first["result"]["next_cursor"]}).json()
    assert first["result"]["matches"] == [396, 791]
    assert second["result"]["matches"][0] == 21562
    assert client.post("/api/search", json={"text": "ADA", "cursor": first["result"]["next_cursor"]}).status_code == 422
    assert client.post("/api/search", json={"text": "PI", "cursor": "@@invalid@@"}).status_code == 422
    assert client.post("/api/encode", json={"text": "π", "profile_id": "latin-a1z26-v1"}).status_code == 422
    assert client.get("/api/digits?start=1000000&count=2").status_code == 422


def test_corrupt_shard_is_rejected(tmp_path):
    source = ROOT / "data/corpus"
    manifest = json.loads((source / "manifest.json").read_text())
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    name = manifest["shards"][0]["file"]
    shutil.copy(source / name, tmp_path / name)
    with (tmp_path / name).open("r+b") as stream:
        stream.seek(500)
        stream.write(b"X")
    with pytest.raises(ValueError):
        load_corpus(tmp_path)


def test_import_creates_verified_shards(tmp_path):
    source_manifest = json.loads((ROOT / "data/corpus/manifest.json").read_text())
    source_file = ROOT / "data/corpus" / source_manifest["shards"][0]["file"]
    plain = tmp_path / "source.txt"
    plain.write_bytes(b"3." + source_file.read_bytes()[:2500])
    target = tmp_path / "prepared"
    subprocess.run([sys.executable, str(ROOT / "scripts/prepare_corpus.py"), "--input", str(plain), "--digits", "2500", "--shard-size", "1000", "--out", str(target)], check=True, capture_output=True)
    loaded = load_corpus(target)
    assert [shard["digits"] for shard in loaded["shards"]] == [1000, 1000, 500]
    from app.worker import SearchWorker
    worker = SearchWorker(ROOT / "engine/build/pi_search", [Path(path) for path in loaded["paths"]])
    try:
        assert worker.digits(998, 8) == source_file.read_bytes()[997:1005].decode()
        pattern = worker.digits(998, 8)
        assert 998 in worker.scan(pattern, 0, 100)["matches"]
    finally:
        worker.close()
    prefix_target = tmp_path / "prefix"
    subprocess.run([sys.executable, str(ROOT / "scripts/prepare_corpus.py"), "--input", str(plain), "--digits", "2000", "--take-prefix", "--shard-size", "1000", "--out", str(prefix_target)], check=True, capture_output=True)
    prefix = load_corpus(prefix_target)
    assert prefix["digits"] == 2000 and prefix["source_digits"] == 2500 and prefix["prefix_taken"] is True
