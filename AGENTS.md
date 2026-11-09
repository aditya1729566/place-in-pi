# AGENTS.md — Pi Dictionary

> **Mission:** Build and ship Pi Dictionary: an original, production-quality, multilingual mathematical search engine that deterministically encodes user text as decimal digits, searches verified finite prefixes of π, reports exact occurrence positions, and lets users explore those positions in an interactive digit visualizer.
>
> This file is the canonical build specification for autonomous coding agents. Work through the entire project end to end; do not stop at a mockup or a partially wired frontend. Never claim a feature or performance result that has not been implemented and verified.

## 0. Operating rules for all agents

1. **Inspect the repository and installed skills before writing code.** Identify package managers, existing components, tests, build commands, local environment, and any `AGENTS.md` instructions. Respect higher-priority instructions. Do not overwrite user work.
2. **Find and use the available reverse-engineering skill** to inspect `https://placeinpi.com/` (see Section 2). Search the agent's available skill registry, skill folders, and tool descriptions for an actual website/UI reverse-engineering skill. Read and follow its instructions before using it. If unavailable or the site blocks inspection, document that fact, use permitted browser/manual inspection techniques, and proceed; do not pretend to have run the skill.
3. **Implement a legally and creatively distinct product.** Study workflows, information architecture, responsiveness, animation patterns, and visualization behaviors of the reference. Do not scrape or transplant source code, proprietary graphics, brand assets, text, logos, product images, or distinctive copyrighted styling. Create original UI and assets. Do not reproduce the reference's merchandise storefront or checkout; commerce is outside scope.
4. **Work in phases without arbitrary stopping points.** Complete the full system, integrations, datasets/manifests, tests, documentation, benchmarking, and deployment-ready configuration. If a resource is unavailable, provide a functioning local fallback and document the blocker rather than abandoning the project.
5. **Prefer correctness over attractive but fictitious results.** All displayed matches must come from real verified π digits. No hardcoded demo positions passed off as real results. No fabricated search coverage, language support, statistics, benchmarks, dataset checksums, or deployment success.
6. **Use an execution plan and keep it updated** (`docs/IMPLEMENTATION_PLAN.md` with phase status, assumptions, blockers, verification results). Run tests and build checks after meaningful changes. Maintain concise logs in `docs/PROGRESS.md`.
7. **Avoid uncontrolled parallel changes.** If multiple agents work concurrently, divide ownership by directory: frontend, encoding/API, search/indexing/data, and QA/docs. Define interfaces first. Shared contracts must be agreed before implementation; one integrator owns final wiring and merges.
8. Use simple, maintainable abstractions. Do not add unnecessary infrastructure, paid services, agents, analytics tracking, or dependencies without a concrete need.

## 1. Product definition and non-negotiable behavior

### Core user journey

1. User enters a name, word, or phrase in a Unicode-aware search field.
2. User selects an encoding profile (default for supported Latin text: English A1Z26 with fixed two-digit tokens; universal fallback: UTF-8 decimal bytes).
3. UI previews **original input → normalized text → per-unit mapping → exact decimal pattern**, including its digit length and encoding/profile version.
4. User searches the selected verified prefix of π; engine performs an **exact substring match**, with no approximation, transliteration, or fuzzy matching hidden in the search.
5. API returns first occurrence (if any), total matches if fully counted, a capped list of positions, coverage, index/data versions, method, and complete/partial status.
6. UI communicates either a verified match or **“No occurrence found in the first N indexed decimal digits”** (never “does not exist in π”).
7. User can jump directly to a result in the digit visualizer, see context before/after the pattern, highlight matches, switch display/layout, copy a permalink, and compare other encoding profiles.

### Core pages

- `/`: Hero, focused search, language/encoding selector, instant encoding preview, coverage badge, relevant exploration entrypoints.
- `/search`: Full results interface, query history (local-only optional), all matching positions with pagination/cursor, encoding comparisons, honest probabilities.
- `/explore`: High-performance digit visualization with **Grid, Spiral, Line** layout modes and **Numbers, Color Blocks, Braille** display modes. Zoom, pan, jump-to-position, keyboard/touch controls, matching-digit emphasis, dark/light modes.
- `/encodings`: Readable specs and interactive examples for all profiles, Unicode normalization, ambiguous text, scripts and translations/transliterations.
- `/about`: Project purpose, corpus origin/verification, counting conventions, mathematical caveats, algorithm overview, limitations.
- `/methodology`: Reproducibility, datasets, benchmarks, probability assumptions, correctness methodology and comparisons.
- Custom not-found/error/loading/empty states.

### Out of scope

- Merchandise purchasing, shopping cart, payment gateway, account sign-in, social leaderboards, NFTs, AI-generated “hidden messages,” or claims of mystical significance.
- “Every possible language” as an unsupported marketing promise: **any Unicode input** via UTF-8 is a real universal baseline; language-aware compact encoding support must be individually specified and tested.

## 2. Mandatory reference study and reverse-engineering workflow

**Reference:** `https://placeinpi.com/`

Before designing the frontend:

1. Locate the available website reverse-engineering skill. Use the exact skill invocation and browser workflow specified by that skill, not an invented API or command. Inspect the live reference if access is permitted.
2. Record the observed **desktop and mobile** experience: header/nav, search interaction, visualizer container, controls, zoom, tooltips, overlays, transitions, loading behavior, empty states, typography hierarchy, spacing, contrast, responsiveness, keyboard interactions, and rendered performance.
3. In particular inspect these publicly exposed interaction concepts (verify their present behavior rather than assuming): search field; “Famous in π”; display choices **Numbers / Color Blocks / Braille**; layout choices **Grid / Spiral / Line**; **Dark / Light**; digit position readout; zoom readout; digit loading feedback. Reference also contains a merchandise area—study only to understand visual organization; **do not clone the shop**.
4. Capture permitted screenshots or notes via the reverse-engineering skill and store an analysis at `docs/REFERENCE_AUDIT.md` with: actual observations, URLs, viewport sizes, interactions, accessibility issues, strengths, weaknesses, and how our original design will differ. If screenshots or tool use are not permitted, document text-only findings.
5. Create `docs/DESIGN_SYSTEM.md`: original palette, typography stack, spacing, breakpoints, motion, visual hierarchy, components, color-encoding legend, light/dark surface specification, accessibility constraints.
6. Implement an **original** polished experience inspired by the useful interaction patterns; do not recreate a pixel-identical page. Make multilingual encoding, verifiable search results, and exploration substantially better than the reference.
7. Test actual website interaction in browser after implementation. Do not mark visual fidelity or usability complete based solely on source code review.

## 3. Recommended system architecture

```text
Browser (Next.js + TypeScript + Tailwind + shadcn/ui)
   |
   | JSON API + paginated position retrieval
   v
FastAPI application (Python 3.12+)
   |-- request normalization and profile registry
   |-- encoded pattern validation / statistics
   |-- coverage metadata + caching + rate limits
   |
   v
C++20 search core (standalone CLI + process/FFI adapter)
   |-- memory-mapped / buffered verified digit data
   |-- baseline exact scan
   |-- optional prefix-postings index
   |-- result count and pagination
   v
Read-only verified π corpus chunks + manifest / SQLite metadata
```

- Begin with a C++ command-line search executable called from a bounded worker subprocess or persistent worker with a framed protocol. Prefer a persistent worker for repeated queries. Avoid invoking an unbounded subprocess per keystroke.
- The backend must work without Redis, Supabase, or an external database. SQLite suffices for metadata and optional caching. Data corpus remains a file-based immutable source of truth.
- Keep compute backend separate from the Vercel-hostable frontend. A stateless serverless frontend must **not** assume it can bundle or mmap a billion-digit file in a tiny function.
- Clearly document dev/prod environment variables; provide `.env.example`, `docker-compose.yml` if genuinely useful, and production deployment guidance for a persistent compute host.

### Suggested repository structure

```text
pi-dictionary/
├── AGENTS.md
├── frontend/
│   ├── app/
│   ├── components/{search,visualizer,layout,ui}/
│   ├── lib/{api,encoding,formatting}/
│   ├── styles/
│   └── tests/
├── backend/
│   ├── app/{api,core,encodings,models,statistics,services}/
│   └── tests/
├── engine/
│   ├── include/
│   ├── src/
│   ├── tests/
│   ├── benchmarks/
│   └── CMakeLists.txt
├── data/
│   ├── manifests/
│   └── README.md
├── scripts/{download,verify,prepare,index}/
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PROGRESS.md
│   ├── REFERENCE_AUDIT.md
│   ├── DESIGN_SYSTEM.md
│   ├── ENCODING_SPEC.md
│   ├── SEARCH_SPEC.md
│   ├── DATA_PROVENANCE.md
│   └── BENCHMARKS.md
└── .github/workflows/
```

## 4. Encoding specification — deterministic and reversible where possible

Encoding must be a **versioned pure function**. API and UI must produce identical results for every Unicode input. Establish a shared test-vector corpus and profile IDs; use one authoritative backend implementation rather than drifting frontend/backend reimplementations.

### Profiles

1. **`latin-a1z26-v1` (default when appropriate):** Accept Latin `A`–`Z`, fixed width 2, `A=01` through `Z=26`. Define precisely whether default policy strips ASCII spaces and supported punctuation (recommended: explicit `letters_only` setting, preview exactly what was removed), case-folds ASCII, and how it handles digits, accented Latin, emojis, and unsupported characters. No silent conversion of unsupported characters. Example: `ADA` → `010401`, `PI` → `1609`.
2. **`utf8-decimal-v1`:** Normalize Unicode to NFC, encode to UTF-8 bytes, then encode **each byte as exactly three decimal digits** `000`–`255`. Example: `PI` → `080073`. This is lossless relative to normalized text and handles valid Unicode input from all scripts; warn that encoded patterns can become very long.
3. **`unicode-scalar-v1` (optional advanced):** Encode each Unicode scalar value as a seven-digit, zero-padded decimal value (sufficient for maximum U+10FFFF = 1114111), after NFC. Reject invalid surrogate sequences. Example: `PI` → `00000800000073`.
4. **Explicit script-specific profiles (later):** Greek, Devanagari, Cyrillic, Arabic, etc. must have documented grapheme/character handling, ordered symbol tables, distinct IDs/versions, and test vectors. Do not assume one character equals one code point or that “one alphabet” exists per spoken language. If any script contains more than 99 tokens, increase fixed width appropriately; reserve codes and escape/word separators intentionally.
5. **Transliteration / language variants:** Opt-in, named transformations only. Never equate transliteration with translation; display the exact converted text and its rule set. Language should be descriptive metadata unless a concrete language-specific encoding exists. Never claim the occurrence is uniquely “in” a language.

### Invariants

- Store `raw_text`, `normalized_text`, transformation options, `profile_id`, `profile_version`, `encoded_pattern` and an encoding breakdown.
- Reject or clearly identify empty patterns; implement length limits, invalid Unicode handling, disallowed controls, and safe input rendering. Unicode normalization and case-fold policies must be documented.
- Leading zeros **are significant**: store encoded patterns as strings, never integers.
- Reject non-decimal search patterns at the engine boundary.
- Present profile comparisons side by side without claiming that a name has a universal fixed position independent of encoding.

## 5. π data pipeline, provenance, and integrity

1. Select a legitimate source of decimal digits of π, record source URL, retrieval date, license/terms, file format, declared range, and any externally published checksums in `docs/DATA_PROVENANCE.md`.
2. Create resumable download/import tooling (where permitted); avoid committing giant datasets to Git. Add appropriate `.gitignore` patterns.
3. Verify downloaded file hashes against authoritative published values when available; independently verify known prefix digits. Never invent or hardcode checksums as if sourced.
4. Parse input meticulously: exclude integer `3`, decimal point, whitespace, headers, and newlines. Position 1 always means the first digit after the decimal point (digit `1`). Use global zero-based offsets internally if convenient and expose **one-based decimal positions** in API/UI.
5. Start with a small checked-in test fixture, then ingest progressively larger corpora: 1M → 100M → 1B digits. Large real downloads are optional in CI and should have documented reproducible commands.
6. Write immutable sharded corpus files with explicit global offsets, digit counts, hashes, and version IDs. Support direct ASCII reads first; benchmark packed BCD later rather than assuming compression is faster.
7. Handle matches crossing chunk boundaries by passing search state between chunks or searching overlap up to `pattern_length - 1`; deduplicate by global start offset and ensure no truncated match is accepted.
8. Record total **verified searchable digit coverage** and expose it in `/api/corpus`. Do not represent 1B digits as available if only 1M were actually loaded.
9. Ensure deterministic append/update behavior and invalidate cached negative results when coverage expands.

## 6. Exact search engine

### Baseline

- Build a C++20 executable/library supporting `count`, `first`, `locate` (bounded positions), and `context` operations.
- Use `uint64_t` for all global offsets and counts; use overflow-safe arithmetic when evaluating `N-k+1` and segment bounds.
- Implement a correct baseline (C++ `std::search` or `std::string::find` on buffered segments, or KMP for explicitly linear worst-case matching); measure rather than guessing which is fastest.
- Short-circuit when the pattern is longer than the verified corpus. Provide a configurable query length cap and a clear client-facing reason.
- Count all occurrences including **overlapping** occurrences. Sorting and pagination must be deterministic.
- Support cancellation/timeouts and safe worker concurrency; track memory use and do not load the entire corpus into every request's process.
- Distinguish full search/count from partial or timed-out queries. A capped list of returned positions is **not** a complete total count unless a full count was performed.
- Ensure result positions are globally consistent across shards and properly report verified surrounding digits.

### Indexed search (second phase)

- Design a fixed-prefix inverted index for prefixes of configurable length (start evaluating 4, 5, 6), mapping digit prefixes to global candidate offsets. Verify **full patterns** against the original π corpus before returning results.
- For patterns shorter than the index prefix length, use a correct fallback path or a purpose-built shorter-prefix strategy.
- Make index build deterministic, versioned, resumable, and validated against the exact source corpus. Index must never silently outlive the corpus version it indexes.
- Recognize that storing positions for all prefixes costs roughly one position per source digit in aggregate, plus metadata. Evaluate sorted/posting compression, delta encoding, 32/64-bit shards, IO and CPU trade-offs.
- Benchmark index lookup vs sequential scan on short/common and long/rare patterns, cold/warm cache, varying corpus sizes and concurrency.
- Treat FM-index, suffix arrays, and compressed suffix arrays as **research/optimization candidates**, not mandatory premature complexity. Only add after a documented benchmark-driven decision.

### Search-result contract

```json
{
  "query": {"raw_text": "ADA", "normalized_text": "ADA", "profile_id": "latin-a1z26-v1", "encoded_pattern": "010401", "pattern_length": 6},
  "corpus": {"constant": "pi", "version": "actual-manifest-version", "digits_searched": 1000000, "position_basis": "1-indexed after decimal"},
  "result": {"found": false, "first_position": null, "matches": [], "total_matches": 0, "count_complete": true, "positions_complete": true, "next_cursor": null},
  "execution": {"method": "scan", "complete": true, "elapsed_ms": 0}
}
```

**Contract example only:** values above are illustrative, NOT a claim about an actual search; generate all real values at runtime. Choose a single stable typed schema and OpenAPI contract. Use `null` instead of zero or false for unknown/incomplete counts, and preserve `complete` flags.

### HTTP endpoints

- `GET /api/health`
- `GET /api/corpus` — verified available extent, source/version, capabilities
- `GET /api/encodings` — supported profiles and specifications
- `POST /api/encode` — validated normalized text and exact encoding breakdown
- `POST /api/search` — encoded search with explicit coverage and bounded results
- `GET /api/search/{search_id}/matches?cursor=...` — optional pagination if server stores search jobs/cursors
- `GET /api/digits?start=1&count=200` — bounded verified context for the visualizer
- `GET /api/stats` — accurate corpus/runtime metrics, optional

Ensure rate limits, CORS allowlist, structured error responses, request size caps, reasonable timeouts, trace IDs, and no information leakage from server file paths.

## 7. Mathematical statistics — clear assumptions, honest messaging

For a uniform independent random-digit model and an exact pattern of length `k` in an `N`-digit corpus:

- Candidate starting positions: `max(0, N - k + 1)`.
- Expected occurrences: `λ = max(0, N - k + 1) × 10^(-k)`.
- Rare-event approximate chance of at least one occurrence: `1 - exp(-λ)` (not exact for all overlapping patterns; use `-expm1(-λ)` for numerical stability).
- Expected waiting distance is of order `10^k` in an independent random model; exact waiting-time expectations depend on pattern self-overlap.

**Never claim** π's decimal digits are proved independent, random, or normal in base 10; normality is unproven. Do not equate a probabilistic prediction with a verified match or promise every finite pattern occurs. Show model assumptions near any probability UI. For extreme lengths use log/exponential-safe calculations; avoid `Infinity`, `NaN` and fake precision in frontend display.

Optional research: observed vs expected match frequencies, empirical distribution of first match positions across equal-length patterns, overlap-aware effects, scan/index latency and memory profiles. Describe these as experiments, not proof of π's normality.

## 8. Frontend execution and visual quality

### Design direction

Create **a premium mathematical observatory**, not a generic dashboard. Original visual language: precise typography, calm scientific color treatment, tasteful π/digit motifs, polished micro-interactions, generous whitespace, and strong information hierarchy. Think editorial mathematics meets high-performance visualization. No stock hero art, gratuitous gradients, fake 3D, or generic AI-generated visual clutter.

### Required components

- `SearchBar` with debounced validation, Enter-to-search, loading/error/success states and keyboard usability.
- `EncodingProfilePicker` with named profiles, explanatory tooltips and unsupported-input feedback.
- `EncodingInspector` showing per-character/byte mappings and zero-padded pattern with copy affordance; virtualize long mappings if necessary.
- `SearchSummary` with exact first position, verified corpus boundary, match count or partial status, method and timing only when measured.
- `OccurrenceList` with cursor pagination, jump links, context previews and properly scoped positions.
- `PiVisualizer` with Grid, Spiral and Line layout; Numbers, Color Blocks and Braille display; viewport-based digit fetching; pan/zoom and selected occurrence highlighting. Braille should be a deliberately documented mapping, not invented or misleading literal text encoding.
- `DatasetCoverage` with manifest version and real loaded extent.
- `ProbabilityExplainer` with assumptions and computed statistics.
- Responsive app shell, intuitive mobile controls, dark/light mode, accessible focus states and reduced-motion support.

### Visualization performance

- Use Canvas/WebGL as indicated by benchmarking for high-density animated digits; DOM is fine for small accessible selections. Avoid rendering a million React elements.
- Virtualize or tile large views; fetch **only visible digit windows** and prefetch limited adjacent ranges. Limit maximum resolution and update rate; keep UI responsive during zoom/pan.
- Render selectable results and screen-reader summaries in semantic HTML alongside any Canvas visualization.
- Distinguish selected digit position, match range, and viewport position. Show global positions clearly.
- Test keyboard interaction, mobile touch behavior, contrast, color-blind usability, and reduced-motion preference.

### No fabricated UX

- Do not ship inert toggles, dummy charts, fake loading states, or clickable controls that do nothing.
- If a visualization variant cannot be implemented correctly, omit it or clearly disable it rather than faking support.
- Live searches must be wired end-to-end to the C++ engine and verified corpus, not local `Math.random()` or fake sample data.

## 9. Testing, verification and benchmarks

### Required correctness tests

- `π` decimal starts `141592653589793...`; position 1 = `1`, position 2 = `4`, etc.
- Pattern `1415` begins at position 1, `4159` at position 2, `1592` at position 3, in a suitable initial fixture.
- Overlapping matches on synthetic corpora (e.g. `11111` searched for `111` finds starts 1, 2, 3).
- Patterns crossing data chunks and shard boundaries, patterns longer than corpus, leading-zero patterns, empty input, very short and long inputs.
- Randomized property tests comparing indexed results with a simple trusted brute-force oracle over small synthetic corpora.
- Unicode NFC, composed/decomposed text, multilingual UTF-8, emoji, unsupported glyphs, multi-codepoint graphemes, punctuation, and case policies.
- Metadata integrity failures: checksum mismatch, missing chunk, stale index, truncated files, malformed manifest, short read, lost worker, timeout.
- API schema/contract tests, cursor pagination, frontend encoding preview consistency, complete vs partial count states.
- Frontend E2E tests: search → exact results → select match → visualizer jump; not-found and offline/error paths; mobile navigation; theme and view controls.
- Accessibility checks for keyboard focus, semantic labels, contrast and reduced motion.

### Benchmarks

Produce reproducible, actual measurements (not target numbers presented as results) for:

- 1M, 100M and 1B real digits where locally available.
- Cold vs warm direct scan and prefix-index lookup.
- Lengths 2, 4, 6, 8, 12, 20+; found and not-found patterns; common repetitive patterns.
- Index construction elapsed time, disk bytes, peak RSS, average/p50/p95 search latency with fixed seed and hardware specs.
- API throughput/concurrency, visualizer frame rate on realistic desktop and mobile settings.

Record exact machine/dataset/build flags in `docs/BENCHMARKS.md`; never invent missing runs. Separate aspirational goals from measurements.

## 10. Security, privacy and reliability

- Treat user text as untrusted. Strict JSON validation; no shell interpolation; safe subprocess arguments; no execution of user-supplied commands or path traversal.
- Use read-only dataset mounts and capped memory/CPU/thread resources for search workers.
- Keep user searches private by default: avoid logging raw names, do not introduce tracking pixels, and do not persist queries unless users explicitly opt in.
- Rate-limit expensive count-all searches and bound response sizes; paginate large result sets.
- Never leak API credentials or publish proprietary/unauthorized datasets. Keep corpus provenance and usage terms documented.
- Provide graceful fallback when full corpus is not locally available. The interface must always show the real current coverage.
- Keep a clear operational distinction between healthy server, available corpus, valid index and ready search worker.

## 11. Build order and completion gates

### Phase 1 — Discovery & specification
- [ ] Inspect repo, tools, skills, and the live Place in Pi reference with the reverse-engineering skill if available.
- [ ] Author reference audit, distinct design system, encoding spec, API schema, data manifest format, and phase plan.

### Phase 2 — Correct vertical slice
- [ ] Build small verified π fixture, C++ exact scan engine, Python encoder/API, and functional Next.js search page.
- [ ] Demonstrate real search, exact positions, not-found reporting, and result context with tests.

### Phase 3 — Data expansion & robust search
- [ ] Add import/verification/chunking, 1M → 100M → 1B ingest paths, manifest coverage and cross-boundary correctness.
- [ ] Add worker supervision, memory control, bounded queries, pagination and cancellation.

### Phase 4 — Complete original frontend
- [ ] Implement polished responsive design and the full visualizer with all honestly supported modes.
- [ ] Connect all interactions to live data, encoding comparisons, probabilities, accessible controls, and permalinks.

### Phase 5 — Indexing & profiling
- [ ] Implement, verify, and benchmark prefix index against direct scan.
- [ ] Select default search strategy from measured trade-offs; preserve scan fallback.

### Phase 6 — Production readiness
- [ ] Run all unit, integration, E2E, accessibility, integrity and performance tests.
- [ ] Document local setup, actual dataset availability, deployment architecture, health checks, errors, and reproducibility.
- [ ] Perform final browser QA at desktop and mobile widths; fix unfinished flows, data issues, console errors, and dead controls.

## 12. Definition of done

Consider the task complete only when all of the following are true:

1. User can enter a name, inspect a deterministic encoding, perform an exact search against a **verified and honestly labeled** π corpus, and receive correct 1-based decimal position(s).
2. Non-matches accurately say the pattern was not found **within the indexed range**, not that it can never occur.
3. Frontend is distinct, polished, responsive and actually functional; reference audit documents how the available reverse-engineering skill was used (or why it could not be used).
4. Grid, Spiral and Line exploration plus supported display controls are real, efficient, and tested; all result jumps highlight the exact underlying digits.
5. Encoding tests, cross-boundary matching tests, integration tests, and E2E happy/error paths pass.
6. Prefix index performance is evaluated rigorously; no misleading benchmark results or unnecessary mandatory index complexity.
7. App can be run locally from documented clean-environment commands and can be configured for deployment with frontend and persistent compute separated.
8. Documentation includes architecture, dataset provenance, exact encoding versions, mathematical caveats, measured performance, known limitations, and next steps.

## 13. Final agent response format

After implementation, provide:

- A concise inventory of completed features and significant architecture choices.
- Exact commands to run frontend/backend/engine, import or verify π data, test, and benchmark.
- The real verified indexed range installed in the environment and any unfulfilled dataset/deployment requirements.
- Tests executed and their actual results, including caveats about skipped tests.
- Evidence from reference inspection and where it was recorded.
- Known limitations and highest-impact follow-up improvements.

**Operating principle: build the product, prove its correctness, and make the mathematics explorable. A beautiful interface is not a substitute for an exact answer; an exact answer is not a substitute for a usable product.**
