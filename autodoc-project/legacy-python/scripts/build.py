"""Single source of truth for the PyInstaller build, used by CI (one
per OS in the release matrix) and optionally by a developer locally to
sanity-check the build before pushing. Keeps the `--add-data` separator
and icon-per-OS logic out of the workflow YAML.

Usage: python scripts/build.py
"""
import platform
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent


def main():
    system = platform.system()
    data_sep = ";" if system == "Windows" else ":"

    args = [
        str(ROOT / "main.py"),
        "--name=AutoDoc",
        "--onefile",
        "--noconsole",
        f"--add-data={ROOT / 'assets'}{data_sep}assets",
        f"--distpath={ROOT / 'dist'}",
        f"--workpath={ROOT / 'build'}",
        f"--specpath={ROOT}",
        "--noconfirm",
    ]

    icon = None
    if system == "Windows":
        icon = ROOT / "assets" / "logo.ico"
    elif system == "Darwin":
        icns = ROOT / "assets" / "logo.icns"
        if icns.exists():
            icon = icns
    if icon and icon.exists():
        args.append(f"--icon={icon}")

    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    main()
