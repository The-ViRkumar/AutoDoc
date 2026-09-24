import platform
import webbrowser

import customtkinter as ctk
import mss

from . import config as app_config
from .monitor_names import get_monitor_names
from .platform_utils import app_icon_path, open_in_file_manager
from .theme import (
    BG,
    BORDER,
    FONT_BRAND,
    FONT_NAV,
    FONT_TAGLINE,
    PRIMARY,
    SIDEBAR_BG,
    TEXT,
    TEXT_MUTED,
)
from .ui.extractor_tab import ExtractorTab
from .ui.recorder_tab import RecorderTab
from .ui.settings_tab import SettingsTab
from .version import AUTHOR_NAME, AUTHOR_URL, __version__

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

NAV_ITEMS = [
    ("\U0001f534", "Recorder", "Record a workflow"),
    ("\U0001f39e️", "Extractor", "Sample a video"),
    ("⚙️", "Settings", "Diagnostics & about"),
]


class AutoDoc(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"AutoDoc v{__version__}")
        self.configure(fg_color=BG)
        self._set_window_icon()
        self._fit_and_center()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        monitors, monitor_names = self._get_monitors()

        self._build_sidebar()
        self._build_content(monitors, monitor_names)
        self._select_nav(0)

    # -- window sizing -------------------------------------------------
    def _fit_and_center(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        width = min(1180, max(860, int(screen_w * 0.68)))
        height = min(880, max(620, int(screen_h * 0.78)))
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(760, 560)
        self.resizable(True, True)

    def _set_window_icon(self):
        icon = app_icon_path()
        if not icon:
            return
        try:
            if platform.system() == "Windows":
                self.iconbitmap(str(icon))
            else:
                from PIL import Image, ImageTk

                self._icon_image = ImageTk.PhotoImage(Image.open(icon))  # keep a ref, Tk needs it alive
                self.iconphoto(True, self._icon_image)
        except Exception:
            pass

    # -- layout ----------------------------------------------------------
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, corner_radius=0, width=210)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(28, 6))
        ctk.CTkLabel(brand, text="AutoDoc", font=FONT_BRAND, text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(brand, text="Guide recording, automated", font=FONT_TAGLINE, text_color=TEXT_MUTED).pack(anchor="w")

        divider = ctk.CTkFrame(sidebar, fg_color=BORDER, height=1)
        divider.pack(fill="x", padx=20, pady=(18, 18))

        self._nav_buttons = []
        for index, (icon, label, subtitle) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                sidebar, text=f"{icon}   {label}", font=FONT_NAV, anchor="w",
                fg_color="transparent", hover_color=BORDER, text_color=TEXT_MUTED,
                corner_radius=8, height=44,
                command=lambda i=index: self._select_nav(i),
            )
            btn.pack(fill="x", padx=14, pady=4)
            self._nav_buttons.append(btn)

        self._recent_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        self._recent_frame.pack(fill="x", padx=14, pady=(14, 0))
        self._render_recent()

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.pack(side="bottom", pady=(0, 16))
        ctk.CTkLabel(footer, text=f"v{__version__}", font=FONT_TAGLINE, text_color=TEXT_MUTED).pack()
        credit = ctk.CTkLabel(footer, text=f"by {AUTHOR_NAME}", font=FONT_TAGLINE, text_color=TEXT_MUTED, cursor="hand2")
        credit.pack()
        credit.bind("<Button-1>", lambda _e: webbrowser.open(AUTHOR_URL))

    def _render_recent(self):
        for child in self._recent_frame.winfo_children():
            child.destroy()

        recents = app_config.load().get("recent_projects", [])
        if not recents:
            return

        ctk.CTkLabel(self._recent_frame, text="RECENT", font=FONT_TAGLINE, text_color=TEXT_MUTED).pack(anchor="w", padx=6, pady=(0, 4))
        for item in recents:
            ctk.CTkButton(
                self._recent_frame, text=item.get("name", "Project"), font=FONT_TAGLINE, anchor="w",
                fg_color="transparent", hover_color=BORDER, text_color=TEXT_MUTED, corner_radius=6, height=26,
                command=lambda p=item.get("path"): open_in_file_manager(p) if p else None,
            ).pack(fill="x", pady=1)

    def refresh_recent(self):
        self._render_recent()

    def _build_content(self, monitors, monitor_names):
        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self._pages = [
            RecorderTab(self.content, self, monitors, monitor_names),
            ExtractorTab(self.content),
            SettingsTab(self.content),
        ]
        for page in self._pages:
            page.grid(row=0, column=0, sticky="nsew")

    def _select_nav(self, index: int):
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(fg_color=PRIMARY, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)
        self._pages[index].tkraise()

    @staticmethod
    def _get_monitors():
        monitor_brands = get_monitor_names()
        monitors, names = [], []
        with mss.MSS() as sct:
            for i, m in enumerate(sct.monitors[1:], 1):
                monitors.append(m)
                key = (m["left"], m["top"], m["width"], m["height"])
                brand = monitor_brands.get(key)
                label = f"Display {i} — {brand}" if brand else f"Display {i}"
                names.append(f"{label} ({m['width']}x{m['height']})")
        return monitors, names


def main():
    from .logging_setup import configure_logging

    configure_logging()
    app = AutoDoc()
    app.mainloop()


if __name__ == "__main__":
    main()
