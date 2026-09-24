"""Minimal hover tooltip for CTk widgets. No external dependency --
just a small always-on-top Toplevel shown on <Enter>/hidden on <Leave>.
"""
import customtkinter as ctk

from ..theme import FONT_SMALL, SURFACE_ALT, TEXT


class Tooltip:
    def __init__(self, widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _show(self):
        if self._tip or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip = ctk.CTkToplevel(self.widget)
        self._tip.overrideredirect(True)
        self._tip.attributes("-topmost", True)
        self._tip.configure(fg_color=SURFACE_ALT)
        self._tip.geometry(f"+{x}+{y}")
        ctk.CTkLabel(
            self._tip, text=self.text, font=FONT_SMALL, text_color=TEXT,
            wraplength=240, justify="left",
        ).pack(padx=8, pady=4)

    def _hide(self, _event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip:
            self._tip.destroy()
            self._tip = None
