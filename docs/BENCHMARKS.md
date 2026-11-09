# Measured search performance

Run on 2026-11-09 on macOS 26.6.2 arm64, Python 3.14.6, AppleClang 21, release `-O3` build. Corpus: 1,000,000 decimal digits, version `pi-1000000-7806ee47461b49ef`, SHA-256 `7806ee47461b49ef1f578e14461b2c83c09c6d7a9a914275da1d71e9cbbf7069`. The four-digit SQLite prefix index contains 999,997 postings and occupies 29,028,352 bytes. Building it took 0.77 seconds wall time and 38,977,536 bytes maximum RSS (`/usr/bin/time -l`).

`scripts/benchmark.py --repeats 30` ran each method sequentially in one warm process and checked that counts, first positions, and first 100 matches agreed. Timings include Python dispatch for both methods; they exclude HTTP and cold filesystem cache effects.

| Pattern | Length | Matches | Scan p50 / p95 ms | Index p50 / p95 ms |
| --- | ---: | ---: | ---: | ---: |
| `1415` | 4 | 94 | 2.191 / 4.629 | 0.094 / 0.162 |
| `1609` | 4 | 108 | 2.215 / 2.351 | 0.097 / 0.127 |
| `14159265` | 8 | 1 | 2.069 / 2.118 | 0.081 / 0.094 |
| `141592653589` | 12 | 1 | 2.053 / 2.104 | 0.077 / 0.086 |
| `14159265358979323846` | 20 | 1 | 2.057 / 2.325 | 0.080 / 0.105 |
| `000000000000` | 12 | 0 | 2.189 / 2.313 | 0.083 / 0.106 |

An additional 30-request local HTTP burst at concurrency 5 returned all correct `PI` results: 0.050 seconds wall time, 598.3 requests/s over that short burst, p50 3.89 ms, p95 23.29 ms. This is a brief local test, not sustained capacity.

**Decision:** use the validated index when installed for patterns of at least four digits, and use KMP scanning for shorter patterns or when the index is absent or invalid. The index is optional because its disk cost grows with corpus size. No 100M/1B, cold-cache, sustained load, or device frame-rate result is claimed here; those require separate runs on provisioned hosts.
