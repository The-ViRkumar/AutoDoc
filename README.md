<p align="center">
  <img src="icons/icons/png/128x128.png" alt="AutoDoc logo" width="96" />
</p>

# AutoDoc

**Turn any workflow into a click-by-click guide** — record your screen, polish the recording, and export a
captioned, shareable guide for Windows, macOS and Linux.

> **Status: early development.** AutoDoc is being built in phases on top of a screen-recorder base
> ([OpenScreen](https://github.com/getopenscreen/openscreen), MIT). The recorder and editor below work today;
> the guide features are being ported in from the original Python AutoDoc and are **not finished yet**.
> See [`autodoc-project/PHASES.md`](autodoc-project/PHASES.md) for exactly what is done and what is next.
> The original Python version is still available on the [`main`](https://github.com/The-ViRkumar/AutoDoc/tree/main) branch.

## What works today (recorder and editor)

- Record a window or the whole screen, with microphone and system audio.
- Webcam overlay, automatic or manual zooms, a clean editable cursor, click effects.
- A timeline editor with captions generated on-device (no upload) and an editable transcript.
- Export to video, and a command-line interface for headless recording and export.

## What is coming (guide features)

These come from the original AutoDoc and are tracked one by one in
[`autodoc-project/FEATURE_INVENTORY.md`](autodoc-project/FEATURE_INVENTORY.md):

- One step per click, with a screenshot, the active window title and the keys typed.
- Step review: delete, reorder and edit captions before export.
- Automatic captions (window title first, OCR as a fallback) and Hindi / Gujarati translation.
- Optional auto-redaction of emails, IP addresses and passwords.
- Export to Markdown, a printable page and an interactive video wizard, plus a one-click zip for delivery.
- A Library, a Docs hub and a Settings page.

## Build from source

Requires Node.js (22.22.1 is pinned; 24 works), npm, and — for the native capture and compositor pieces — Rust,
the C++ build tools for your platform, CMake, Ninja, LLVM and FFmpeg. Full instructions:
[`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`technical-documentation/engineering/build-and-packaging.md`](technical-documentation/engineering/build-and-packaging.md).

```bash
npm ci
npm run dev        # Vite + Electron
npx tsc --noEmit   # typecheck
npm run test       # unit tests
```

There are no prebuilt downloads of the new app yet.

## Credits

AutoDoc is made by [The.ViRkumar](https://github.com/The-ViRkumar) and is built on
[OpenScreen](https://github.com/getopenscreen/openscreen) by Siddharth Vaddem and the OpenScreen contributors,
used under the MIT License. Third-party components are listed in [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md).

## License

[MIT](LICENSE). The license keeps the original OpenScreen copyright notices alongside AutoDoc's own.
