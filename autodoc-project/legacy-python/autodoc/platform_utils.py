"""Cross-platform helpers: asset/resource paths, Tesseract discovery,
active-window support, and the app's config/log directory.

Kept as small stdlib-only functions so every other module can stay
platform-agnostic and just call into here instead of sprinkling
sys.platform checks around the codebase.
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR_NAME = ".autodoc"

_TESSERACT_CANDIDATES = {
    "Windows": [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ],
    "Darwin": [
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
    ],
    "Linux": [
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ],
}

TESSERACT_INSTALL_HINTS = {
    "Windows": "https://github.com/UB-Mannheim/tesseract/wiki",
    "Darwin": "brew install tesseract",
    "Linux": "sudo apt install tesseract-ocr  (or your distro's equivalent)",
}


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resource_path(*parts: str) -> Path:
    """Resolve a bundled asset both when run from source and from a
    PyInstaller-frozen executable (which unpacks assets under sys._MEIPASS)."""
    if is_frozen():
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent.parent
    return base.joinpath(*parts)


def app_icon_path() -> Path | None:
    system = platform.system()
    candidate = resource_path("assets", "logo.ico" if system == "Windows" else "logo.png")
    return candidate if candidate.exists() else None


def app_data_dir() -> Path:
    path = Path.home() / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return app_data_dir() / "config.json"


def log_path() -> Path:
    log_dir = app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "autodoc.log"


def find_tesseract() -> str | None:
    """Look for a usable tesseract binary: PATH first, then common
    per-OS install locations. Returns None if not found anywhere."""
    on_path = shutil.which("tesseract")
    if on_path:
        return on_path
    for candidate in _TESSERACT_CANDIDATES.get(platform.system(), []):
        if Path(candidate).exists():
            return candidate
    return None


def tesseract_install_hint() -> str:
    return TESSERACT_INSTALL_HINTS.get(platform.system(), "Install Tesseract OCR and ensure it's on PATH.")


def active_window_supported() -> bool:
    """pygetwindow has no Linux backend (raises NotImplementedError)."""
    return platform.system() != "Linux"


def open_in_file_manager(path: str) -> None:
    """Opens `path` in the OS file manager. Best-effort; failures are
    the caller's problem to surface, not something to raise here."""
    system = platform.system()
    if system == "Windows":
        os.startfile(path)  # noqa: S606 -- Windows-only, path is our own project dir
    elif system == "Darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)


def get_active_window_info() -> dict | None:
    """Returns {left, top, width, height, title} for the current
    foreground window, or None if unsupported/unavailable. Never raises."""
    if not active_window_supported():
        return None
    try:
        import pygetwindow as gw

        win = gw.getActiveWindow()
        if not win:
            return None
        return {"left": win.left, "top": win.top, "width": win.width, "height": win.height, "title": win.title}
    except Exception:
        return None


if __name__ == "__main__":
    # Minimal self-check, run with: python -m autodoc.platform_utils
    p = resource_path("assets", "logo.png")
    assert p.parent.name == "assets", f"unexpected resource_path resolution: {p}"

    tess = find_tesseract()
    assert tess is None or Path(tess).exists(), f"find_tesseract returned a non-existent path: {tess}"

    assert isinstance(active_window_supported(), bool)
    print("platform_utils self-check OK:", {"tesseract": tess, "resource_path": str(p)})
