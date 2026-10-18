"""Screen/click/keystroke recorder.

Ported from the original monolithic studio.py (start_recording,
record_video_thread, on_click, on_key_press, stop_recording) into a
standalone class with no Tkinter/UI dependency, so it can be unit-poked
and reused without dragging the whole app window along.
"""
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import mss
import numpy as np
from pynput import keyboard, mouse

from ..platform_utils import get_active_window_info

logger = logging.getLogger("autodoc.recorder")


def overlay_watermark(background: np.ndarray, overlay: np.ndarray | None) -> np.ndarray:
    if overlay is None:
        return background
    h, w = overlay.shape[:2]
    bh, bw = background.shape[:2]
    y_offset, x_offset = bh - h - 20, 20
    try:
        if overlay.shape[2] == 4:
            alpha = overlay[:, :, 3] / 255.0
            for c in range(3):
                background[y_offset:y_offset + h, x_offset:x_offset + w, c] = (
                    alpha * overlay[:, :, c]
                    + (1 - alpha) * background[y_offset:y_offset + h, x_offset:x_offset + w, c]
                )
        else:
            background[y_offset:y_offset + h, x_offset:x_offset + w] = overlay
    except Exception:
        logger.exception("Failed to composite watermark")
    return background


@dataclass
class RecorderOptions:
    client_facing: bool = False
    cursor_effects: bool = True
    log_keystrokes: bool = True


@dataclass
class Step:
    file: str
    path: str
    x: int
    y: int
    keys: str
    time: float
    window_title: str = ""
    caption_override: str = ""  # set by the user in the review grid; "" means auto-caption at export


class Recorder:
    """Owns the video-writer thread and the global mouse/keyboard hooks
    for one recording session. Not thread-safe for concurrent sessions
    by design -- one Recorder = one recording."""

    def __init__(
        self,
        project_dir: Path,
        monitor: dict,
        options: RecorderOptions,
        watermark_img: np.ndarray | None = None,
        on_hotkey_pause: callable = None,
        on_hotkey_stop: callable = None,
    ):
        self.project_dir = project_dir
        self.monitor = monitor
        self.options = options
        self.watermark_img = watermark_img
        self._on_hotkey_pause = on_hotkey_pause
        self._on_hotkey_stop = on_hotkey_stop

        self.is_recording = False
        self.is_paused = False
        self.step_count = 0
        self.click_data: list[Step] = []
        self._current_keys: list[str] = []
        self.start_time = 0.0

        self._mouse_ctrl = mouse.Controller()
        self._ripple_frames = 0
        self._ripple_pos = (0, 0)

        self._video_thread: threading.Thread | None = None
        self._mouse_listener: mouse.Listener | None = None
        self._keyboard_listener: keyboard.Listener | None = None

    # -- lifecycle -----------------------------------------------------
    def start(self):
        os.makedirs(self.project_dir, exist_ok=True)
        self.is_recording = True
        self.is_paused = False
        self.step_count = 0
        self.click_data = []
        self._current_keys = []
        self._ripple_frames = 0
        self.start_time = time.time()

        self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self._keyboard_listener.start()
        self._mouse_listener = mouse.Listener(on_click=self._on_click)
        self._mouse_listener.start()

        self._video_thread = threading.Thread(target=self._record_video_thread, daemon=True)
        self._video_thread.start()

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def stop(self) -> list[Step]:
        self.is_recording = False
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._video_thread:
            self._video_thread.join(timeout=5)
        return self.click_data

    # -- video thread ----------------------------------------------------
    def _record_video_thread(self):
        video_path = os.path.join(self.project_dir, "recording.mp4")
        with mss.MSS() as sct:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(video_path, fourcc, 10.0, (self.monitor["width"], self.monitor["height"]))

            while self.is_recording:
                if self.is_paused:
                    time.sleep(0.1)
                    continue

                img = np.array(sct.grab(self.monitor))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                if self.options.cursor_effects:
                    self._draw_cursor_fx(frame)

                if self.watermark_img is not None:
                    frame = overlay_watermark(frame, self.watermark_img)

                out.write(frame)
                time.sleep(0.1)

            out.release()

    def _draw_cursor_fx(self, frame: np.ndarray):
        mx, my = self._mouse_ctrl.position
        rel_x = int(mx - self.monitor["left"])
        rel_y = int(my - self.monitor["top"])

        overlay = frame.copy()
        cv2.circle(overlay, (rel_x, rel_y), 25, (0, 255, 255), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

        if self._ripple_frames > 0:
            rx, ry = self._ripple_pos
            radius = 30 + ((10 - self._ripple_frames) * 3)
            cv2.circle(frame, (rx, ry), radius, (0, 0, 255), 3)
            self._ripple_frames -= 1

    # -- input hooks -----------------------------------------------------
    def _on_click(self, x, y, button, pressed):
        if not (pressed and self.is_recording and not self.is_paused):
            return
        m = self.monitor
        if not (m["left"] <= x <= m["left"] + m["width"] and m["top"] <= y <= m["top"] + m["height"]):
            return

        rel_x, rel_y = int(x - m["left"]), int(y - m["top"])
        self._ripple_frames = 10
        self._ripple_pos = (rel_x, rel_y)
        timestamp = time.time() - self.start_time

        self.step_count += 1
        filename = f"step_{self.step_count:03d}.png"
        filepath = os.path.join(self.project_dir, filename)

        active = get_active_window_info()
        window_title = (active or {}).get("title", "") or ""

        crop_rect = self.monitor
        if self.options.client_facing and active:
            left = max(m["left"], active["left"])
            top = max(m["top"], active["top"])
            width = min(m["width"], active["width"])
            height = min(m["height"], active["height"])
            if width > 0 and height > 0:
                crop_rect = {"left": left, "top": top, "width": width, "height": height}

        try:
            with mss.MSS() as sct:
                img = np.array(sct.grab(crop_rect))
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                if self.watermark_img is not None:
                    img = overlay_watermark(img, self.watermark_img)
                cv2.imwrite(filepath, img)
        except Exception:
            logger.exception("Failed to capture step screenshot for step %s", self.step_count)
            self.step_count -= 1
            return

        keys_typed = " ".join(self._current_keys)
        self.click_data.append(Step(filename, filepath, rel_x, rel_y, keys_typed, timestamp, window_title))
        self._current_keys = []

    def _on_key_press(self, key):
        if key == keyboard.Key.f8:
            self.toggle_pause()
            if self._on_hotkey_pause:
                self._on_hotkey_pause()
            return
        if key == keyboard.Key.f9:
            if self._on_hotkey_stop:
                self._on_hotkey_stop()
            return

        if not (self.is_recording and not self.is_paused and self.options.log_keystrokes):
            return
        try:
            char = key.char
            if char is not None:
                self._current_keys.append(char)
        except AttributeError:
            key_name = str(key).replace("Key.", "").capitalize()
            if "<" not in key_name:
                self._current_keys.append(f"[{key_name}]")
