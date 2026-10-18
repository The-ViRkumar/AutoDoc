"""Recorder page: configure + run a recording session, then export the guide."""
import logging
import os
import queue

import cv2
import customtkinter as ctk
from tkinter import filedialog, messagebox

from .. import config as app_config
from ..core.annotator import annotate_steps
from ..core.exporter import ExportOptions, run_export
from ..core.packaging import package_for_delivery
from ..core.recorder import Recorder, RecorderOptions
from ..platform_utils import active_window_supported, find_tesseract, open_in_file_manager, tesseract_install_hint
from ..theme import (
    ACCENT,
    ACCENT_HOVER,
    BORDER,
    FONT_BODY,
    FONT_BUTTON,
    FONT_SECTION,
    FONT_SMALL,
    PRIMARY,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    TEXT_MUTED,
    WARNING,
)
from .floating_toolbar import FloatingToolbar
from .review_grid import show_review
from .tooltip import Tooltip

logger = logging.getLogger("autodoc.recorder_tab")


def _card(parent, title: str) -> ctk.CTkFrame:
    card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
    card.pack(fill="x", pady=(0, 16))
    ctk.CTkLabel(card, text=title, font=FONT_SECTION, text_color=TEXT).pack(anchor="w", padx=18, pady=(14, 8))
    return card


class RecorderTab(ctk.CTkFrame):
    def __init__(self, master, root_window, monitors: list, monitor_names: list):
        super().__init__(master, fg_color="transparent")
        self.root_window = root_window
        self.monitors = monitors
        self.monitor_names = monitor_names
        self.cfg = app_config.load()

        self.watermark_path = self.cfg.get("watermark_path", "")
        self.watermark_img = None
        if self.watermark_path and os.path.exists(self.watermark_path):
            self._load_watermark(self.watermark_path)

        self.tesseract_path = find_tesseract()
        self._recorder: Recorder | None = None
        self._toolbar: FloatingToolbar | None = None
        self._hotkey_queue: queue.Queue = queue.Queue()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    # -- UI ---------------------------------------------------------------
    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))
        ctk.CTkLabel(header, text="Live Recorder", font=("Segoe UI", 20, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(header, text="Capture a workflow, then export a ready-to-share guide.", font=FONT_BODY, text_color=TEXT_MUTED).pack(anchor="w")

        # Two independent columns, each packing its own cards top-down by
        # natural content height -- a shared grid row would force the
        # shorter card in each row to stretch and match its taller
        # neighbor, leaving an ugly empty void inside it.
        columns = ctk.CTkFrame(self, fg_color="transparent")
        columns.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 8))
        columns.grid_columnconfigure((0, 1), weight=1, uniform="col")
        columns.grid_rowconfigure(0, weight=1)

        col_left = ctk.CTkFrame(columns, fg_color="transparent")
        col_left.grid(row=0, column=0, sticky="new", padx=8)
        col_right = ctk.CTkFrame(columns, fg_color="transparent")
        col_right.grid(row=0, column=1, sticky="new", padx=8)

        # -- Project card (left) --------------------------------------------
        project_card = _card(col_left, "Project")
        self.project_entry = ctk.CTkEntry(project_card, placeholder_text="Project name (e.g. Client_NAS_Setup)", height=34)
        self.project_entry.pack(fill="x", padx=18, pady=(0, 8))

        self.display_combo = ctk.CTkComboBox(project_card, values=self.monitor_names, state="readonly", height=34)
        saved_idx = self.cfg.get("monitor_index", 0)
        if self.monitor_names:
            idx = saved_idx if saved_idx < len(self.monitor_names) else 0
            self.display_combo.set(self.monitor_names[idx])
        self.display_combo.pack(fill="x", padx=18, pady=(0, 14))

        self.brand_btn = ctk.CTkButton(
            project_card, text="Add custom watermark / logo", fg_color=SURFACE_ALT, hover_color=BORDER,
            text_color=TEXT, height=34, corner_radius=10, command=self.select_watermark,
        )
        self.brand_btn.pack(fill="x", padx=18, pady=(0, 14))
        if self.watermark_img is not None:
            self.brand_btn.configure(text=f"Watermark loaded: {os.path.basename(self.watermark_path)}")

        # -- Capture settings card (right) -----------------------------------
        capture_card = _card(col_right, "Capture settings")
        self.client_facing_var = ctk.BooleanVar(value=False)
        self.effects_var = ctk.BooleanVar(value=True)
        self.keys_var = ctk.BooleanVar(value=True)
        self.annot_var = ctk.BooleanVar(value=True)

        crop_supported = active_window_supported()
        crop_label = "Client-facing mode (crop active window)"
        if not crop_supported:
            crop_label += " — unavailable on Linux"
        crop_check = self._checkbox(
            capture_card, crop_label, self.client_facing_var,
            tooltip="Crops each screenshot to the active application window instead of the full screen.",
        )
        if not crop_supported:
            crop_check.configure(state="disabled")

        self._checkbox(
            capture_card, "Cursor halo + click ripple effects", self.effects_var,
            tooltip="Draws a soft glow around the cursor and a ripple on each click in the recorded video.",
        )
        self._checkbox(
            capture_card, "Log keystrokes between clicks", self.keys_var,
            tooltip="Captures what you typed between clicks and shows it under that step.",
        )
        self._checkbox(
            capture_card, "Manual annotation pass after stop", self.annot_var,
            tooltip="After stopping, opens each screenshot so you can blur or highlight areas before exporting.",
        )
        self.redact_var = ctk.BooleanVar(value=False)
        self._checkbox(
            capture_card, "Auto-redact sensitive text", self.redact_var, pad_bottom=10,
            tooltip="Scans each step's caption for emails, IPs, keys, and passwords — blurs that part of the screenshot and redacts the caption when found.",
        )

        if not self.tesseract_path:
            ctk.CTkLabel(
                capture_card, text=f"Tesseract OCR not found — captions skip the auto-guess. Install: {tesseract_install_hint()}",
                font=FONT_SMALL, text_color=WARNING, wraplength=280, justify="left",
            ).pack(anchor="w", padx=18, pady=(0, 12))

        # -- Export card (left) -----------------------------------------------
        export_card = _card(col_left, "Export")
        self.md_var = ctk.BooleanVar(value=True)
        self.pdf_var = ctk.BooleanVar(value=True)
        self.html_var = ctk.BooleanVar(value=True)
        self.lang_var = ctk.StringVar(value=self.cfg.get("language", "English Only"))

        self._checkbox(export_card, "Markdown (guide.md)", self.md_var, tooltip="A plain-text guide with embedded image links.")
        self._checkbox(export_card, "Printable PDF-style HTML", self.pdf_var, tooltip="A styled page with a print-to-PDF button.")
        self._checkbox(export_card, "Interactive HTML wizard", self.html_var, pad_bottom=10, tooltip="Pairs the recording video with clickable steps that seek to each moment.")

        self.lang_combo = ctk.CTkComboBox(export_card, variable=self.lang_var, values=["English Only", "English + Gujarati", "English + Hindi", "All Three"], state="readonly", height=32)
        self.lang_combo.pack(fill="x", padx=18, pady=(0, 14))
        Tooltip(self.lang_combo, "Adds a translated caption under each English step.")

        # -- Action card (right) -----------------------------------------------
        action_card = _card(col_right, "Start")

        ctk.CTkLabel(
            action_card, text="Everything above can be changed any time before you hit start.",
            font=FONT_SMALL, text_color=TEXT_MUTED, wraplength=280, justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 16))

        self.record_btn = ctk.CTkButton(
            action_card, text="●  START RECORDING", font=FONT_BUTTON, height=48,
            fg_color=PRIMARY, hover_color=ACCENT_HOVER, corner_radius=12, command=self.start_recording,
        )
        self.record_btn.pack(fill="x", padx=18, pady=(0, 10))

        self.status_label = ctk.CTkLabel(action_card, text="Ready", font=FONT_BODY, text_color=TEXT_MUTED)
        self.status_label.pack(pady=(0, 16))

        self.progress = ctk.CTkProgressBar(action_card, mode="indeterminate", progress_color=ACCENT)

    @staticmethod
    def _checkbox(parent, text, variable, pad_bottom=6, tooltip=None):
        cb = ctk.CTkCheckBox(parent, text=text, variable=variable, fg_color=PRIMARY, hover_color=ACCENT_HOVER, font=FONT_BODY, text_color=TEXT)
        cb.pack(anchor="w", padx=20, pady=(0, pad_bottom))
        if tooltip:
            Tooltip(cb, tooltip)
        return cb

    def _load_watermark(self, filepath: str):
        img = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
        if img is None:
            return
        h, w = img.shape[:2]
        new_w = 150
        new_h = int((new_w / w) * h)
        self.watermark_img = cv2.resize(img, (new_w, new_h))

    def select_watermark(self):
        filepath = filedialog.askopenfilename(title="Select Logo/Watermark", filetypes=[("Images", "*.png *.jpg")])
        if not filepath:
            return
        self.watermark_path = filepath
        self._load_watermark(filepath)
        self.brand_btn.configure(text=f"Watermark loaded: {os.path.basename(filepath)}")

    # -- recording lifecycle -----------------------------------------------
    def start_recording(self):
        project_name = self.project_entry.get().strip()
        if not project_name:
            return messagebox.showerror("Error", "Enter Project Name")

        monitor_index = self.display_combo.cget("values").index(self.display_combo.get())
        monitor = self.monitors[monitor_index]
        project_dir = os.path.join(os.getcwd(), project_name)

        if os.path.isdir(project_dir) and os.listdir(project_dir):
            if not messagebox.askyesno(
                "Project already exists",
                f"'{project_name}' already has files in it. Recording into it may mix old and new steps.\n\nContinue anyway?",
            ):
                return

        options = RecorderOptions(
            client_facing=self.client_facing_var.get() and active_window_supported(),
            cursor_effects=self.effects_var.get(),
            log_keystrokes=self.keys_var.get(),
        )

        # pynput's listener callbacks fire on their own background thread,
        # never on the Tk main thread -- touching widgets or popping a
        # messagebox from there is unsafe. F8/F9 only ever push an action
        # onto a thread-safe queue; _poll_hotkeys (scheduled via `after`,
        # so it always runs on the main thread) is what actually acts on it.
        # Fresh queue each session so a stale action can't leak into the next.
        self._hotkey_queue = queue.Queue()
        self._recorder = Recorder(
            project_dir, monitor, options, watermark_img=self.watermark_img,
            on_hotkey_pause=lambda: self._hotkey_queue.put("pause"),
            on_hotkey_stop=lambda: self._hotkey_queue.put("stop"),
        )
        self._recorder.start()

        app_config.save({
            **self.cfg,
            "watermark_path": self.watermark_path,
            "language": self.lang_var.get(),
            "monitor_index": monitor_index,
        })

        self.root_window.iconify()
        self._toolbar = FloatingToolbar(self.root_window, self._recorder, on_pause=self._on_toolbar_pause, on_stop=self.stop_recording)
        self._poll_hotkeys()

    def _on_toolbar_pause(self):
        self._recorder.toggle_pause()
        self._toolbar.set_paused(self._recorder.is_paused)

    def _poll_hotkeys(self):
        if not self._recorder:
            return  # recording already stopped; nothing left to poll for
        try:
            while True:
                action = self._hotkey_queue.get_nowait()
                if action == "pause" and self._toolbar:
                    self._toolbar.set_paused(self._recorder.is_paused)
                elif action == "stop":
                    self.stop_recording()
                    return  # stop_recording() clears self._recorder; loop ends
        except queue.Empty:
            pass
        self.after(150, self._poll_hotkeys)

    def stop_recording(self):
        if not self._recorder:
            return
        steps = self._recorder.stop()
        project_dir = self._recorder.project_dir

        if self._toolbar:
            try:
                self._toolbar.destroy()
            except Exception:
                pass
            self._toolbar = None
        self.root_window.deiconify()

        steps = show_review(self.root_window, steps)

        self.status_label.configure(text="Processing outputs & compiling data...", text_color=ACCENT)
        self.progress.pack(fill="x", padx=18, pady=(0, 16))
        self.progress.start()
        self.update()

        if self.annot_var.get() and steps:
            annotate_steps(steps, show_instructions=lambda msg: messagebox.showinfo("Annotation", msg))

        languages = set()
        if "Hindi" in self.lang_var.get() or "All Three" in self.lang_var.get():
            languages.add("hi")
        if "Gujarati" in self.lang_var.get() or "All Three" in self.lang_var.get():
            languages.add("gu")

        export_options = ExportOptions(
            tesseract_path=self.tesseract_path,
            client_facing=self.client_facing_var.get(),
            redact_sensitive=self.redact_var.get(),
            languages=languages,
            want_markdown=self.md_var.get(),
            want_pdf=self.pdf_var.get(),
            want_html=self.html_var.get(),
        )
        export_failed = False
        try:
            run_export(project_dir, os.path.basename(project_dir), steps, export_options)
        except Exception:
            logger.exception("Export failed for project %s", project_dir)
            export_failed = True
            messagebox.showerror("Export Error", "Something went wrong generating the guide. Check the log for details.")

        self.progress.stop()
        self.progress.pack_forget()
        self.status_label.configure(text="Ready", text_color=TEXT_MUTED)

        if not export_failed:
            app_config.add_recent_project(self.cfg, os.path.basename(project_dir), project_dir)
            app_config.save(self.cfg)
            if hasattr(self.root_window, "refresh_recent"):
                self.root_window.refresh_recent()

            if messagebox.askyesno("Package for delivery", "Zip the guide + media into a single file to share with the client?"):
                try:
                    zip_path = package_for_delivery(project_dir)
                    messagebox.showinfo("Packaged", f"Created:\n{zip_path}")
                except Exception:
                    logger.exception("Failed to package project %s for delivery", project_dir)
                    messagebox.showerror("Package Error", "Couldn't create the zip. Check the log for details.")

            if messagebox.askyesno("Complete", f"Project successfully saved and exported to:\n{project_dir}\n\nOpen the folder now?"):
                try:
                    open_in_file_manager(project_dir)
                except Exception:
                    logger.exception("Failed to open project folder %s", project_dir)

        self._recorder = None
