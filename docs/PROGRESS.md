# Progress

2026-11-09: Initialized the repository from the supplied specification.
2026-11-09: Inspected live Place in Pi on mobile and desktop through browser fallback; recorded REA tool absence. Created distinct design system.
2026-11-09: Imported 1,000,000 verified digits from pi2e.ch, recorded source and parsed SHA-256, and checked published positions 10,000, 12,000, and 50,000.
2026-11-09: Built persistent mmap C++ KMP worker, sharded data importer, FastAPI encoding/search/digit API, and optional validated SQLite prefix index.
2026-11-09: Built Next.js home, search, explore, encodings, about, and methodology pages. Browser-tested PI search → result #396 → highlighted digits, plus all layout/display modes and dark theme at desktop width.
2026-11-09: Added an independently computed 1,000-digit fixture, corpus prefix cross-check, and CI workflow. `PYTHONPATH=backend:. .venv/bin/pytest -q backend/tests` passed 13 tests; `npm run build` passed. Benchmark results are in `docs/BENCHMARKS.md`.
2026-11-09: Verified 390×844 mobile layout in the in-app browser. Home search transferred the query without putting it in the URL; results and occurrence rows rendered; Unicode unsupported-input guidance switched to UTF-8; a long pattern showed a scoped no-match. The mobile Line/Braille/Dark visualizer rendered and highlighted the match.
