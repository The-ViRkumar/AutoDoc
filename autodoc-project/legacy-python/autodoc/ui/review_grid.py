"""Modal step review shown right after a recording stops: delete
unwanted steps and reorder the rest before annotation/export runs.
Replaces having to discover a bad screenshot only once you're deep
into the per-image OpenCV annotation pass.
"""
import os

import customtkinter as ctk
from PIL import Image

from ..theme import ACCENT_HOVER, BORDER, DANGER, FONT_BODY, FONT_BUTTON, FONT_SECTION, FONT_SMALL, PRIMARY, SURFACE, TEXT, TEXT_MUTED

THUMB_SIZE = (160, 90)


class _ReviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, steps: list):
        super().__init__(parent)
        self.title("Review Steps")
        self.geometry("640x640")
        self.transient(parent)
        self.grab_set()
        self.result = list(steps)
        self._thumb_cache = []  # keep CTkImage refs alive across re-renders

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(header, text="Review captured steps", font=FONT_SECTION, text_color=TEXT).pack(anchor="w")
        self.count_label = ctk.CTkLabel(header, text="", font=FONT_SMALL, text_color=TEXT_MUTED)
        self.count_label.pack(anchor="w")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        ctk.CTkButton(
            self, text="Continue", font=FONT_BUTTON, height=44, fg_color=PRIMARY,
            hover_color=ACCENT_HOVER, corner_radius=10, command=self._finish,
        ).pack(fill="x", padx=20, pady=(0, 16))

        self.protocol("WM_DELETE_WINDOW", self._finish)
        self._render()

    def _render(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        self._thumb_cache.clear()

        self.count_label.configure(text=f"{len(self.result)} step(s) — reorder, edit captions, or remove before exporting")

        for index, step in enumerate(self.result):
            row = ctk.CTkFrame(self.list_frame, fg_color=SURFACE, corner_radius=10, border_width=1, border_color=BORDER)
            row.pack(fill="x", pady=6)

            thumb = self._load_thumb(step.path)
            if thumb:
                ctk.CTkLabel(row, image=thumb, text="").pack(side="left", padx=10, pady=10)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, pady=10, padx=(0, 6))
            ctk.CTkLabel(info, text=f"Step {index + 1}", font=FONT_BODY, text_color=TEXT).pack(anchor="w")

            caption_var = ctk.StringVar(value=step.caption_override or step.window_title or "")
            caption_var.trace_add("write", lambda *_a, s=step, v=caption_var: setattr(s, "caption_override", v.get().strip()))
            ctk.CTkEntry(
                info, textvariable=caption_var, placeholder_text="Auto-detect at export",
                height=28, font=FONT_SMALL,
            ).pack(fill="x", pady=(2, 2))

            if step.keys:
                ctk.CTkLabel(info, text=f"Keys: {step.keys}", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")

            controls = ctk.CTkFrame(row, fg_color="transparent")
            controls.pack(side="right", padx=10)
            ctk.CTkButton(controls, text="▲", width=32, height=26, fg_color=SURFACE, hover_color=BORDER, text_color=TEXT, command=lambda i=index: self._move(i, -1)).pack(pady=1)
            ctk.CTkButton(controls, text="▼", width=32, height=26, fg_color=SURFACE, hover_color=BORDER, text_color=TEXT, command=lambda i=index: self._move(i, 1)).pack(pady=1)
            ctk.CTkButton(controls, text="Delete", width=64, height=26, fg_color=DANGER, hover_color="#C1304F", command=lambda i=index: self._delete(i)).pack(pady=1)

    def _load_thumb(self, path):
        try:
            img = Image.open(path)
            img.thumbnail(THUMB_SIZE)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self._thumb_cache.append(ctk_img)
            return ctk_img
        except Exception:
            return None

    def _move(self, index, delta):
        target = index + delta
        if 0 <= target < len(self.result):
            self.result[index], self.result[target] = self.result[target], self.result[index]
            self._render()

    def _delete(self, index):
        step = self.result.pop(index)
        try:
            if os.path.exists(step.path):
                os.remove(step.path)
        except Exception:
            pass
        self._render()

    def _finish(self):
        self.grab_release()
        self.destroy()


def show_review(parent, steps: list) -> list:
    """Blocks until the user hits Continue (or closes the dialog).
    Returns the kept steps in their (possibly reordered) final order."""
    if not steps:
        return steps
    dialog = _ReviewDialog(parent, steps)
    parent.wait_window(dialog)
    return dialog.result
