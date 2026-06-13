"""
transcriber.py
Transcribes audio chunks using OpenAI Whisper running locally.
No audio ever leaves your machine. Fast on CPU for short chunks.
"""

import queue
import threading
import os
import whisper
import torch


# Model sizes: tiny (fastest), base, small, medium, large (most accurate)
# For real-time coaching, "base" or "small" hits the sweet spot
DEFAULT_MODEL = "base"


class Transcriber:
    def __init__(self, audio_queue: queue.Queue, transcript_queue: queue.Queue, model_name: str = DEFAULT_MODEL):
        self.audio_queue = audio_queue
        self.transcript_queue = transcript_queue
        self.model_name = model_name
        self.model = None
        self.is_running = False
        self.thread = None

    def load_model(self):
        """Load Whisper model into memory. Call once before start()."""
        print(f"[Transcriber] Loading Whisper '{self.model_name}' model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model(self.model_name, device=device)
        print(f"[Transcriber] Model loaded on {device}")

    def start(self):
        """Start transcription worker thread."""
        if self.model is None:
            self.load_model()
        self.is_running = True
        self.thread = threading.Thread(target=self._transcribe_loop, daemon=True)
        self.thread.start()
        print("[Transcriber] Listening for audio chunks...")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[Transcriber] Stopped")

    def _transcribe_loop(self):
        """Pull WAV files from audio queue, transcribe, push text to transcript queue."""
        while self.is_running:
            try:
                wav_path = self.audio_queue.get(timeout=1)
                text = self._transcribe(wav_path)
                os.unlink(wav_path)  # Clean up temp file immediately

                if text.strip():
                    print(f"[Transcript] {text.strip()}")
                    self.transcript_queue.put(text.strip())

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Transcriber] Error: {e}")

    def _transcribe(self, wav_path: str) -> str:
        """Run Whisper on a WAV file and return the transcript."""
        result = self.model.transcribe(
            wav_path,
            language="en",          # Force English — change for multilingual support
            fp16=False,             # CPU-safe
            condition_on_previous_text=False,  # Each chunk is independent
        )
        return result.get("text", "")
