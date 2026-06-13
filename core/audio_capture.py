"""
audio_capture.py
Captures microphone audio in real-time chunks for transcription.
Runs in a background thread, pushes audio chunks to a queue.
"""

import pyaudio
import wave
import threading
import queue
import tempfile
import os
import time


CHUNK_DURATION_SECONDS = 5      # How often we send audio to transcriber
SAMPLE_RATE = 16000             # Whisper works best at 16kHz
CHANNELS = 1                    # Mono
FORMAT = pyaudio.paInt16        # 16-bit audio
CHUNK_SIZE = 1024               # Frames per buffer read


class AudioCapture:
    def __init__(self, audio_queue: queue.Queue):
        self.audio_queue = audio_queue
        self.is_running = False
        self.thread = None
        self.pa = pyaudio.PyAudio()

    def list_devices(self):
        """Print all available audio input devices."""
        print("\nAvailable audio input devices:")
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                print(f"  [{i}] {info['name']}")
        print()

    def start(self, device_index=None):
        """Start capturing audio in background thread."""
        self.is_running = True
        self.thread = threading.Thread(
            target=self._capture_loop,
            args=(device_index,),
            daemon=True
        )
        self.thread.start()
        print(f"[AudioCapture] Started — capturing every {CHUNK_DURATION_SECONDS}s")

    def stop(self):
        """Stop capturing."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=3)
        self.pa.terminate()
        print("[AudioCapture] Stopped")

    def _capture_loop(self, device_index):
        """Main capture loop — records chunks and puts temp WAV files on queue."""
        stream = self.pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK_SIZE,
        )

        frames_per_chunk = SAMPLE_RATE * CHUNK_DURATION_SECONDS

        while self.is_running:
            frames = []
            for _ in range(0, int(frames_per_chunk / CHUNK_SIZE)):
                if not self.is_running:
                    break
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                frames.append(data)

            if frames:
                wav_path = self._save_temp_wav(frames)
                self.audio_queue.put(wav_path)

        stream.stop_stream()
        stream.close()

    def _save_temp_wav(self, frames):
        """Save audio frames to a temp WAV file, return path."""
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.pa.get_sample_size(FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(frames))
        return tmp.name
