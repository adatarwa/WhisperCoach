"""
coach.py
The brain of WhisperCoach.
Maintains a rolling transcript window, calls the Claude API,
and produces short real-time coaching whispers.
"""

import queue
import threading
import time
import os
import anthropic
from pathlib import Path
from collections import deque


# Rolling window of transcript lines sent to Claude each time
TRANSCRIPT_WINDOW = 20

# Minimum seconds between coaching whispers (avoid spam)
MIN_WHISPER_INTERVAL = 12

# Max words in a whisper — keep it tight, it's a coaching cue not an essay
MAX_WHISPER_WORDS = 20


class Coach:
    def __init__(self, transcript_queue: queue.Queue, whisper_queue: queue.Queue):
        self.transcript_queue = transcript_queue
        self.whisper_queue = whisper_queue

        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.system_prompt = self._load_system_prompt()

        self.transcript_buffer = deque(maxlen=TRANSCRIPT_WINDOW)
        self.last_whisper_time = 0
        self.is_running = False
        self.thread = None

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._coach_loop, daemon=True)
        self.thread.start()
        print("[Coach] Active — watching the conversation...")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[Coach] Stopped")

    def _coach_loop(self):
        """Drain transcript queue, accumulate context, trigger coaching when ready."""
        while self.is_running:
            # Pull all available transcripts into buffer
            drained = False
            while True:
                try:
                    line = self.transcript_queue.get_nowait()
                    self.transcript_buffer.append(line)
                    drained = True
                except queue.Empty:
                    break

            # Only fire if we have new content and enough time has passed
            now = time.time()
            if drained and (now - self.last_whisper_time) >= MIN_WHISPER_INTERVAL:
                whisper = self._get_whisper()
                if whisper:
                    self.whisper_queue.put(whisper)
                    self.last_whisper_time = now

            time.sleep(1)

    def _get_whisper(self) -> str | None:
        """Send transcript context to Claude, get a coaching whisper back."""
        if not self.transcript_buffer:
            return None

        transcript_text = "\n".join(self.transcript_buffer)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=80,      # Short responses only — whispers not essays
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"<transcript>\n{transcript_text}\n</transcript>"
                    }
                ]
            )

            whisper = response.content[0].text.strip()

            # Enforce word limit — truncate if Claude gets chatty
            words = whisper.split()
            if len(words) > MAX_WHISPER_WORDS:
                whisper = " ".join(words[:MAX_WHISPER_WORDS]) + "..."

            # Claude returns PASS when no coaching is needed
            if whisper.upper().startswith("PASS"):
                return None

            return whisper

        except Exception as e:
            print(f"[Coach] API error: {e}")
            return None

    def _load_system_prompt(self) -> str:
        """Load the coaching system prompt from file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "coach_system.txt"
        if prompt_path.exists():
            return prompt_path.read_text()
        return DEFAULT_SYSTEM_PROMPT


# Fallback if file not found
DEFAULT_SYSTEM_PROMPT = """You are WhisperCoach — a silent real-time conversation coach.
You watch live transcripts and whisper short, sharp coaching cues to the speaker.
Keep whispers under 20 words. Be direct. No fluff. One cue at a time.
If nothing needs coaching right now, respond with exactly: PASS"""
