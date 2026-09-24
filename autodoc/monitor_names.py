"""Best-effort per-monitor brand/model name detection, so the display
picker can show "Display 2 — LG ULTRAGEAR (2560x1440)" instead of just
"Display 2 (2560x1440)".

Every platform path here is wrapped so a failure just yields an empty
map -- callers fall back to the plain "Display N" label they already
had, this is a pure enhancement, never a hard requirement.
"""
import platform
import re
import subprocess


def get_monitor_names() -> dict:
    """Returns {(left, top, width, height): "Brand Model"} for
    whichever monitors could be identified. Geometry keys match what
    `mss.MSS().monitors` reports, so callers can look a monitor's
    rect up directly."""
    system = platform.system()
    try:
        if system == "Windows":
            return _windows_monitor_names()
        if system == "Darwin":
            return _macos_monitor_names()
        if system == "Linux":
            return _linux_monitor_names()
    except Exception:
        pass
    return {}


def _windows_monitor_names() -> dict:
    """Windows' own DeviceString for a monitor is usually just
    "Generic PnP Monitor" -- the real brand/model only lives in the
    monitor's EDID, which Windows caches in the registry per PnP
    device ID. mss's `unique_id` (e.g. "...#LGD06B3#...") gives us
    that PnP ID directly, so we read the same EDID bytes Linux reads
    from sysfs and run them through the same parser."""
    import mss

    names = {}
    with mss.MSS() as sct:
        for m in sct.monitors[1:]:
            unique_id = m.get("unique_id", "")
            parts = unique_id.split("#")
            if len(parts) < 2:
                continue
            pnp_id = parts[1]
            edid = _read_windows_edid(pnp_id)
            if not edid:
                continue
            name = _parse_edid_monitor_name(edid)
            if name:
                key = (m["left"], m["top"], m["width"], m["height"])
                names[key] = name
    return names


def _read_windows_edid(pnp_id: str) -> bytes | None:
    import winreg

    base = rf"SYSTEM\CurrentControlSet\Enum\DISPLAY\{pnp_id}"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as pnp_key:
            index = 0
            while True:
                try:
                    instance_name = winreg.EnumKey(pnp_key, index)
                except OSError:
                    return None
                index += 1
                try:
                    with winreg.OpenKey(pnp_key, instance_name + r"\Device Parameters") as params_key:
                        edid, _ = winreg.QueryValueEx(params_key, "EDID")
                        return edid
                except OSError:
                    continue
    except OSError:
        return None


def _macos_monitor_names() -> dict:
    """No reliable per-display geometry from system_profiler, so this
    pairs names to monitors positionally by mss's own enumeration
    order -- good enough for "which display is which" identification,
    not guaranteed pixel-exact for unusual multi-monitor arrangements."""
    import json

    import mss

    output = subprocess.run(
        ["system_profiler", "SPDisplaysDataType", "-json"],
        capture_output=True, text=True, timeout=5, check=False,
    ).stdout
    data = json.loads(output)

    display_names = []
    for gpu in data.get("SPDisplaysDataType", []):
        for display in gpu.get("spdisplays_ndrvs", []):
            name = display.get("_name")
            if name:
                display_names.append(name)

    names = {}
    with mss.MSS() as sct:
        for monitor, name in zip(sct.monitors[1:], display_names):
            key = (monitor["left"], monitor["top"], monitor["width"], monitor["height"])
            names[key] = name
    return names


def _linux_monitor_names() -> dict:
    """xrandr gives us connector name + exact geometry (matching mss's
    keys directly); the monitor's model name comes from parsing the
    EDID descriptor block sysfs exposes for that connector."""
    output = subprocess.run(["xrandr", "--query"], capture_output=True, text=True, timeout=5, check=False).stdout

    names = {}
    for line in output.splitlines():
        match = re.match(r"^(\S+) connected(?: primary)? (\d+)x(\d+)\+(\d+)\+(\d+)", line)
        if not match:
            continue
        connector, width, height, left, top = match.groups()
        model = _read_edid_name(connector)
        if model:
            key = (int(left), int(top), int(width), int(height))
            names[key] = model
    return names


def _read_edid_name(connector: str) -> str | None:
    from pathlib import Path

    for edid_path in Path("/sys/class/drm").glob(f"*{connector}*/edid"):
        try:
            data = edid_path.read_bytes()
        except Exception:
            continue
        name = _parse_edid_monitor_name(data)
        if name:
            return name
    return None


def _parse_edid_monitor_name(edid: bytes) -> str | None:
    # EDID descriptor blocks live at bytes 54-125, 18 bytes each; a
    # monitor-name descriptor starts with 00 00 00 FC 00.
    for offset in range(54, 126, 18):
        block = edid[offset:offset + 18]
        if len(block) == 18 and block[0:5] == b"\x00\x00\x00\xfc\x00":
            text = block[5:].split(b"\x0a")[0]
            name = text.decode("ascii", errors="ignore").strip()
            if name:
                return name
    return None


if __name__ == "__main__":
    # Self-check: the EDID parser is the only pure-logic piece here
    # worth testing without real hardware/OS calls.
    fake_edid = bytearray(128)
    fake_edid[54:59] = b"\x00\x00\x00\xfc\x00"
    fake_edid[59:72] = b"LG ULTRAGEAR\x0a"
    assert _parse_edid_monitor_name(bytes(fake_edid)) == "LG ULTRAGEAR"
    assert _parse_edid_monitor_name(bytes(128)) is None
    print("monitor_names self-check OK")
