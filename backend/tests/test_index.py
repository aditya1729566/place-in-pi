import json
import random
import subprocess
import sys
from pathlib import Path

from scripts.prefix_index import IndexReader, build

ROOT = Path(__file__).resolve().parents[2]


def test_index_matches_brute_force_on_sharded_prefix(tmp_path):
    manifest = json.loads((ROOT / "data/corpus/manifest.json").read_text())
    raw = (ROOT / "data/corpus" / manifest["shards"][0]["file"]).read_bytes()[:2500]
    source = tmp_path / "pi.txt"
    source.write_bytes(b"3." + raw)
    corpus_dir = tmp_path / "corpus"
    subprocess.run([sys.executable, str(ROOT / "scripts/prepare_corpus.py"), "--input", str(source), "--digits", "2500", "--shard-size", "1000", "--out", str(corpus_dir)], check=True, capture_output=True)
    index_path = tmp_path / "index.sqlite"
    build(corpus_dir, index_path)
    reader = IndexReader(corpus_dir, index_path)
    try:
        digits = raw.decode()
        rng = random.Random(2026)
        patterns = [digits[index:index + length] for index, length in [(997, 8), (1998, 6)] + [(rng.randrange(0, 2450), rng.randrange(4, 12)) for _ in range(20)]] + ["000000000000"]
        for pattern in patterns:
            expected = [index + 1 for index in range(len(digits) - len(pattern) + 1) if digits.startswith(pattern, index)]
            actual = reader.search(pattern)
            assert actual["total"] == len(expected)
            assert actual["first"] == (expected[0] if expected else None)
            assert actual["matches"] == expected[:100]
    finally:
        reader.close()
