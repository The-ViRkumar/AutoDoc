# AutoDoc — Legacy Feature Inventory

**Purpose:** a complete record of everything the original Python AutoDoc (v0.1.0) does, so
nothing is lost while its features are re-built on top of the OpenScreen fork.

- The full original source is preserved, unmodified, in [`legacy-python/`](legacy-python/).
  A byte-identical copy also still lives in `D:\Rajkumar Projects\Guide Creator\`.
- "Legacy file" paths below are relative to `legacy-python/`.
- **Target (new app)** columns are *plans*, not commitments — OpenScreen internals are still
  being studied. Anything marked `verify` must be checked in the phase that touches it.
- **Status values:** `todo` · `in progress` · `done` · `dropped (reason)` · `replaced by upstream`.

---

## 1. Capture & recording

| # | Feature | Legacy behavior (exact) | Legacy file | Target in new app | Phase | Status |
|---|---|---|---|---|---|---|
| 1.1 | **Click-by-click step capture** | Global mouse hook; on every button *press* inside the selected monitor: save full-monitor (or cropped) screenshot as `step_NNN.png` (3-digit, 1-based), store step = file, path, x, y (relative to monitor), keys typed since previous click, seconds since recording start, window title. Clicks outside the selected monitor are ignored. If the screenshot fails, the step counter is rolled back. | `autodoc/core/recorder.py` → `Recorder._on_click`, `Step` | Derive steps from OpenScreen's cursor-click telemetry + a frame grab at the click timestamp (`verify`: does telemetry carry click events with enough precision?). Fallback: own global hook. | 3 | todo |
| 1.2 | **Screen video recording** | mss + OpenCV `mp4v` at 10 fps, pausable → `recording.mp4`. | `core/recorder.py` → `_record_video_thread` | **Replaced by upstream** (native WGC / ScreenCaptureKit / PipeWire capture — far better). Must keep step timestamps aligned to the video timeline. | 3 | replaced by upstream |
| 1.3 | **Pause / resume** | F8 toggles pause; paused = no frames, clicks ignored, keys ignored. | `core/recorder.py` | Upstream already has pause + global shortcuts (`electron/globalShortcut.ts`) — `verify` that step capture honors pause. | 3 | todo |
| 1.4 | **Stop hotkey** | F9 stops. | `core/recorder.py` | Upstream global shortcuts. | 3 | todo |
| 1.5 | **Floating control bar** | Always-on-top, borderless, bottom-right (`screen_w-270`, `screen_h-130`); Pause/Resume + Stop; live label `Recording • MM:SS • N steps` refreshed every 500 ms. | `ui/floating_toolbar.py` | Extend upstream's recording HUD with a **step counter**. | 3 | todo |
| 1.6 | **Cursor halo + click ripple (burned into video)** | 25 px yellow halo @ 30% alpha; red ripple ring growing 30→57 px over 10 frames after a click. | `core/recorder.py` → `_draw_cursor_fx` | **Replaced by upstream** (editable cursor overlay + click effects). | — | replaced by upstream |
| 1.7 | **Keystroke logging between clicks** | Printable chars appended as-is; special keys as `[Enter]`, `[Space]`…; F8/F9 never logged; joined with spaces and attached to the *next* click's step. Toggleable. | `core/recorder.py` → `_on_key_press` | New: upstream does not log keys (`verify`). Needs a global key hook (e.g. `uiohook-napi`) in the main process. **Privacy-sensitive** (passwords) → ties to redaction (4.4). | 3 | todo |
| 1.8 | **Multi-monitor picker with brand names** | Label `Display N — <Brand Model> (WxH)`; brand omitted when unknown. Windows: read EDID from registry `HKLM\SYSTEM\CurrentControlSet\Enum\DISPLAY\<PnP id>\<instance>\Device Parameters\EDID` (PnP id taken from mss `unique_id` `…#LGD06B3#…`); macOS: `system_profiler SPDisplaysDataType -json` `_name`, paired positionally; Linux: `xrandr --query` geometry + `/sys/class/drm/*<connector>*/edid`. EDID monitor-name descriptor = 18-byte block at offsets 54..125 starting `00 00 00 FC 00`, ASCII, terminated by `0x0A`. Windows' own DeviceString is almost always "Generic PnP Monitor" (useless). Laptop built-in panels often have no name descriptor → plain "Display N". | `monitor_names.py` | Electron `screen.getAllDisplays()` (`label`) — `verify` whether it already gives real names; if not, port the EDID approach to the main process. | 3 | todo |
| 1.9 | **Client-facing mode** | Crop each step screenshot to the *active window* rect clamped to the monitor. Disabled on Linux (no window API). | `core/recorder.py`, `platform_utils.get_active_window_info` | Active-window bounds via an Electron-compatible lib (e.g. `active-win`) at click time (`verify`). | 3 | todo |
| 1.10 | **Active window title per click** | Captured at click time; primary caption source (see 4.5). | `platform_utils.get_active_window_info` | Same lib as 1.9. | 3 | todo |
| 1.11 | **Watermark / logo overlay** | User-picked PNG/JPG, resized to 150 px wide, drawn bottom-left with 20 px margin, alpha-blended; burned into **both** video frames and step screenshots; path persisted in config. | `core/recorder.py` → `overlay_watermark`, `ui/recorder_tab.py` | Upstream has wallpaper/overlay features (`verify` for a logo overlay); otherwise add to the export compositor for video and apply to step images in the guide exporter. | 6 | todo |
| 1.12 | **Duplicate project guard** | If the project folder already contains files, ask before recording into it (avoids mixing steps). | `ui/recorder_tab.py` | Upstream `recordingsDirManager` owns locations — adapt guard to it. | 3 | todo |

## 2. Post-recording workflow

| # | Feature | Legacy behavior (exact) | Legacy file | Target in new app | Phase | Status |
|---|---|---|---|---|---|---|
| 2.1 | **Step review screen** | Modal list shown right after Stop, before annotation/export. Per step: 160×90 thumbnail, "Step N", editable caption field (pre-filled with the window title, placeholder "Auto-detect at export"), keys line, ▲ ▼ reorder, **Delete** (also deletes the screenshot file). Continue button. Empty caption ⇒ automatic at export; typed caption ⇒ used verbatim. Edits live-saved to the step object, so re-rendering after move/delete never loses them. | `ui/review_grid.py` | New **Guide** tab/panel in the editor (step list synced to the video timeline). | 4 | todo |
| 2.2 | **Manual annotation pass** | OpenCV window per screenshot: left-drag = red box (3 px), right-drag = Gaussian blur (51×51), `z` undo, `s` save & next, `x` discard step (deletes file), `q` skip. Display scaled to max 1280×720. Per-image state is encapsulated (original had module globals — a latent bug). | `core/annotator.py` | **Replaced/superseded** by upstream annotation + blur tools (`src/lib/blurEffects.ts`, annotations) — `verify` they can target step stills; else add a still-image annotate mode. | 4 | todo |
| 2.3 | **Open folder after export** | Prompt "Open the folder now?"; cross-platform open (Win `os.startfile`, mac `open`, Linux `xdg-open`). | `platform_utils.open_in_file_manager` | Electron `shell.showItemInFolder` / `openPath`. | 5 | todo |
| 2.4 | **Package for delivery** | Prompt after export; zips every *file* directly inside the project folder (non-recursive) into a **sibling** `<project>.zip` (outside the folder so it never contains itself). | `core/packaging.py` | Zip in main process (`archiver`/`yazl`) — same sibling-zip rule. | 5 | todo |
| 2.5 | **Recent projects** | Last 6 projects, de-duplicated by path, newest first; sidebar buttons open the folder. Stored as `[{name, path}]`. Never mutate the shared defaults list (bug avoided by reassigning). | `config.py`, `app.py` → `_render_recent` | **Library** tab (richer: thumbnails, dates, open, re-export). | 7 | todo |

## 3. Extractor

| # | Feature | Legacy behavior | Legacy file | Target | Phase | Status |
|---|---|---|---|---|---|---|
| 3.1 | **Video frame extractor** | Pick video (`mp4 avi mov mkv`) + output folder + interval seconds (default 2). Saves `extracted_NNN.png` every `max(1, int(fps*interval))` frames. Runs on a worker thread; determinate progress bar; result via shared state polled on the UI thread (workers never touch widgets). Validates file/folder/number; 0 or negative interval clamps to every frame. | `core/video_extractor.py`, `ui/extractor_tab.py` | **Extractor** tab using the bundled FFmpeg (`fps=1/N` filter) with progress events over IPC. | 8 | todo |

## 4. Guide generation (the core differentiator)

| # | Feature | Legacy behavior (exact) | Legacy file | Target | Phase | Status |
|---|---|---|---|---|---|---|
| 4.1 | **Markdown export** | `guide.md`: `# {project} Deployment Guide`, then per step `### Step N`, caption, optional `*(Hindi): …*` / `*(Gujarati): …*`, `![Step N](step_NNN.png)`, `---`; credit footer (see 7.1). | `core/exporter.py` → `build_markdown` | TS exporter module, same output shape. | 5 | todo |
| 4.2 | **Printable "PDF" HTML** | `Export_to_PDF.html`: markdown→HTML, centered 800 px column, "🖨️ Click Here to Save as PDF" button (`window.print()`, hidden in print CSS), brand-colored h1. (It is HTML + print button, **not** a real PDF.) | `core/exporter.py` → `build_pdf_html` | Same, optionally add a real PDF via Electron `printToPDF` (improvement). | 5 | todo |
| 4.3 | **Interactive wizard HTML** | `Interactive_Wizard.html`: dark two-pane page — video (`recording.mp4`) left, scrolling step cards right; clicking a card seeks the video to that step's timestamp and plays; active card highlights and reveals its screenshot; credit footer. | `core/exporter.py` → `build_interactive_html` | Same page, video from the new recording (`verify` container format/seek-ability — upstream records WebM/MP4 variants). | 5 | todo |
| 4.4 | **Auto-redact sensitive text (opt-in, default OFF)** | At export, OCR the 300×100 region around the click; if it matches any pattern → blur that region of the screenshot (Gaussian radius 18) and replace the caption with `🔒 **Sensitive content redacted**`. Patterns: **email** `[\w.+-]+@[\w-]+\.[\w.-]+` · **IPv4** `\b(?:\d{1,3}\.){3}\d{1,3}\b` · **credential keyword** `(?i)\b(password\|passwd\|pwd\|secret\|api[_ -]?key\|license[_ -]?key\|serial(?:\s*(?:no\|number))?)\b\s*[:=]?\s*\S+`. Redaction **outranks** a manual caption override (safety > convenience). Known limit: only scans the area around the click, not the whole screen. | `core/redaction.py`, `core/exporter.py` → `_ocr_scan` | Port regexes verbatim; OCR via bundled engine (see 4.5). Consider scanning the whole step image later (improvement). | 6 | todo |
| 4.5 | **Caption engine** | Per-step caption priority at export: **1)** redaction notice → **2)** manual override (review screen) → **3)** `Action in: **<window title>**` → **4)** OCR `Action on: **<first 5 words>**` → **5)** `Clicked here`. Keystrokes appended: `\n*Keyboard Input:* \`keys\``. OCR = Tesseract on the 300×100 crop around the click (x±150, y±50, clamped). | `core/exporter.py` → `_step_caption`, `_ocr_scan` | TS caption module with unit tests mirroring the priority order. OCR: `tesseract.js` (bundled WASM, no user install) — decision pending in Phase 6. | 6 | todo |
| 4.6 | **Client-facing warning** | In client-facing mode, if the caption source text contains `admin`, `settings`, or `config` (case-insens.), prepend `⚠️ **WARNING: Do not modify system settings here.**` + blank line. Checks the window title when it is the source, else the OCR text. | `core/exporter.py` | Port with the caption engine. | 6 | todo |
| 4.7 | **Translation** | Options: *English Only / English + Gujarati / English + Hindi / All Three*. Google Translate (`deep_translator`) en→hi / en→gu per step; `**` stripped before translating; any failure is logged and just omits that language (never aborts export). Needs internet. | `core/exporter.py` → `translate_steps` | Upstream already has an on-device/LLM caption-translation layer (`transcription-and-captions.md`) — `verify` reuse; else a small translate provider. | 6 | todo |
| 4.8 | **Tesseract discovery** | PATH first, then per-OS install dirs; missing ⇒ OCR skipped silently except a warning label with the OS-specific install hint. | `platform_utils.find_tesseract` | Moot if OCR is bundled (`tesseract.js`). | 6 | todo |

## 5. App shell & UX (legacy design — to carry over as *design intent*, rebuilt in React)

| # | Item | Detail |
|---|---|---|
| 5.1 | **Navigation** | Left sidebar, 210 px: brand "AutoDoc" + tagline "Guide recording, automated"; nav = Recorder, Extractor, Settings; RECENT list; footer `vX.Y.Z` + "by The.ViRkumar" (clickable). |
| 5.2 | **Layout rule (hard-won)** | Two *independent* columns of cards that size to their own content. A shared grid row forces the shorter card to stretch and leaves a dead void inside it. No page needs scrolling at normal window sizes. |
| 5.3 | **Window sizing** | Open at 68% × 78% of the screen, clamped 860–1180 × 620–880, min 760×560, always centered. |
| 5.4 | **Palette tokens** | BG `#0F1117` · SIDEBAR `#141726` · SURFACE `#1B1E2B` · SURFACE_ALT `#232739` · BORDER `#2B2F42` · PRIMARY `#6C5CE7` (hover `#5A4BD1`) · ACCENT `#00D9C0` (hover `#00B8A3`) · TEXT `#ECEDF5` · MUTED `#8A8FA3` · WARNING `#F5A623` · DANGER `#EF476F`. Font: Segoe UI. |
| 5.5 | **Tooltips** (exact copy) | Client-facing: "Crops each screenshot to the active application window instead of the full screen." · Cursor halo: "Draws a soft glow around the cursor and a ripple on each click in the recorded video." · Keystrokes: "Captures what you typed between clicks and shows it under that step." · Annotation: "After stopping, opens each screenshot so you can blur or highlight areas before exporting." · Redact: "Scans each step's caption for emails, IPs, keys, and passwords — blurs that part of the screenshot and redacts the caption when found." · Markdown: "A plain-text guide with embedded image links." · PDF: "A styled page with a print-to-PDF button." · Wizard: "Pairs the recording video with clickable steps that seek to each moment." · Translation: "Adds a translated caption under each English step." |
| 5.6 | **Settings page** | Diagnostics (Tesseract path/status, config file path, log file path) + About (version, author link). |
| 5.7 | **Persistence** | `~/.autodoc/config.json` (`watermark_path`, `language`, `monitor_index`, `recent_projects`), rotating log `~/.autodoc/logs/autodoc.log` (1 MB × 2). New app uses upstream's `app-settings` store instead. |

## 6. Build & release (legacy pipeline — ideas to carry over)

| # | Item | Detail |
|---|---|---|
| 6.1 | **Auto-version tag** | On push to `main`: find latest `v*.*.*` tag, bump **patch**, create + push the tag from CI (no semantic-release dependency). Pushing a tag does not re-trigger a `branches: [main]` workflow, so no loop. |
| 6.2 | **3-OS matrix build → one Release** | `build` per OS → artifacts → `release` job attaches all to the new tag via `softprops/action-gh-release@v2`. Asset names `AutoDoc-Windows.exe`, `AutoDoc-macOS.zip`, `AutoDoc-Linux.tar.gz`. |
| 6.3 | **Release page copy** | See [`legacy-python/DOWNLOADS-release-page-template.md`](legacy-python/DOWNLOADS-release-page-template.md) (unsigned-binary first-run steps, OCR note). Repo description + topics are recorded in `PROJECT_LOG.md`. |
| 6.4 | **Note** | The release workflow publishes a Release with an empty body unless `body_path`/`generate_release_notes` is set. |

## 7. Branding & attribution (must survive the fork)

| # | Item | Detail |
|---|---|---|
| 7.1 | **Author credit** | `AUTHOR_NAME = "The.ViRkumar"`, `AUTHOR_URL = "https://github.com/The-ViRkumar"`. Shown: sidebar footer (clickable), Settings → About, and the footer of **every** generated export (`*Generated with AutoDoc — made by [The.ViRkumar](https://github.com/The-ViRkumar)*` in markdown/PDF-HTML; small clickable line in the wizard). |
| 7.2 | **MIT obligations** | OpenScreen is MIT. Keep its `LICENSE` + copyright notice and `THIRD-PARTY-NOTICES.md`; add AutoDoc's own notice alongside — never replace it. |
| 7.3 | **Repo blurb** | "Turn any workflow into a click-by-click guide: screen recording, auto-captioned steps, translation, and one-click export to Markdown/PDF/HTML — for Windows, macOS & Linux." |

---

## 8. Engineering lessons from the Python build (apply them again)

1. **Never touch UI from a hook/worker thread.** Global key/mouse hooks fire on their own thread; F8/F9 handlers that popped dialogs from there were a real freeze/crash risk. Push an action onto a thread-safe queue and let the UI thread poll it. (Electron equivalent: hooks live in the main process → forward over IPC; never block it.) Also reset the queue per session so a stale "stop" can't end the next recording.
2. **Screen-grab handles are per-thread** (mss). Use `MSS()` not the deprecated `mss()`.
3. **Windows monitor names:** don't trust the API's DeviceString ("Generic PnP Monitor") — read EDID.
4. **Don't force equal card heights** across columns (see 5.2).
5. **`.gitignore` by content, not folder name** — users name project folders anything; ignore `recording.mp4`, `guide.md`, `Export_to_PDF.html`, `Interactive_Wizard.html`, `step_*.png`, `extracted_*.png`, `*.zip`.
6. **Pin risky dependency majors** (we capped `customtkinter<7`); unbounded ranges silently break CI months later.
7. **Delete dead code** (we removed `redact_text()` and an unused `last_project_parent` default found in the final review).
8. **Self-check every non-trivial module** (`python -m …` asserts). In the new repo this becomes Vitest unit tests mirroring each legacy behavior above.
9. **Unsigned binaries need a first-run explanation** on the download page.
10. **Shared mutable defaults:** when a config default is a list/dict, always reassign a new copy — never mutate it in place.

## 9. Things the legacy app did NOT do (don't assume parity)

- The "PDF" export is HTML + a print button, not a PDF file.
- Redaction only scans around the click, only with OCR available, only at export.
- Translation needs internet and only supports Hindi/Gujarati.
- No audio, no webcam, no video editing, no trimming — upstream OpenScreen supplies all of that.
- Linux: no window title / client-facing mode.
