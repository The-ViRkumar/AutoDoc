"""Small always-on-top pause/stop control shown while recording, since
the main window is minimized during a recording session. Also shows a
live step counter + elapsed time so there's some feedback that
something is actually being captured while the main window is hidden.
"""
import time

import customtkinter as ctk

from ..theme import ACCENT, DANGER, FONT_SMALL, SIDEBAR_BG, TEXT_MUTED, WARNING


class FloatingToolbar(ctk.CTkToplevel):
    def __init__(self, master, recorder, on_pause, on_stop):
        super().__init__(master)
        self._recorder = recorder
        self._on_pause = on_pause
        self._on_stop = on_stop
        self._tick_job = None

        self.title("Controls")
        self.geometry("220x78")
        self.configure(fg_color=SIDEBAR_BG)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"+{screen_width - 270}+{screen_height - 130}")

        self.status_label = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=TEXT_MUTED)
        self.status_label.pack(pady=(8, 2))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.pause_btn = ctk.CTkButton(
            btn_frame, text="⏸ Pause (F8)", width=90, command=self._toggle,
            fg_color=WARNING, text_color="black", corner_radius=8,
        )
        self.pause_btn.pack(side="left", padx=4, pady=4)
        ctk.CTkButton(
            btn_frame, text="⏹ Stop (F9)", width=90, command=self._on_stop,
            fg_color=DANGER, corner_radius=8,
        ).pack(side="right", padx=4, pady=4)

        self._tick()

    def _tick(self):
        elapsed = int(time.time() - self._recorder.start_time)
        mins, secs = divmod(max(0, elapsed), 60)
        state = "Paused" if self._recorder.is_paused else "Recording"
        self.status_label.configure(text=f"{state}  •  {mins:02d}:{secs:02d}  •  {self._recorder.step_count} steps")
        self._tick_job = self.after(500, self._tick)

    def destroy(self):
        if self._tick_job:
            self.after_cancel(self._tick_job)
        super().destroy()

    def _toggle(self):
        self._on_pause()

    def set_paused(self, is_paused: bool):
        if is_paused:
            self.pause_btn.configure(text="▶ Resume (F8)", fg_color=ACCENT, text_color="black")
        else:
            self.pause_btn.configure(text="⏸ Pause (F8)", fg_color=WARNING, text_color="black")
