"""Verify the exact immutable corpus named by a manifest."""
import hashlib
import json
from pathlib import Path

PREFIX = b"14159265358979323846264338327950288419716939937510"
FIRST_1000_SHA256 = "808b01bd3137f0fd50877c7ad44b2a97478666390780372803859749172292bd"
CHECKPOINTS = {
    9951: b"46101264836999892256959688159205600101655256375678",
    11951: b"66830082383404656475880405138080163363887421637140",
    49951: b"06526234053394391421112718106910522900246574236041",
}


def load_corpus(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    shards = manifest.get("shards")
    if not isinstance(shards, list) or not shards:
        raise ValueError("manifest has no shards")
    digest = hashlib.sha256()
    size = 0
    paths = []
    for shard in shards:
        name = shard.get("file")
        if not isinstance(name, str) or Path(name).name != name or shard.get("start") != size + 1:
            raise ValueError("invalid shard name or offset")
        path = directory / name
        paths.append(str(path))
        shard_hash = hashlib.sha256()
        shard_size = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                if any(byte < 48 or byte > 57 for byte in chunk):
                    raise ValueError("corpus contains non-decimal bytes")
                digest.update(chunk)
                shard_hash.update(chunk)
                shard_size += len(chunk)
        if shard_size != shard.get("digits") or shard_hash.hexdigest() != shard.get("sha256"):
            raise ValueError("shard count or SHA-256 mismatch")
        size += shard_size
    if size != manifest.get("digits") or digest.hexdigest() != manifest.get("sha256"):
        raise ValueError("corpus count or SHA-256 mismatch")
    def read_window(position, length):
        output = bytearray()
        for shard, path in zip(shards, paths):
            end = shard["start"] + shard["digits"] - 1
            if position > end or position + length - 1 < shard["start"]:
                continue
            with Path(path).open("rb") as stream:
                local = max(position, shard["start"])
                stream.seek(local - shard["start"])
                output.extend(stream.read(min(end - local + 1, length - len(output))))
        return bytes(output)
    if read_window(1, len(PREFIX)) != PREFIX:
        raise ValueError("π prefix mismatch")
    if size >= 1000 and hashlib.sha256(read_window(1, 1000)).hexdigest() != FIRST_1000_SHA256:
        raise ValueError("independent π prefix mismatch")
    for position, expected in CHECKPOINTS.items():
        if size >= position + len(expected) - 1 and read_window(position, len(expected)) != expected:
            raise ValueError(f"published π checkpoint mismatch at {position}")
    if not str(manifest.get("version", "")).startswith(f"pi-{size}-{digest.hexdigest()[:16]}"):
        raise ValueError("corpus version mismatch")
    return {**manifest, "paths": paths}
