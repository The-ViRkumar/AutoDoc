"""Extractor page: sample screenshots out of any video file at a fixed interval."""
import logging
import os
import threading

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ..core.video_extractor import extract_frames
from ..theme import ACCENT, ACCENT_HOVER, BORDER, FONT_BODY, FONT_BUTTON, FONT_SECTION, PRIMARY, SURFACE, SURFACE_ALT, TEXT, TEXT_MUTED

logger = logging.getLogger("autodoc.extractor_tab")


def _card(parent, title: str, row: int, col: int) -> ctk.CTkFrame:
    card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
    card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
    ctk.CTkLabel(card, text=title, font=FONT_SECTION, text_color=TEXT).pack(anchor="w", padx=18, pady=(14, 8))
    return card


class ExtractorTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._progress_state = {"current": 0, "total": 0}
        self._extract_result = None
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))
        ctk.CTkLabel(header, text="Video Extractor", font=("Segoe UI", 20, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(header, text="Sample screenshots out of any existing video at a fixed interval.", font=FONT_BODY, text_color=TEXT_MUTED).pack(anchor="w")

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 8))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="col")
        grid.grid_rowconfigure(0, weight=1)

        video_card = _card(grid, "Source video", row=0, col=0)
        self.video_entry = ctk.CTkEntry(video_card, height=34, placeholder_text="No video selected")
        self.video_entry.pack(fill="x", padx=18, pady=(0, 8))
        ctk.CTkButton(video_card, text="Browse video", command=self.select_video, fg_color=SURFACE_ALT, hover_color=BORDER, text_color=TEXT, height=32).pack(anchor="w", padx=18, pady=(0, 14))

        output_card = _card(grid, "Output folder", row=0, col=1)
        self.output_entry = ctk.CTkEntry(output_card, height=34, placeholder_text="No folder selected")
        self.output_entry.pack(fill="x", padx=18, pady=(0, 8))
        ctk.CTkButton(output_card, text="Browse folder", command=self.select_output, fg_color=SURFACE_ALT, hover_color=BORDER, text_color=TEXT, height=32).pack(anchor="w", padx=18, pady=(0, 14))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 20))
        footer.grid_columnconfigure(0, weight=1)

        interval_row = ctk.CTkFrame(footer, fg_color="transparent")
        interval_row.grid(row=0, column=0, sticky="w", pady=(0, 12))
        ctk.CTkLabel(interval_row, text="Extract every (seconds)", font=FONT_BODY, text_color=TEXT_MUTED).pack(side="left", padx=(0, 10))
        self.interval_entry = ctk.CTkEntry(interval_row, width=80, height=32)
        self.interval_entry.insert(0, "2")
        self.interval_entry.pack(side="left")

        self.progress = ctk.CTkProgressBar(footer, mode="determinate", progress_color=ACCENT)
        self.progress.set(0)

        self.extract_btn = ctk.CTkButton(
            footer, text="\U0001f4f8  EXTRACT SCREENSHOTS", font=FONT_BUTTON, height=48,
            fg_color=PRIMARY, hover_color=ACCENT_HOVER, corner_radius=12, command=self.extract,
        )
        self.extract_btn.grid(row=2, column=0, sticky="ew")

    def select_video(self):
        filepath = filedialog.askopenfilename(title="Select Video", filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if filepath:
            self.video_entry.delete(0, ctk.END)
            self.video_entry.insert(0, filepath)

    def select_output(self):
        folderpath = filedialog.askdirectory(title="Select Output Folder")
        if folderpath:
            self.output_entry.delete(0, ctk.END)
            self.output_entry.insert(0, folderpath)

    def extract(self):
        video_path, output_folder = self.video_entry.get(), self.output_entry.get()
        if not os.path.isfile(video_path):
            return messagebox.showerror("Error", "Select a valid video file")
        if not os.path.isdir(output_folder):
            return messagebox.showerror("Error", "Select a valid output folder")
        try:
            interval = float(self.interval_entry.get())
        except ValueError:
            return messagebox.showerror("Error", "Interval must be a number")

        self.extract_btn.configure(state="disabled", text="Extracting...")
        self.progress.set(0)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self._progress_state = {"current": 0, "total": 0}
        self._extract_result = None

        def on_progress(current, total):
            self._progress_state["current"] = current
            self._progress_state["total"] = total

        def worker():
            try:
                saved = extract_frames(video_path, output_folder, interval, on_progress=on_progress)
                self._extract_result = ("done", saved)
            except Exception as exc:
                logger.exception("Frame extraction failed for %s", video_path)
                self._extract_result = ("error", str(exc))

        threading.Thread(target=worker, daemon=True).start()
        self._poll_progress()

    def _poll_progress(self):
        total = self._progress_state["total"]
        if total:
            self.progress.set(min(1.0, self._progress_state["current"] / total))
        else:
            self.progress.set(0)

        if self._extract_result is None:
            self.after(100, self._poll_progress)
            return

        status, payload = self._extract_result
        self.progress.grid_forget()
        self.extract_btn.configure(state="normal", text="\U0001f4f8  EXTRACT SCREENSHOTS")

        if status == "done":
            messagebox.showinfo("Done", f"Extracted {payload} images.")
        else:
            messagebox.showerror("Error", f"Extraction failed: {payload}")
