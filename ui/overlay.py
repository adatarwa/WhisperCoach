"""
overlay.py
A transparent, always-on-top floating window that shows whispers
on screen while you're in any call. Stays out of the way until
there's something to say. Works on Mac and Windows.

Uses tkinter (built into Python — no extra install needed).
"""

import tkinter as tk
import queue
import threading
import time
import platform


# --- Visual config ---
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 80
MARGIN_RIGHT = 30       # Distance from right edge of screen
MARGIN_BOTTOM = 80      # Distance from bottom edge of screen

BG_COLOR = "#1a1025"           # Deep purple-black
TEXT_COLOR = "#e8d5ff"         # Soft lavender white
ACCENT_COLOR = "#9d6fff"       # Purple accent
ICON_COLOR = "#7b4fd4"

FONT_MAIN = ("SF Pro Display", 13) if platform.system() == "Darwin" else ("Segoe UI", 12)
FONT_SMALL = ("SF Pro Display", 10) if platform.system() == "Darwin" else ("Segoe UI", 9)

FADE_IN_DURATION = 0.4         # Seconds to fade in
HOLD_DURATION = 8.0            # Seconds whisper stays visible
FADE_OUT_DURATION = 0.6        # Seconds to fade out


class WhisperOverlay:
    def __init__(self, whisper_queue: queue.Queue):
        self.whisper_queue = whisper_queue
        self.root = None
        self.label = None
        self.is_running = False
        self._fade_job = None
        self._hide_job = None

    def start(self):
        """Launch the overlay window (runs on main thread — call this last)."""
        self._build_window()
        self.is_running = True
        self._poll_queue()
        self.root.mainloop()

    def stop(self):
        self.is_running = False
        if self.root:
            self.root.quit()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _build_window(self):
        self.root = tk.Tk()
        self.root.title("WhisperCoach")
        self.root.overrideredirect(True)        # No title bar
        self.root.attributes("-topmost", True)  # Always on top
        self.root.attributes("-alpha", 0.0)     # Start invisible

        # Transparent background trick
        if platform.system() == "Darwin":
            self.root.attributes("-transparent", True)
            self.root.config(bg="systemTransparent")
        elif platform.system() == "Windows":
            self.root.attributes("-transparentcolor", "#000001")
            self.root.config(bg="#000001")
        else:
            self.root.config(bg=BG_COLOR)

        # Position: bottom-right corner
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = sw - WINDOW_WIDTH - MARGIN_RIGHT
        y = sh - WINDOW_HEIGHT - MARGIN_BOTTOM
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        """Build the inner card with icon + whisper text."""
        # Outer frame — the visible card
        self.card = tk.Frame(
            self.root,
            bg=BG_COLOR,
            padx=16,
            pady=12,
        )
        self.card.pack(fill="both", expand=True)

        # Top row: icon dot + "whispercoach" label
        header = tk.Frame(self.card, bg=BG_COLOR)
        header.pack(fill="x", anchor="w")

        self.dot = tk.Canvas(header, width=8, height=8, bg=BG_COLOR, highlightthickness=0)
        self.dot.create_oval(1, 1, 7, 7, fill=ACCENT_COLOR, outline="")
        self.dot.pack(side="left", padx=(0, 6), pady=2)

        tk.Label(
            header,
            text="whispercoach",
            font=FONT_SMALL,
            fg=ICON_COLOR,
            bg=BG_COLOR,
        ).pack(side="left")

        # Whisper text
        self.label = tk.Label(
            self.card,
            text="",
            font=FONT_MAIN,
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            wraplength=WINDOW_WIDTH - 40,
            justify="left",
            anchor="w",
        )
        self.label.pack(fill="x", anchor="w", pady=(4, 0))

        # Click to dismiss
        self.root.bind("<Button-1>", lambda e: self._hide_now())
        self.card.bind("<Button-1>", lambda e: self._hide_now())
        self.label.bind("<Button-1>", lambda e: self._hide_now())

    # ── Whisper display ───────────────────────────────────────────────────────

    def _poll_queue(self):
        """Check for new whispers every 200ms."""
        try:
            whisper = self.whisper_queue.get_nowait()
            self._show_whisper(whisper)
        except queue.Empty:
            pass

        if self.is_running:
            self.root.after(200, self._poll_queue)

    def _show_whisper(self, text: str):
        """Display a new whisper — cancel any existing fade."""
        # Cancel pending hide/fade jobs
        if self._hide_job:
            self.root.after_cancel(self._hide_job)
        if self._fade_job:
            self.root.after_cancel(self._fade_job)

        self.label.config(text=text)
        self._pulse_dot()
        self._fade_in(0.0)

    def _pulse_dot(self):
        """Flash the accent dot briefly to signal a new whisper."""
        self.dot.itemconfig(1, fill="#ffffff")
        self.root.after(300, lambda: self.dot.itemconfig(1, fill=ACCENT_COLOR))

    def _fade_in(self, alpha: float):
        alpha = min(alpha + 0.08, 0.93)
        self.root.attributes("-alpha", alpha)
        if alpha < 0.93:
            self._fade_job = self.root.after(
                int(FADE_IN_DURATION * 1000 / 12),
                lambda: self._fade_in(alpha)
            )
        else:
            # Fully visible — schedule fade out
            self._hide_job = self.root.after(
                int(HOLD_DURATION * 1000),
                self._fade_out_start
            )

    def _fade_out_start(self):
        self._fade_out(0.93)

    def _fade_out(self, alpha: float):
        alpha = max(alpha - 0.06, 0.0)
        self.root.attributes("-alpha", alpha)
        if alpha > 0.0:
            self._fade_job = self.root.after(
                int(FADE_OUT_DURATION * 1000 / 16),
                lambda: self._fade_out(alpha)
            )

    def _hide_now(self):
        """Immediately dismiss on click."""
        if self._hide_job:
            self.root.after_cancel(self._hide_job)
        if self._fade_job:
            self.root.after_cancel(self._fade_job)
        self.root.attributes("-alpha", 0.0)
