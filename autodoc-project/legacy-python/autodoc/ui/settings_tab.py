"""Settings / About page: diagnostics (Tesseract, config/log paths) and
app credit, consolidated in one place instead of scattered inline text.
"""
import webbrowser

import customtkinter as ctk

from ..platform_utils import config_path, find_tesseract, log_path, tesseract_install_hint
from ..theme import BORDER, FONT_BODY, FONT_SECTION, FONT_SMALL, PRIMARY, SURFACE, TEXT, TEXT_MUTED
from ..version import AUTHOR_NAME, AUTHOR_URL, __version__


def _card(parent, title: str, row: int, col: int) -> ctk.CTkFrame:
    card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
    card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
    ctk.CTkLabel(card, text=title, font=FONT_SECTION, text_color=TEXT).pack(anchor="w", padx=18, pady=(14, 8))
    return card


def _kv(parent, key: str, value: str):
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=18, pady=(0, 10))
    ctk.CTkLabel(row, text=key, font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")
    ctk.CTkLabel(row, text=value, font=FONT_BODY, text_color=TEXT, wraplength=320, justify="left").pack(anchor="w")


def _link(parent, text: str, url: str):
    label = ctk.CTkLabel(parent, text=text, font=FONT_BODY, text_color=PRIMARY, cursor="hand2")
    label.pack(anchor="w", padx=18, pady=(0, 14))
    label.bind("<Button-1>", lambda _e: webbrowser.open(url))
    return label


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))
        ctk.CTkLabel(header, text="Settings", font=("Segoe UI", 20, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(header, text="Diagnostics and app info.", font=FONT_BODY, text_color=TEXT_MUTED).pack(anchor="w")

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 8))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="col")
        grid.grid_rowconfigure(0, weight=1)

        diag_card = _card(grid, "Diagnostics", row=0, col=0)
        tesseract = find_tesseract()
        _kv(diag_card, "Tesseract OCR", tesseract or f"Not found — {tesseract_install_hint()}")
        _kv(diag_card, "Config file", str(config_path()))
        _kv(diag_card, "Log file", str(log_path()))

        about_card = _card(grid, "About", row=0, col=1)
        _kv(about_card, "AutoDoc version", f"v{__version__}")
        ctk.CTkLabel(about_card, text="Made by", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=18)
        _link(about_card, f"{AUTHOR_NAME}  —  {AUTHOR_URL}", AUTHOR_URL)
