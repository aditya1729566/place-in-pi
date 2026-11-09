#!/usr/bin/env python3
"""Build and query a version-bound fixed-prefix SQLite postings index."""
import argparse
import hashlib
import json
import mmap
import os
import sqlite3
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.corpus import load_corpus  # noqa: E402


def build(corpus_dir: Path, output: Path, prefix_length: int = 4):
    if prefix_length < 4 or prefix_length > 6:
        raise ValueError("prefix length must be 4–6")
    corpus = load_corpus(corpus_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    db = sqlite3.connect(temporary)
    try:
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("CREATE TABLE postings (prefix INTEGER NOT NULL, pos INTEGER NOT NULL)")
        for key, value in {"version": corpus["version"], "sha256": corpus["sha256"], "digits": str(corpus["digits"]), "prefix_length": str(prefix_length)}.items():
            db.execute("INSERT INTO meta VALUES (?, ?)", (key, value))
        carry = b""
        processed = 0
        batch = []
        for path in corpus["paths"]:
            with Path(path).open("rb") as stream:
                for chunk in iter(lambda: stream.read(1 << 20), b""):
                    data = carry + chunk
                    base = processed - len(carry)
                    for index in range(len(data) - prefix_length + 1):
                        batch.append((int(data[index:index + prefix_length]), base + index + 1))
                        if len(batch) >= 50_000:
                            db.executemany("INSERT INTO postings VALUES (?, ?)", batch)
                            batch.clear()
                    carry = data[-(prefix_length - 1):]
                    processed += len(chunk)
        if batch:
            db.executemany("INSERT INTO postings VALUES (?, ?)", batch)
        db.execute("CREATE INDEX postings_lookup ON postings(prefix, pos)")
        db.commit()
    finally:
        db.close()
    os.replace(temporary, output)
    digest = hashlib.sha256()
    with output.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    sidecar = {"index_sha256": digest.hexdigest(), "corpus_version": corpus["version"], "entries": corpus["digits"] - prefix_length + 1}
    sidecar_tmp = output.with_suffix(output.suffix + ".json.tmp")
    sidecar_tmp.write_text(json.dumps(sidecar, indent=2) + "\n")
    os.replace(sidecar_tmp, output.with_suffix(output.suffix + ".json"))
    return {"index": str(output), "bytes": output.stat().st_size, **sidecar}


class IndexReader:
    def __init__(self, corpus_dir: Path, index_path: Path):
        self.corpus = load_corpus(corpus_dir)
        sidecar = json.loads(index_path.with_suffix(index_path.suffix + ".json").read_text())
        digest = hashlib.sha256()
        with index_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                digest.update(chunk)
        if digest.hexdigest() != sidecar.get("index_sha256") or sidecar.get("corpus_version") != self.corpus["version"]:
            raise ValueError("index file hash or corpus version mismatch")
        self.db = sqlite3.connect(f"file:{index_path}?mode=ro", uri=True, check_same_thread=False)
        self.lock = threading.Lock()
        self.meta = dict(self.db.execute("SELECT key, value FROM meta"))
        if self.meta.get("version") != self.corpus["version"] or self.meta.get("sha256") != self.corpus["sha256"] or self.meta.get("digits") != str(self.corpus["digits"]):
            self.db.close()
            raise ValueError("index does not match corpus")
        self.prefix_length = int(self.meta["prefix_length"])
        expected_count = self.corpus["digits"] - self.prefix_length + 1
        if sidecar.get("entries") != expected_count or self.db.execute("SELECT COUNT(*) FROM postings").fetchone()[0] != expected_count:
            self.db.close()
            raise ValueError("index posting count mismatch")
        self.maps = []
        for shard, path in zip(self.corpus["shards"], self.corpus["paths"]):
            stream = Path(path).open("rb")
            self.maps.append((shard["start"], mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ), stream))

    def read(self, position: int, count: int) -> bytes:
        remaining = count
        output = bytearray()
        for start, mapped, _ in self.maps:
            end = start + len(mapped)
            if position >= end or position + remaining <= start:
                continue
            local = max(position, start) - start
            take = min(remaining, len(mapped) - local)
            output.extend(mapped[local:local + take])
            remaining -= take
            position += take
            if not remaining:
                break
        return bytes(output)

    def search(self, pattern: str, offset: int = 0, limit: int = 100):
        if len(pattern) < self.prefix_length or not pattern.isascii() or not pattern.isdecimal():
            raise ValueError("pattern is shorter than index prefix or not decimal")
        expected = pattern.encode("ascii")
        total = 0
        first = None
        page = []
        with self.lock:
            for (position,) in self.db.execute("SELECT pos FROM postings WHERE prefix=? ORDER BY pos", (int(pattern[:self.prefix_length]),)):
                if position + len(pattern) - 1 > self.corpus["digits"]:
                    continue
                if self.read(position, len(pattern)) == expected:
                    if first is None:
                        first = position
                    if total >= offset and len(page) < limit:
                        page.append(position)
                    total += 1
        return {"total": total, "first": first, "matches": page}

    def close(self):
        with self.lock:
            for _, mapped, stream in self.maps:
                mapped.close()
                stream.close()
            self.db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=ROOT / "data/corpus")
    parser.add_argument("--out", type=Path, default=ROOT / "data/index/pi-prefix-4.sqlite")
    parser.add_argument("--prefix-length", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(build(args.corpus, args.out, args.prefix_length), indent=2))
