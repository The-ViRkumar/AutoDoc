"""Tiny persisted-settings store (last project folder, watermark, etc).
Plain JSON, stdlib only -- no need for anything heavier here.
"""
import json
import logging

from .platform_utils import config_path

logger = logging.getLogger("autodoc.config")

MAX_RECENT_PROJECTS = 6

DEFAULTS = {
    "watermark_path": "",
    "language": "English Only",
    "monitor_index": 0,
    "recent_projects": [],  # [{"name": ..., "path": ...}, ...], newest first
}


def load() -> dict:
    path = config_path()
    if not path.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {**DEFAULTS, **data}
    except Exception:
        logger.exception("Failed to read config at %s, using defaults", path)
        return dict(DEFAULTS)


def add_recent_project(cfg: dict, name: str, path: str) -> None:
    """Moves (name, path) to the front of cfg['recent_projects'],
    de-duplicated by path and capped at MAX_RECENT_PROJECTS. Mutates
    cfg in place by reassigning the list (never mutates a list that
    might still be the shared DEFAULTS one)."""
    recents = [r for r in cfg.get("recent_projects", []) if r.get("path") != path]
    recents.insert(0, {"name": name, "path": path})
    cfg["recent_projects"] = recents[:MAX_RECENT_PROJECTS]


def save(data: dict) -> None:
    path = config_path()
    try:
        merged = {**DEFAULTS, **data}
        path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write config at %s", path)
