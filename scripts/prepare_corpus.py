#!/usr/bin/env python3
"""Import an explicitly sourced π prefix into an immutable, checked manifest."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen
from datetime import datetime, timezone

DEFAULT_URL = "https://pi2e.ch/blog/wp-content/uploads/2017/03/pi_dec_1m.txt"
PREFIX = b"14159265358979323846264338327950288419716939937510"
FIRST_1000_SHA256 = "808b01bd3137f0fd50877c7ad44b2a97478666390780372803859749172292bd"
CHECKPOINTS = {
    9951: b"46101264836999892256959688159205600101655256375678",
    11951: b"66830082383404656475880405138080163363887421637140",
    49951: b"06526234053394391421112718106910522900246574236041",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--url", help="Source URL; defaults to the published 1M file")
    source.add_argument("--input", type=Path, help="Already downloaded plain-text source")
    parser.add_argument("--digits", type=int, default=1_000_000)
    parser.add_argument("--take-prefix", action="store_true", help="Use only the first N digits of a longer source, while hashing and validating the full source")
    parser.add_argument("--shard-size", type=int, default=10_000_000)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data/corpus")
    parser.add_argument("--expected-source-sha256", help="Optional externally published hash")
    args = parser.parse_args()
    if not 1 <= args.digits <= 100_000_000_000:
        parser.error("--digits must be between 1 and 100 billion")
    if not 1000 <= args.shard_size <= 1_000_000_000:
        parser.error("--shard-size must be between 1,000 and 1 billion")
    if args.url is None and args.input is None and args.digits != 1_000_000:
        parser.error("larger imports need --url or --input")
    url = args.url or (None if args.input else DEFAULT_URL)
    args.out.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="pi-import-", dir=args.out)
    os.close(fd)
    temp = Path(temp_name)
    original_hash = hashlib.sha256()
    digits_hash = hashlib.sha256()
    source_bytes = 0
    digits = 0
    source_digits = 0
    prefix_probe = bytearray()
    prefix_decided = False
    try:
        with (urlopen(url, timeout=60) if url else args.input.open("rb")) as src, temp.open("wb") as dst:
            for chunk in iter(lambda: src.read(1 << 20), b""):
                original_hash.update(chunk)
                source_bytes += len(chunk)
                clean = bytearray()
                for b in chunk:
                    if b in b" \t\r\n":
                        continue
                    if not prefix_decided:
                        prefix_probe.append(b)
                        if len(prefix_probe) < 2:
                            continue
                        if prefix_probe != b"3.":
                            clean.extend(prefix_probe)
                        prefix_probe.clear()
                        prefix_decided = True
                        continue
                    clean.append(b)
                if clean:
                    if any(b < 48 or b > 57 for b in clean):
                        raise ValueError("source contains non-decimal content")
                    source_digits += len(clean)
                    if source_digits > args.digits and not args.take_prefix:
                        raise ValueError("source contains more digits than requested; provide an exact prefix file")
                    selected = clean[:max(0, args.digits - digits)]
                    digits += len(selected)
                    dst.write(selected)
                    digits_hash.update(selected)
        if digits != args.digits:
            raise ValueError(f"expected {args.digits} digits; got {digits}")
        with temp.open("rb") as file:
            if file.read(len(PREFIX)) != PREFIX:
                raise ValueError("known π prefix mismatch")
            if args.digits >= 1000:
                file.seek(0)
                if hashlib.sha256(file.read(1000)).hexdigest() != FIRST_1000_SHA256:
                    raise ValueError("independently computed 1,000-digit prefix mismatch")
            for position, expected in CHECKPOINTS.items():
                if args.digits >= position + len(expected) - 1:
                    file.seek(position - 1)
                    if file.read(len(expected)) != expected:
                        raise ValueError(f"published π checkpoint mismatch at position {position}")
        original_digest = original_hash.hexdigest()
        if args.expected_source_sha256 and original_digest.lower() != args.expected_source_sha256.lower():
            raise ValueError("source SHA-256 mismatch")
        digest = digits_hash.hexdigest()
        version = f"pi-{digits}-{digest[:16]}"
        shards = []
        with temp.open("rb") as source:
            start = 1
            index = 0
            while start <= digits:
                name = f"{version}-{index:04d}.digits"
                shard_path = args.out / name
                shard_hash = hashlib.sha256()
                length = 0
                with shard_path.open("wb") as shard:
                    while length < args.shard_size:
                        chunk = source.read(min(1 << 20, args.shard_size - length))
                        if not chunk:
                            break
                        shard.write(chunk)
                        shard_hash.update(chunk)
                        length += len(chunk)
                shards.append({"file": name, "start": start, "digits": length, "sha256": shard_hash.hexdigest()})
                start += length
                index += 1
        manifest = {
            "constant": "pi", "version": version, "position_basis": "1-indexed after decimal",
            "digits": digits, "shards": shards, "sha256": digest,
            "source": url or str(args.input.resolve()), "source_sha256": original_digest,
            "source_bytes": source_bytes, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "source_digits": source_digits, "prefix_taken": source_digits > digits,
            "verification": {"known_prefix_50": True, "independent_prefix_1000": args.digits >= 1000, "published_checkpoints": [p for p in CHECKPOINTS if args.digits >= p + 49], "source_sha256_checked": bool(args.expected_source_sha256)},
        }
        manifest_tmp = args.out / "manifest.json.tmp"
        manifest_tmp.write_text(json.dumps(manifest, indent=2) + "\n")
        os.replace(manifest_tmp, args.out / "manifest.json")
        print(json.dumps(manifest, indent=2))
    finally:
        temp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
