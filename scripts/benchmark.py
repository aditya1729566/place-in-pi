#!/usr/bin/env python3
"""Compare exact KMP scan and verified fixed-prefix postings on the loaded corpus."""
import argparse
import json
import platform
import statistics
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))
from app.corpus import load_corpus  # noqa: E402
from app.worker import SearchWorker  # noqa: E402
from prefix_index import IndexReader  # noqa: E402


def summarize(values):
    ordered = sorted(values)
    return {"mean_ms": round(statistics.mean(values), 3), "p50_ms": round(statistics.median(values), 3), "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=ROOT / "data/corpus")
    parser.add_argument("--index", type=Path, default=ROOT / "data/index/pi-prefix-4.sqlite")
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()
    corpus = load_corpus(args.corpus)
    index = IndexReader(args.corpus, args.index)
    worker = SearchWorker(ROOT / "engine/build/pi_search", [Path(path) for path in corpus["paths"]])
    try:
        patterns = ["1415", "1609", "14159265", "141592653589", "14159265358979323846", "000000000000"]
        results = []
        for pattern in patterns:
            scan_times, index_times = [], []
            scan_result = index_result = None
            for _ in range(args.repeats):
                began = perf_counter()
                scan_result = worker.scan(pattern, 0, 100, 120000)
                scan_times.append((perf_counter() - began) * 1000)
                began = perf_counter()
                index_result = index.search(pattern, 0, 100)
                index_times.append((perf_counter() - began) * 1000)
            if scan_result["observed_count"] != index_result["total"] or scan_result["first_position"] != index_result["first"] or scan_result["matches"] != index_result["matches"]:
                raise RuntimeError(f"index disagrees with scan for {pattern}")
            results.append({"pattern": pattern, "length": len(pattern), "matches": index_result["total"], "scan": summarize(scan_times), "index": summarize(index_times)})
        print(json.dumps({"corpus_version": corpus["version"], "corpus_sha256": corpus["sha256"], "digits": corpus["digits"], "index_bytes": args.index.stat().st_size, "python": sys.version.split()[0], "host": platform.platform(), "repeats": args.repeats, "results": results}, indent=2))
    finally:
        worker.close()
        index.close()


if __name__ == "__main__":
    main()
