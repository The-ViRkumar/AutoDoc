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
| D13 | 2026-10-18 | **Rebrand depth = user-visible only.** Renamed: README/roadmap/security/conduct/contributing docs, app name, installer + app IDs, window titles, menu text, About box, all 14 locale files (value strings only), permission prompts, icons/logo, update/star links, env example, notices. **Kept on purpose:** internal identifiers, the `openscreen` CLI command + MCP server name, the `.openscreen` project file extension, `OPENSCREEN_*` env vars, `package.json` `name` (so dev data folder is still `openscreen`), storage keys. | ~6,600 mentions in 794 files; a blind rename would break upstream-hosted model downloads and risk subtle bugs for no user benefit. Revisit the CLI/MCP/extension names in a later phase if wanted. |
| D14 | 2026-10-18 | Credit line everywhere visible: `© 2026 The.ViRkumar — Built on OpenScreen (MIT License)` (About box + installer copyright, kept byte-identical by `about.test.ts`). `LICENSE` keeps both upstream holders and adds `Copyright (c) 2026 The.ViRkumar (AutoDoc modifications)`. `THIRD-PARTY-NOTICES.md` names OpenScreen as the base. | User chose a small credit line; MIT only requires the notice. The copyright-holder name is a placeholder the user can change. |
| D15 | 2026-10-18 | Deleted upstream-infra workflows (announce, AUR, auto-approve, 3× Discord, docs/website deploy, flatpak spike, merged-PR bookkeeping, nix build/check, MS Store, winget, Homebrew, **prerelease, promote**), their helper scripts + tests, `CODEOWNERS`, `FUNDING.yml` (would have shown their sponsor button), `website/` (252 files), `nix/`, `flake.*`, `glama.json`. **Kept:** `ci.yml`, `build.yml`, `build-whisper-stt.yml`, `build-onnxruntime-macos.yml`, `diagnostic-artifact.yml`. | User chose to delete infra tied to upstream. Everything is still recoverable from local branch `openscreen-main`. |
| D16 | 2026-10-18 | **Removed the usage ping entirely** (`electron/usage-ping.ts` + test, tray toggle, startup call) — it posted a daily count to upstream's PostHog project. **Updater disabled** behind one constant `UPDATES_ENABLED = false` in `electron/main.ts` (no update check, no update menu, no background timer). Star prompt now links to `The-ViRkumar/AutoDoc`. | User chose "disable both for now". Flip `UPDATES_ENABLED` in Phase 9 after pointing `electron/update-checker.ts` (still targets upstream, inert) at our repo and updating its tests. |
| D17 | 2026-10-18 | App identity: `appId` `com.thevirkumar.autodoc`, `productName` `AutoDoc`, version reset to **1.0.0**, publish target `The-ViRkumar/AutoDoc`, Microsoft Store (`appx`) block + `build:win:store` script removed (it carried the previous maintainer's Store identity); `scripts/i18n-check.mjs` made tolerant of a missing appx block. | Their Store identity must not ship under our name. 1.0.0 avoids colliding with the old Python tags (v0.1.x). |

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

### 2026-10-18 — Phase 2 (rebrand) executed
- Done as described in D13–D17. Icons were regenerated from the legacy 512 px logo with Electron's own `nativeImage` (no new dependency): `icons/icons/png/*` (16–1024), `win/icon.ico` (copied from the legacy `.ico`, 16–256), `mac/icon.icns` (hand-built container, 128/256/512/1024), tray + empty-state art renamed `public/openscreen.png` → `public/autodoc.png` (3 code references updated).
- Recovered the real CLI reference (the old `docs/cli.md` was only a pointer to the deleted website) from `openscreen-main:website/docs/cli.md`, converted to plain Markdown at `docs/cli.md`.
- **Verification:** `npx tsc --noEmit` 0 · `npx tsc -p tsconfig.test.json --noEmit` 0 · `npx biome check .` 0 errors (26 pre-existing warnings) · `npm run docs:check` OK (37 files) · `npm run i18n:check` PASSED · full unit suite **4,829 passed / 5 failed / 12 skipped**; after fixing, the only remaining failure is `scripts/appimage-updates.test.mjs` — `@noble/hashes` is not hoisted to the top-level `node_modules` on this Windows install; the test file is byte-identical to upstream and the lockfile is untouched, so it is **pre-existing/environmental**, not caused by the rebrand. The other 5 failures were caused by us and fixed (4× brand text in `EditorTopBar.stylePresets.test.tsx`; 1× nix test removed from `scripts/ffmpeg-linked-libraries.test.mjs` because `nix/` was deleted).
- **Not verified:** the app was not launched (no native toolchain yet — Phase 1). About box, tray icon and window titles are verified by code + unit tests only. Do a visual check once a build runs.

### Deferred / known leftovers after Phase 2 (nothing here blocks Phase 3)
1. **Do not push any `v*` tag yet.** `build.yml` still contains upstream release/publishing steps (e.g. it dispatches the deleted `docs.yml`). Phase 9 rewrites it.
2. **Upstream-hosted downloads:** the app fetches speech-to-text models/aligners from upstream's GitHub releases (e.g. `electron/stt/modelManager.ts` → `getopenscreen/openscreen` release `v0.0.0-ctc-aligners-1`, plus the `v0.0.0-stt-models` model). That is a functional dependency on their repo — mirror the files under `The-ViRkumar/AutoDoc` releases in Phase 9.
3. `electron/update-checker.ts` and its test still point at upstream (inert while `UPDATES_ENABLED = false`); `MS_STORE_PRODUCT_ID` in `electron/star-prompt.ts` is upstream's Store listing (unreachable outside a Store install).
4. Linux packaging identity still upstream's: `build/com.getopenscreen.OpenScreen.metainfo.xml`, `build/flatpak/…`, and `ci.yml` validates that metainfo. `build/appx/*` tile PNGs are unused leftovers. Rename/remove in Phase 9.
5. `linux.maintainer` is `The.ViRkumar <noreply@github.com>` — set a real contact before the first public release.
6. Agent/MCP prompt text and descriptions (`electron/mcp/*`, `electron/ai-edition/*`) still say "OpenScreen" in places; the CLI command and MCP server name are still `openscreen`. Decide with the AI-feature scope (Phase 6+).
7. Upstream maintainer/agent tooling still in tree: `.harness/` (used by `docs:check`), `.opencode/`, `.claude/launch.json`, `skills/`, `design/`, `docs/*.md` engineering notes, `technical-documentation/` (still says OpenScreen — it is developer reference).
8. The i18n success message still says "…align with appx.languages…" (cosmetic, from the checker script).
