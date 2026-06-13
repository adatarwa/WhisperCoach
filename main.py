"""
main.py
WhisperCoach — entry point.
Wires together: audio → transcribe → coach → overlay + session debrief.

Run: python main.py
"""

import queue
import time
import os
import sys
import signal
import threading
from dotenv import load_dotenv

load_dotenv()

from core.audio_capture import AudioCapture
from core.transcriber import Transcriber
from core.coach import Coach
from core.session import Session
from ui.overlay import WhisperOverlay


def main():
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠  ANTHROPIC_API_KEY not set.")
        print("Copy .env.example to .env and add your key.\n")
        sys.exit(1)

    # Shared queues
    audio_queue = queue.Queue()
    transcript_queue = queue.Queue()
    whisper_queue = queue.Queue()
    # Mirrored whisper queue — session observes without consuming display queue
    session_whisper_tap = queue.Queue()

    # Components
    audio = AudioCapture(audio_queue)
    transcriber = Transcriber(audio_queue, transcript_queue)
    coach = Coach(transcript_queue, whisper_queue)
    session = Session(transcript_queue, whisper_queue)
    overlay = WhisperOverlay(whisper_queue)

    # Show devices for mic selection
    audio.list_devices()
    choice = input("Enter device number (or Enter for default mic): ").strip()
    device_index = int(choice) if choice.isdigit() else None

    print("\n[WhisperCoach] Loading transcription model...")
    transcriber.load_model()

    print("[WhisperCoach] Starting session...\n")

    # Start background threads
    audio.start(device_index=device_index)
    transcriber.start()
    coach.start()
    session.start()

    # Graceful shutdown
    def shutdown(sig, frame):
        print("\n[WhisperCoach] Ending session...")
        audio.stop()
        transcriber.stop()
        coach.stop()
        session.stop()   # Triggers debrief generation
        overlay.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    # Run overlay on main thread (required by tkinter)
    overlay.start()


if __name__ == "__main__":
    main()
