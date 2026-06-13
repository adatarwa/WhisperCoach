# 🤫 WhisperCoach

**An AI coach that whispers in your ear during live conversations.**

WhisperCoach runs silently in the background while you talk. It listens, reads the room, and surfaces short coaching cues — only when you need them. Like having a world-class coach watching every call you make.

---

## What it does

While you're on a Zoom call, sales pitch, job interview, or difficult conversation, WhisperCoach:

- **Transcribes your conversation locally** using Whisper (nothing leaves your machine)
- **Reads the room in real time** — pace, tone, filler words, missed signals, buying cues
- **Whispers one short cue at a time** in a subtle floating overlay on your screen
- **Generates a post-call debrief** with specific, honest coaching after every session

---

## What it whispers

```
┌──────────────────────────────────────────────────────┐
│  🤫  You've talked for 3 minutes — ask a question.   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  🤫  They said "budget" twice. Address it directly.  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  🤫  You've said "basically" 6 times. Drop it.       │
└──────────────────────────────────────────────────────┘
```

Whispers appear for 8 seconds, then fade. Click to dismiss instantly.

---

## Modes

Switch modes from the menu bar icon before any call:

| Mode | Optimized for |
|------|---------------|
| **General** | Any conversation |
| **Sales call** | Buying signals, objections, closing moments |
| **Job interview** | Specificity, confidence, landing answers cleanly |
| **Investor pitch** | Traction, skepticism signals, making the ask |
| **Difficult convo** | Staying calm, acknowledgment, de-escalation |

---

## How it works

```
Microphone
    │
    ▼
audio_capture.py   — records 5-second audio chunks locally
    │
    ▼
transcriber.py     — Whisper runs on-device, produces transcript
    │
    ▼
coach.py           — Claude API reads rolling transcript, returns one whisper (or PASS)
    │
    ▼
overlay.py         — floating window shows the whisper on screen
    +
session.py         — records everything, generates debrief on call end
```

**Privacy first.** Audio is transcribed locally using OpenAI Whisper. Your audio never leaves your machine. Only the text transcript is sent to the Claude API for coaching.

---

## Installation

**Requirements:** Python 3.9+, macOS or Windows

```bash
# Clone
git clone https://github.com/yourusername/WhisperCoach.git
cd WhisperCoach

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Open .env and add your Anthropic API key
# Get one free at: https://console.anthropic.com
```

**First run** will download the Whisper `base` model (~140MB). This happens once.

```bash
python main.py
```

---

## Usage

1. Run `python main.py`
2. Select your microphone from the list
3. The tray icon appears in your menu bar
4. Right-click → choose your mode → **Start listening**
5. Have your conversation — whispers appear automatically
6. When done: right-click → **Stop listening**
7. Your debrief is printed and saved to `~/WhisperCoach/sessions/`

---

## Project structure

```
WhisperCoach/
├── core/
│   ├── audio_capture.py   — mic recording in 5s chunks
│   ├── transcriber.py     — local Whisper transcription
│   ├── coach.py           — Claude API coaching logic
│   └── session.py         — session recording + debrief
├── ui/
│   ├── overlay.py         — floating whisper window
│   └── tray.py            — system tray icon + mode switcher
├── prompts/
│   ├── coach_system.txt   — general coaching prompt
│   ├── coach_sales.txt    — sales mode
│   ├── coach_interview.txt
│   ├── coach_pitch.txt
│   └── coach_difficult.txt
├── main.py                — entry point
├── requirements.txt
└── .env.example
```

---

## Configuration

`.env` options:

```
ANTHROPIC_API_KEY=your_key_here
WHISPER_MODEL=base    # tiny | base | small | medium | large
```

Whisper model tradeoff:

| Model | Speed | Accuracy | Best for |
|-------|-------|----------|----------|
| `tiny` | Fastest | Lower | Old hardware |
| `base` | Fast | Good | **Recommended** |
| `small` | Medium | Better | Quiet mics |
| `medium` | Slow | High | Accents, noisy rooms |

---

## Customizing your coaching

The real power is in the prompts. Edit any file in `prompts/` to tune the coaching style.

Want WhisperCoach to focus only on filler words? Edit `coach_system.txt`.
Want a mode for client presentations? Add `prompts/coach_presentation.txt` and register it in `ui/tray.py`.

---

## Roadmap

- [ ] macOS native app (no Python install needed)
- [ ] Windows installer `.exe`
- [ ] Whisper language selection (Spanish, Hindi, Arabic...)
- [ ] Session history viewer
- [ ] Custom coaching personas
- [ ] Team mode (manager gets debrief after 1-on-1s)

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `openai-whisper` | On-device speech-to-text |
| `anthropic` | Claude API for coaching logic |
| `pyaudio` | Microphone capture |
| `pystray` | System tray icon |
| `Pillow` | Tray icon rendering |
| `python-dotenv` | Environment config |

---

## Contributing

PRs welcome. The most valuable contributions:

- New coaching modes (`prompts/`)
- Better whisper prompts with real examples
- macOS/Windows packaging
- Language support in transcriber

---

## License

MIT — use it, fork it, build on it.

---

*Built with [Claude](https://anthropic.com) + [Whisper](https://github.com/openai/whisper)*
