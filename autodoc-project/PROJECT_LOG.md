# AutoDoc — Project Log

Chronological record + decision ledger. Newest entries at the bottom of each section.
Companion files: [`PHASES.md`](PHASES.md) (plan/status) · [`FEATURE_INVENTORY.md`](FEATURE_INVENTORY.md)
(what must not be lost).

---

## Decisions

| ID | Date | Decision | Why |
|---|---|---|---|
| D1 | 2026-10-18 | **Fork OpenScreen** ([getopenscreen/openscreen](https://github.com/getopenscreen/openscreen), **MIT**, TypeScript/Electron/React + Rust compositor, v2.1.1) as the base of the new all-in-one AutoDoc. | Free recorder/editor/audio/webcam/cursor effects/captions out of the box; MIT lets us rebrand and keep our code private/commercial; native desktop (not a browser extension) so global click capture is possible. |
| D2 | 2026-10-18 | **Rejected Screenity** as the base. | Chrome extension (JS) — can't capture clicks outside the browser; **GPL-3.0** would force the whole product to be GPL. Used only as a feature idea. |
| D3 | 2026-10-18 | **Keep the Python AutoDoc v0.1.0 intact** as `legacy-python/` and port its features by phases. | User requirement: "keep all old things so we can add all in the new one properly". |
| D4 | 2026-10-18 | New project lives in **`D:\Rajkumar Projects\AutoDoc\`**; the original **`Guide Creator\`** folder is left untouched as a second backup. | Keeps the fork's git history clean and the old app recoverable even if the new repo is damaged. |
| D5 | 2026-10-18 | Cloned with **full history**; remote **renamed `origin` → `upstream`**. Our own GitHub repo becomes `origin` at push time. | Lets us pull upstream fixes; prevents accidental pushes to their repo. |
| D6 | 2026-10-18 | Our records live in **`autodoc-project/`** (not `docs/` or `technical-documentation/`). | Upstream's `docs:check` lints `technical-documentation/` and `.harness/`; `docs/` holds their media. Keeping ours separate avoids tripping their checks. |
| D7 | 2026-10-18 | Work is delivered **phase by phase**; no phase starts until the user says go. | User instruction. |
| D8 | 2026-10-18 | The new product goes on a **separate branch `studio`** of the user's existing repo `The-ViRkumar/AutoDoc` (remote `origin`); `main` keeps the old Python app, its history, tags and releases untouched. Local folder is added to GitHub Desktop directly (no copying between folders). | The existing repo already has the Python version (6 commits, 3 branches, 4 tags, releases up to v0.1.2). The fork's history is unrelated to it, so a force-push to `main` would destroy it. A branch with an unrelated root is safe. Later the default branch can be switched (rename old `main` to `legacy-python` first). |
| D9 | 2026-10-18 | **Publish a clean, single-commit history under the user's name** instead of OpenScreen's full history. Local branch layout: `studio` (clean, 1 commit, **the only branch to publish**), `openscreen-main` (OpenScreen's code + full history, tracks `upstream/main`, **never publish**), `openscreen-base` (identical to the clone-time snapshot, **never publish**). | User doesn't want other authors' names/commits in their repo. MIT only requires the copyright + license notice to stay in the files (it does: `LICENSE`, `THIRD-PARTY-NOTICES.md`), not the git history. Trade-off: no shared ancestry with upstream, so future upstream updates are a manual diff/copy from `openscreen-main` rather than `git merge`. |
| D10 | 2026-10-18 | Added a catch-all `* text=auto eol=lf` to the top of `.gitattributes` (specific upstream rules below it still win). | Upstream only forces LF for some extensions; on Windows (`core.autocrlf=true`) `.json/.jsonc/.js/.cjs/.h/.css/...` came out as CRLF and the pre-commit Biome check (`lineEnding: lf`) rejected ~550 files. Without this rule every Windows commit that touches those files would fail the hook. |
| D11 | 2026-10-18 | The first commit **omits** the usual "Co-Authored-By: Claude" trailer. | User asked for a history showing only their own name. Add the trailer to future commits only if they want it. |
| D12 | 2026-10-18 | Changed `.husky/pre-commit` from `npx lint-staged` to `node node_modules/lint-staged/bin/lint-staged.js`. | Committing from **GitHub Desktop** failed with `WSL (10 - Relay) ERROR: execvpe(/bin/bash) failed`. Node's `npx` on Windows is an extensionless script with `#!/usr/bin/env bash`; Desktop's hook environment has no Git bash on PATH, so `bash` resolved to the WSL launcher `System32\bash.exe` (no distro installed). Reproduced with `PATH=System32:nodejs sh -e .husky/pre-commit`; the node-direct form passes the same test and works on every OS. |

## Open decisions (need the user)

| ID | Question | Options |
|---|---|---|
| Q1 | **How do we build/test the native app?** | (a) Install Rust + MSVC/CMake/Ninja/LLVM + FFmpeg SDK locally (~GBs, system-level, long first build). (b) Push the fork and let GitHub Actions build artifacts (matches your earlier "build on GitHub" preference); locally do TypeScript typecheck + unit tests + UI-only dev server. (c) Both, later. |
| Q2 | Node version | Upstream pins **22.22.1 / npm 10.9.4**; this machine has **24.15.0 / 11.14.1** (works with warnings so far). Install a Node 22 manager (nvm-windows/fnm) or keep 24? |
| Q3 | Final product name / repo name | Working name: **AutoDoc**. Confirm GitHub repo name when you create it. |

## Environment findings (this machine, 2026-10-18)

- Windows 11 Pro, `git 2.55`, `node 24.15.0`, `npm 11.14.1`. **Not installed:** `pnpm`/`yarn` (not needed — upstream mandates npm), **`rustc`/`cargo`/`rustup`, `cmake`, `ninja`, `clang`**. Visual Studio (v18) folder exists under Program Files. `gh` CLI not installed.
- D: has ~56 GB free. Fork `.git` alone is ~277 MB; a full native toolchain + FFmpeg SDK + `node_modules` + build outputs will add several GB.
- **What the native pieces are** (from `technical-documentation/engineering/build-and-packaging.md`): Windows needs `wgc-capture.exe` + `cursor-sampler.exe` (C++, CMake/Ninja/MSVC), FFmpeg shared DLLs (downloaded by `npm run fetch:ffmpeg`), the Rust **D3D11 compositor addon** `compositor_view.node` (Rust MSVC + LLVM/libclang + pinned FFmpeg SDK), optional whisper STT (CMake) and ONNX runtime. **Without the compositor addon the editor preview is blank.** `npm run dev` itself is just Vite + the Electron plugin and expects those artifacts to exist.
- Upstream CI already builds all of this for Windows (x64/arm64), macOS and Linux.

## Upstream map (starting points for later phases)

- Process model: `electron/` (main), `src/` (React), IPC through `electron/native-bridge/`.
- Recording: `electron/recording/`, `electron/native/` (Swift macOS, C++ Windows), docs `technical-documentation/architecture/recording.md`.
- **Cursor + click telemetry:** `src/lib/cursorTelemetryBuffer.ts` (samples `{timeMs, cx, cy}` normalised 0..1), `electron/native-bridge/cursor/`, doc `architecture/cursor.md` — likely source for step timestamps (Phase 3).
- Project document (single source of truth): `AxcutDocument`, `architecture/document-model.md` — where `steps[]` should live (Phase 3).
- Editor shell / adding a tab or region kind: `architecture/editor-shell.md` (Phase 4/7).
- Export + FFmpeg: `architecture/export-pipeline.md`; transcription/captions/translation: `architecture/transcription-and-captions.md`.
- Upstream-specific behaviors to neutralize in Phase 2: `electron/auto-updater.ts`, `update-checker.ts`, `usage-ping.ts`, `star-prompt.ts`, `glama.json`, `website/`, README badges/links.
- Settled-decision ledger to read before changing architecture: `architecture/decisions.md`.

## Log

### 2026-10-18 — Phase 0 started
- User chose **option 1** (fork OpenScreen + port AutoDoc features), in phases, with a written record.
- Inspected OpenScreen via GitHub API: MIT, TypeScript, 4.5k★, v2.1.1, actively maintained, 280 MB repo.
- Cloned to `D:\Rajkumar Projects\AutoDoc` (full history); `origin` → `upstream`.
- Copied the whole legacy Python project to `autodoc-project/legacy-python/` and diffed it against the original (package, scripts, assets, README, `.github` all identical; 52 files).
- Re-created `DOWNLOADS-release-page-template.md` there (the original lived only in a temp scratch folder).
- Wrote `FEATURE_INVENTORY.md`, `PHASES.md`, this log.
- Started `npm ci` (warns `EBADENGINE`: Node 24 vs pinned 22.22.1).
- `npm ci` finished (exit 0). `npx tsc --noEmit` → pass (exit 0, ~12 s). `npx vitest --run src/lib/cursorTelemetryBuffer.test.ts` → 16/16 pass. So the **TypeScript dev loop works locally on Node 24** (typecheck + unit tests); only the native app build is blocked (see Q1).
- Side effect noticed: after `npm ci` the fork's root `.gitignore` showed one deleted blank line (not authored by us — most likely an npm lifecycle script). Restored with `git checkout -- .gitignore`; it stayed clean after a Vitest run. If it reappears after a future `npm ci`/install, treat it as noise and restore it.
- **Nothing committed.** The fork's working tree has one uncommitted addition (`autodoc-project/`). Commit when you're happy with the records.
- **Phase 0 is complete, pending the user's answers to Q1–Q3.** No phase 1 work has started.

### 2026-10-18 — Connecting the fork to the user's GitHub repo
- User already has `https://github.com/The-ViRkumar/AutoDoc` (old Python version, releases, CI). GitHub Desktop showed the local folder as "openscreen" only because its sole remote was `upstream`.
- Ran locally (nothing pushed): `git remote add origin https://github.com/The-ViRkumar/AutoDoc.git` and `git checkout -b studio`. Remotes now: `origin` (user's repo) + `upstream` (OpenScreen). Branch: `studio`.
- **Risk found:** upstream ships ~20 workflows tied to their own infrastructure (Discord, winget, AUR, Homebrew, MS Store, release announcements, nix). Most trigger on `main`/`release/**`/tags/releases, but `build-whisper-stt.yml` triggers on **any** branch push that touches whisper files — a first push of the full history would likely start a 4-platform whisper build. **Mitigation:** temporarily disable GitHub Actions on the repo before the first push (Settings → Actions → General), re-enable after Phase 2/9 adapt or remove the upstream workflows. The legacy `release.yml` only runs on pushes to `main`, so it is unaffected either way.
- Never push all tags: the fork carries ~97 upstream tags (`v*` tags start upstream's full release build).

### 2026-10-18 — Clean history created (D9–D11)
- User chose "clean start under my name". Created an orphan branch, staged the whole tree (2,070 files, largest 4.5 MB) and committed once as **Rajkumar Viroliya** (`01edf4df`, "Initial commit: AutoDoc Studio base project and Phase 0 records"). `git log studio` → one author.
- The pre-commit hook (`lint-staged` → `biome check`) **failed first**: 151 format errors, all CRLF line endings on non-`.ts` files created by Windows `core.autocrlf=true`. We did **not** bypass the hook. Fix = D10 (`.gitattributes` catch-all) + normalizing the 553 affected text files to LF (the index already held LF, so no content changed). Then `npx biome check .` → 0 errors, 26 pre-existing warnings, and the commit passed the hook.
- Gotchas learned: `git checkout-index -f` did **not** rewrite those files; plain `sed -i 's/\r$//'` on the listed text files did. Git reads attribute rules from the *staged* `.gitattributes`, so stage it before relying on a new rule. `git branch -d` refuses to delete a branch from an unrelated history (renamed it instead).
- lint-staged printed a hint that `.claude/` is in `.gitignore` while one tracked file exists there (`.claude/launch.json`); harmless.
- **Phase 2 audit list for upstream's agent/maintainer files still in the tree:** `.claude/` (1), `.harness/` (9), `.opencode/` (3), `skills/` (1), `AGENTS.md`, `glama.json`, `.github/workflows/*` (~20, mostly upstream infra), `website/`, README badges/links. Decide per item: keep (useful for dev), adapt, or remove. **Legally required and must stay:** `LICENSE` (OpenScreen copyright line + ours added) and `THIRD-PARTY-NOTICES.md`.
- Publish plan for the user (GitHub Desktop): disable Actions on `The-ViRkumar/AutoDoc` first (done by the user), then **Publish branch `studio`** only. Do not publish `openscreen-main` / `openscreen-base`; do not push tags.

### Reference text recorded from the legacy project

**GitHub repo description (copy-paste):**
```
Turn any workflow into a click-by-click guide: screen recording, auto-captioned steps, translation, and one-click export to Markdown/PDF/HTML — for Windows, macOS & Linux.
```
**Topics:** `documentation-generator screen-recorder tutorial-creator guide-generator python customtkinter desktop-app windows macos linux automation ocr` *(for the new repo swap `python customtkinter` → `electron typescript`)*.
