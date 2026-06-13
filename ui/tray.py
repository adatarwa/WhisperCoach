"""
tray.py
System tray icon for WhisperCoach.
Runs quietly in your menu bar. Right-click to control everything.
No terminal needed once installed.

Requires: pip install pystray pillow
"""

import pystray
from PIL import Image, ImageDraw
import threading
import queue
import os
import platform
from pathlib import Path


# Coaching modes — each swaps in a different system prompt
MODES = {
    "General":          "prompts/coach_system.txt",
    "Sales call":       "prompts/coach_sales.txt",
    "Job interview":    "prompts/coach_interview.txt",
    "Investor pitch":   "prompts/coach_pitch.txt",
    "Difficult convo":  "prompts/coach_difficult.txt",
}


class TrayApp:
    def __init__(self, start_cb, stop_cb, mode_cb):
        """
        start_cb  — called when user clicks Start
        stop_cb   — called when user clicks Stop
        mode_cb   — called with mode name when user switches mode
        """
        self.start_cb = start_cb
        self.stop_cb = stop_cb
        self.mode_cb = mode_cb

        self.is_active = False
        self.current_mode = "General"
        self.whisper_count = 0
        self.icon = None

    # ── Icon drawing ──────────────────────────────────────────────────────────

    def _make_icon(self, active: bool) -> Image.Image:
        """Draw a simple mic icon. Purple when active, gray when idle."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        color = (157, 111, 255, 255) if active else (120, 120, 120, 200)  # purple or gray

        # Mic body
        draw.rounded_rectangle([22, 8, 42, 38], radius=10, fill=color)

        # Mic stand arc
        draw.arc([14, 24, 50, 52], start=0, end=180, fill=color, width=3)

        # Mic stand pole
        draw.line([32, 52, 32, 58], fill=color, width=3)

        # Base
        draw.line([24, 58, 40, 58], fill=color, width=3)

        # Active pulse dot
        if active:
            draw.ellipse([44, 8, 56, 20], fill=(80, 255, 160, 255))

        return img

    # ── Menu building ─────────────────────────────────────────────────────────

    def _build_menu(self) -> pystray.Menu:
        status_label = f"● Active — {self.whisper_count} whispers" if self.is_active else "○ Idle"

        mode_items = [
            pystray.MenuItem(
                mode,
                self._make_mode_handler(mode),
                checked=lambda item, m=mode: self.current_mode == m,
                radio=True,
            )
            for mode in MODES
        ]

        return pystray.Menu(
            pystray.MenuItem(status_label, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Stop listening" if self.is_active else "Start listening",
                self._toggle
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Mode", pystray.Menu(*mode_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open sessions folder", self._open_sessions),
            pystray.MenuItem("Quit", self._quit),
        )

    def _make_mode_handler(self, mode: str):
        def handler(icon, item):
            self.current_mode = mode
            self.mode_cb(mode)
            self._refresh()
        return handler

    # ── Actions ───────────────────────────────────────────────────────────────

    def _toggle(self, icon=None, item=None):
        if self.is_active:
            self.is_active = False
            self.stop_cb()
        else:
            self.is_active = True
            self.whisper_count = 0
            self.start_cb()
        self._refresh()

    def _open_sessions(self, icon=None, item=None):
        sessions_dir = Path.home() / "WhisperCoach" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        if platform.system() == "Darwin":
            os.system(f"open '{sessions_dir}'")
        elif platform.system() == "Windows":
            os.startfile(str(sessions_dir))
        else:
            os.system(f"xdg-open '{sessions_dir}'")

    def _quit(self, icon=None, item=None):
        if self.is_active:
            self.stop_cb()
        self.icon.stop()

    def _refresh(self):
        """Redraw icon and menu to reflect current state."""
        if self.icon:
            self.icon.icon = self._make_icon(self.is_active)
            self.icon.menu = self._build_menu()

    def increment_whisper(self):
        """Call this from main.py each time a whisper is shown."""
        self.whisper_count += 1
        self._refresh()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def run(self):
        """Start the tray icon — blocks until quit."""
        self.icon = pystray.Icon(
            name="WhisperCoach",
            icon=self._make_icon(False),
            title="WhisperCoach",
            menu=self._build_menu(),
        )
        self.icon.run()
