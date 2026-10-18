# AutoDoc

Record a click-by-click walkthrough of any workflow and turn it into a shareable guide:
a screen recording, a per-step screenshot for every click, auto-captioned steps (active
window title, with an OCR-guessed fallback), optional Hindi/Gujarati translation, and
export to Markdown, a printable PDF-style HTML page, and an interactive HTML wizard that
jumps the video to each step.

## Run from source

```bash
pip install -r requirements.txt
python main.py
```

Three pages, switched from the sidebar:
- **Live Recorder** — configure a project, hit Start, click through the workflow you're
  documenting (F8 pause / F9 stop). After you stop, a review screen lets you delete,
  reorder, or hand-edit the caption of any step before export. Optional per-image
  blur/highlight annotation, sensitive-text auto-redaction, and translation run next,
  then your guide is exported automatically — with an option to zip it up for delivery
  and open the folder.
- **Video Extractor** — sample screenshots out of any existing video at a fixed interval.
- **Settings** — Tesseract status, config/log file locations, and app info.

### Step captions

Each step is captioned from the active window's title at the moment you clicked, falling
back to an OCR guess of the text near the click if the title isn't available. You can
always override either one by typing a custom caption in the post-recording review
screen.

### Optional: OCR step captions

Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (Windows),
`brew install tesseract` (macOS), or `sudo apt install tesseract-ocr` (Linux) and make
sure it's on your `PATH`. The app auto-detects it at startup; without it, steps still
export fine, just without the OCR fallback (window-title captions and manual overrides
work either way).

### Auto-redact sensitive text

Turn on "Auto-redact sensitive text" before recording to have the app scan each step's
caption for emails, IP addresses, and password/key/serial-style values. A match blurs
that part of the screenshot and swaps the caption for a redaction notice — off by
default, opt in when you need it.

### Platform notes

- **Client-Facing Mode** (crop screenshots to the active window) isn't available on
  Linux — `pygetwindow` has no Linux backend there. Full-monitor capture always works.
- Display names (e.g. "Display 2 — LG ULTRAGEAR") are detected per-OS from EDID/registry
  data where available; falls back to a plain "Display N" label if not.
- On **macOS**, the first recording may prompt for Accessibility permission (needed for
  global mouse/keyboard capture).
- Global keystroke/click capture on **Linux under Wayland** can be unreliable — X11
  sessions work as expected.

Logs go to `~/.autodoc/logs/autodoc.log`; settings (including recent projects) persist
in `~/.autodoc/config.json`.

## Downloads

Prebuilt executables for Windows, macOS, and Linux are published automatically on every
push to `main` — see the [Releases](../../releases) page.

## Building locally (optional)

CI builds the release binaries; you normally don't need to do this yourself. To sanity
check the packaged build on your own machine:

```bash
pip install -r requirements.txt pyinstaller
python scripts/build.py
```

Output lands in `dist/`.
