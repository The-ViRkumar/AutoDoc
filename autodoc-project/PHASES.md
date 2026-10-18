# AutoDoc — Phase Plan

Vision: **one app** that records your screen like OpenScreen *and* turns any workflow into a
shareable, captioned, translated guide — with a Library, Docs and Settings around it.

Rules of the road
- **One phase at a time.** Each phase ends with its exit criteria met, `PROJECT_LOG.md`
  updated, and the status below flipped. Don't start the next phase until the user says go.
- **Nothing from the old app is dropped silently.** Every legacy feature lives in
  [`FEATURE_INVENTORY.md`](FEATURE_INVENTORY.md) with a status; a feature is only ever
  `replaced by upstream` or `dropped (reason)` with the reason written down.
- Follow upstream conventions (`AGENTS.md`): TypeScript strict, Biome, npm only, Vitest next
  to source, keep each addition self-contained. Keep our code in clearly named modules so
  upstream merges stay easy.
- Upstream remote is `upstream`. Our own GitHub repo will be `origin` (added at push time).

## Status board

| Phase | Name | Status |
|---|---|---|
| 0 | Preserve, inventory, fork, feasibility | **done** (published on branch `studio`) |
| 1 | Get a baseline build running | todo |
| 2 | Rebrand to AutoDoc | **done in code** — verified by typecheck, lint, docs/i18n checks and unit tests; visual check waits for the first build (see log, "Deferred leftovers") |
| 3 | Guide capture core (steps from a recording) | todo |
| 4 | Guide editor tab (review / reorder / edit / annotate) | todo |
| 5 | Guide export (MD / HTML / wizard / zip) | todo |
| 6 | Smart captions (title + OCR), redaction, translation, client-facing | todo |
| 7 | Library, Docs and Settings tabs | todo |
| 8 | Extractor tab + remaining legacy features | todo |
| 9 | Release pipeline, polish, docs | todo |

---

## Phase 0 — Preserve, inventory, fork, feasibility *(done)*

**Goal:** make it impossible to lose the old app, and know exactly what we're building on.

Deliverables
- [x] Old Python project copied byte-identical to `autodoc-project/legacy-python/` (52 files; original folder untouched).
- [x] `FEATURE_INVENTORY.md` — every legacy feature, exact behavior, lessons, target mapping.
- [x] `PHASES.md` (this file) and `PROJECT_LOG.md` (decisions + chronological log).
- [x] OpenScreen cloned with full history; remote renamed `upstream`.
- [x] `npm ci` succeeds (exit 0); `npx tsc --noEmit` passes (exit 0, ~12 s); a targeted Vitest file runs (`cursorTelemetryBuffer.test.ts`: 16/16). The full suite was deliberately not run (upstream: ~1670 tests, 1+ min — run once per task, at the end).
- [x] Native-toolchain gap identified and written down (see log).
- [x] GitHub wiring: `origin` = `The-ViRkumar/AutoDoc`, `upstream` = OpenScreen; new work on branch **`studio`** (old Python app stays on `main`).
- [x] Clean single-commit history under the user's name (log D9); line-ending fix so the pre-commit hook passes on Windows (log D10).
- [ ] User publishes branch `studio` from GitHub Desktop (Actions disabled first).

Exit criteria: user has reviewed the three records and approved the toolchain choice for Phase 1.

## Phase 1 — Get a baseline build running

**Goal:** a working, *unmodified* OpenScreen build we can launch, record with, and test against.

Needs a decision (see `PROJECT_LOG.md` → "Open decisions"): install the native toolchain
locally (Rust + MSVC/CMake/Ninja/LLVM + FFmpeg SDK, several GB, system-level) **or** let GitHub
Actions build it (upstream's workflows already do) and test from downloaded artifacts, using
local unit tests + the browser-mode dev server for UI-only work in between.

Deliverables: build recipe written into the log; a launched baseline (or CI artifact) with one
successful test recording; the dev loop documented (typecheck, unit tests, UI-only mode).

## Phase 2 — Rebrand to AutoDoc *(done in code — results in PROJECT_LOG.md, decisions D13–D17)*

**Goal:** it *looks and behaves* like our product, and nothing phones home to upstream.

Scope: product/app name + app id + window titles; logo/icon (reuse `legacy-python/assets/`);
About screen with author credit (inventory 7.1); `LICENSE` keeps MIT + upstream copyright and
adds ours; `THIRD-PARTY-NOTICES.md` kept; README + website folder; `package.json` name/version;
`electron-builder.json5`. **Audit and neutralize upstream-specific behavior:** auto-updater
pointing at upstream releases, usage ping, star prompt, update checker, Glama/MCP listing,
Discord/Sponsor links. Apply the AutoDoc palette (inventory 5.4) where it fits upstream's theming.

Exit: app launches branded; a grep for upstream URLs/identifiers shows only intentional
attribution; updater/telemetry verified pointed at us or disabled.

## Phase 3 — Guide capture core

**Goal:** pressing Record also produces **steps** (click → screenshot/timestamp/window title/keys).

Scope (inventory §1): study upstream cursor telemetry + native bridge first (`cursor.md`,
`recording.md`, `native-bridge.md`); decide telemetry-derived vs own global hook; step data model
stored inside the project document (`document-model.md`); window title + keys capture; HUD step
counter; multi-monitor names; pause/stop parity; guard against recording into an existing project.

Exit: a recording yields a persisted `steps[]` aligned to the video timeline; unit tests mirror
legacy behaviors 1.1–1.10; verified on a real recording.

## Phase 4 — Guide editor tab

**Goal:** the review screen, rebuilt properly inside the editor.

Scope (inventory §2.1–2.2): new **Guide** tab listing steps (thumbnail, caption field, keys,
reorder, delete) synced with the timeline; annotate/blur on step stills (reuse upstream tools if
possible). Delete removes the step *and* its still.

Exit: steps can be reviewed/reordered/edited/deleted; edits persist in the project file.

## Phase 5 — Guide export

**Goal:** the three legacy outputs + packaging.

Scope (inventory §2.3–2.4, §4.1–4.3, §7.1): `guide.md`, printable HTML, interactive wizard,
credit footer on all, "Package for delivery" sibling zip, open-folder prompt. Output shape must
match legacy exactly (snapshot tests against sample steps).

Exit: exporting a recording produces all files that open correctly; wizard seeks the video.

## Phase 6 — Smart captions, redaction, translation

**Goal:** the caption engine and its safety features.

Scope (inventory §4.4–4.8): caption priority engine with tests; OCR (bundled engine decision);
opt-in auto-redact with the three regexes; client-facing warning + active-window crop; Hindi /
Gujarati translation (reuse upstream's translation layer if suitable).

Exit: priority order test-covered; redaction blurs and replaces captions; works with no OCR.

## Phase 7 — Library, Docs, Settings tabs

**Goal:** the "all-in-one" shell. **Library:** every recording/guide with thumbnails, open,
re-export, recent list (inventory 2.5). **Docs:** guide templates / exports hub. **Settings:**
diagnostics + about (inventory 5.6).

## Phase 8 — Extractor + leftovers

**Goal:** frame extractor tab (inventory 3.1, FFmpeg-based) and sweep the inventory for any
`todo` row; watermark overlay (1.11) if not already done.

## Phase 9 — Release pipeline, polish, docs

**Goal:** shippable. Adapt upstream's release workflows (+ our auto patch-tag idea, inventory
6.1), release-page copy (6.3), unsigned-build notes, README/screens, final audit pass like the
Python app's "final check" (threading, ignore files, dead code, dependency pins).
