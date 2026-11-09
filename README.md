# Pi Dictionary

An original, local-first instrument for encoding text, searching a verified finite prefix of π, and exploring exact decimal positions. The default import is one million digits. The frontend does not claim that a pattern absent from that range is absent from π.

## Run locally

Requires Python 3.12+, CMake, a C++20 compiler, and Node.js 24+. On this Mac, use `/opt/homebrew/bin/python3`; `/usr/bin/python3` is 3.9 and is too old.

```sh
python3.14 -m venv .venv                     # or /opt/homebrew/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
cmake -S engine -B engine/build -DCMAKE_BUILD_TYPE=Release
cmake --build engine/build -j2
.venv/bin/python scripts/prepare_corpus.py    # downloads and checks the published 1M file
.venv/bin/python scripts/prefix_index.py      # optional, makes >=4-digit searches faster
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. The API is at `http://localhost:8000/api/health`. The browser API origin is configured by `NEXT_PUBLIC_API_URL` at frontend build time; see `.env.example`. To use Docker after importing data and building the index, run `docker compose up --build`.

## Verification and benchmarks

```sh
PYTHONPATH=backend .venv/bin/pytest -q backend/tests
cd frontend && npm run build && cd ..
.venv/bin/python scripts/benchmark.py --repeats 30
```

The default corpus manifest currently installed in this development environment names **1,000,000** digits and parsed SHA-256 `7806ee47461b49ef1f578e14461b2c83c09c6d7a9a914275da1d71e9cbbf7069`. Data and index files are intentionally ignored by Git; every fresh checkout must import and verify them. The importer compares the first 1,000 digits with the independently computed checked-in fixture, checks published checkpoints, and records the source hash. This is provenance and consistency checking, not an independent proof of every digit. See `docs/DATA_PROVENANCE.md`.

## Optional larger prefixes

Obtain an authorized plain-text π source, such as the 1B archive linked from the [pi2e.ch download page](https://pi2e.ch/blog/2017/03/10/pi-digits-download/), extract it outside Git, and run one of:

```sh
.venv/bin/python scripts/prepare_corpus.py --input /absolute/path/pi-decimal.txt --digits 100000000 --take-prefix
.venv/bin/python scripts/prepare_corpus.py --input /absolute/path/pi-decimal.txt --digits 1000000000 --take-prefix
```

The importer hashes and checks the full source, writes ten-million-digit shards, and atomically selects the new manifest. Build an index only if the host has enough free disk; each decimal start creates a posting. Restart the API after changing the corpus. Search falls back to a bounded KMP scan when an index is unavailable. The frontend always displays the running API's actual verified coverage.

## Deployment

Deploy the static Next.js frontend to Vercel or another Node host with `NEXT_PUBLIC_API_URL` set to the HTTPS address of a persistent API host. Run the backend container on a host with read-only corpus and optional index mounts; do not place a billion-digit file inside a serverless frontend function. Set `PI_CORS_ORIGINS` to the frontend origin, provide enough disk and RAM for the chosen corpus/index, and check `/api/health` plus `/api/corpus` before routing traffic. No live deployment is claimed.

Implementation notes: `docs/IMPLEMENTATION_PLAN.md`, `docs/REFERENCE_AUDIT.md`, `docs/ENCODING_SPEC.md`, `docs/SEARCH_SPEC.md`, `docs/BENCHMARKS.md`.
