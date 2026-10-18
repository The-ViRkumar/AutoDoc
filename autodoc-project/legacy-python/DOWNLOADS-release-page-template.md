## Download AutoDoc

Prebuilt binaries for Windows, macOS, and Linux are attached below — built automatically
from this tag by GitHub Actions. No installer needed; each is a single standalone
executable.

| Platform | File | Notes |
|---|---|---|
| Windows | `AutoDoc-Windows.exe` | Double-click to run. |
| macOS | `AutoDoc-macOS.zip` | Unzip, then see **First run** below. |
| Linux | `AutoDoc-Linux.tar.gz` | Extract, then see **First run** below. |

### First run

These builds aren't code-signed (that costs money per platform), so your OS will flag
them as coming from an unidentified source the first time. This is expected — here's how
to get past it:

- **Windows** — SmartScreen will say "Windows protected your PC." Click **More info** →
  **Run anyway**.
- **macOS** — Gatekeeper will refuse to open it normally. Either:
  - Right-click (or Control-click) the `AutoDoc` binary → **Open** → confirm **Open** in
    the dialog, or
  - In Terminal: `chmod +x AutoDoc && xattr -d com.apple.quarantine AutoDoc && ./AutoDoc`
- **Linux** — Extract, then: `chmod +x AutoDoc && ./AutoDoc`. Needs a desktop with X11 or
  XWayland; global keyboard/click capture can be unreliable under native Wayland.

### Optional: OCR step captions

Steps are captioned from the active window's title by default, with an OCR-guessed
fallback if [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) is installed
and on your `PATH`. Not required — the app works fully without it, just without the OCR
fallback caption.

### What's in a recording

Each project folder gets: the screen recording (`recording.mp4`), a screenshot per click,
`guide.md`, a printable `Export_to_PDF.html`, and an interactive `Interactive_Wizard.html`
that syncs the video to each step. A "Package for delivery" option zips it all into one
file to hand off to a client.

### Full changelog

See the commit history since the previous tag: `<previous-tag>...<this-tag>`
