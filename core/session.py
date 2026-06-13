"""
session.py
Records the full session: every transcript line, every whisper,
timestamps. After the call ends, generates a debrief using Claude.
Saves to ~/WhisperCoach/sessions/ as a readable markdown file.
"""

import os
import queue
import threading
import time
import json
import anthropic
from datetime import datetime
from pathlib import Path


SESSIONS_DIR = Path.home() / "WhisperCoach" / "sessions"


DEBRIEF_PROMPT = """You are WhisperCoach reviewing a completed conversation session.

You will receive:
- A full transcript of the conversation
- Every coaching whisper that was shown to the speaker during the call

Generate a post-call debrief with exactly these sections:

## What went well
2-3 specific things the speaker did right in this conversation.

## What to work on
2-3 specific, actionable coaching points for next time. Be honest. No fluff.

## Patterns noticed
Any recurring habits (filler words, pace issues, missed signals) across the session.

## The one thing to remember for next time
One sentence. The single most important takeaway from this call.

Keep the whole debrief under 250 words. Be a good coach: direct, specific, constructive.
"""


class Session:
    def __init__(self, transcript_queue: queue.Queue, whisper_queue_ref: queue.Queue):
        self.transcript_queue = transcript_queue
        self.whisper_queue_ref = whisper_queue_ref  # Reference to observe, not consume

        self.transcript_lines = []
        self.whispers_shown = []
        self.start_time = None
        self.session_name = None

        self.is_running = False
        self.thread = None
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    def start(self):
        self.start_time = datetime.now()
        self.session_name = self.start_time.strftime("session_%Y%m%d_%H%M%S")
        self.is_running = True
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        print(f"[Session] Recording started — {self.session_name}")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=3)
        print("[Session] Generating debrief...")
        self._save_and_debrief()

    def log_whisper(self, whisper: str):
        """Call this from main.py whenever a whisper is displayed."""
        self.whispers_shown.append({
            "time": self._elapsed(),
            "text": whisper,
        })

    # ── Internal ──────────────────────────────────────────────────────────────

    def _elapsed(self) -> str:
        if not self.start_time:
            return "0:00"
        delta = int((datetime.now() - self.start_time).total_seconds())
        return f"{delta // 60}:{delta % 60:02d}"

    def _record_loop(self):
        """Observe transcript queue and mirror lines into session log."""
        while self.is_running:
            # We peek at the transcript — we use a side-tap pattern via
            # a shared list that coach.py also writes to.
            # For simplicity here, session reads from a mirrored list
            # that main.py populates. See integration notes in main.py.
            time.sleep(0.5)

    def _save_and_debrief(self):
        """Save raw session data and generate AI debrief."""
        duration = self._elapsed()

        # Build readable transcript
        transcript_text = "\n".join(self.transcript_lines) if self.transcript_lines else "(no transcript recorded)"
        whispers_text = "\n".join(
            [f"[{w['time']}] {w['text']}" for w in self.whispers_shown]
        ) if self.whispers_shown else "(no whispers triggered)"

        # Generate debrief via Claude
        debrief = self._generate_debrief(transcript_text, whispers_text)

        # Write markdown file
        output_path = SESSIONS_DIR / f"{self.session_name}.md"
        content = f"""# WhisperCoach Session Debrief
**Date:** {self.start_time.strftime('%B %d, %Y at %I:%M %p')}
**Duration:** {duration}
**Whispers shown:** {len(self.whispers_shown)}

---

{debrief}

---

## Raw session log

### Transcript
```
{transcript_text}
```

### Whispers shown
```
{whispers_text}
```
"""
        output_path.write_text(content)
        print(f"\n[Session] Debrief saved → {output_path}")
        print(f"\n{'─' * 50}")
        print(debrief)
        print(f"{'─' * 50}\n")

    def _generate_debrief(self, transcript: str, whispers: str) -> str:
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                system=DEBRIEF_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"<transcript>\n{transcript}\n</transcript>\n\n<whispers_shown>\n{whispers}\n</whispers_shown>"
                    }
                ]
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"(Debrief generation failed: {e})"
