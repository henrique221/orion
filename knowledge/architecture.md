# Orion - System Architecture

## Overview

Orion is a 100% offline, local Brazilian Portuguese voice assistant for Ubuntu (JARVIS-style). It combines wake word detection, speech-to-text, LLM command interpretation, system command execution, and text-to-speech in a continuous loop.

## High-Level Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                   AUDIO INPUT (Microphone)                    │
└──────────┬───────────────────────────────────────────────────┘
           │
    ┌──────┴──────────┐
    │                 │
    ▼                 ▼
┌──────────────┐  ┌──────────────────┐
│ ClapDetector │  │ WakeWordDetector │
│  (44.1kHz)   │  │     (16kHz)      │
│ RMS Energy   │  │ VAD + Whisper    │
│ Double-tap   │  │ Regex match      │
└──────┬───────┘  └──────┬───────────┘
       │                 │
       └────────┬────────┘
                │ Activation trigger
                ▼
      ┌──────────────────────┐
      │   VoiceAssistant     │
      │   _on_activate()     │
      │  (thread-safe lock)  │
      └──────┬───────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │  SpeechRecognizer          │
    │  • Record audio (16kHz)    │
    │  • VAD-based auto-stop     │
    │  • Bandpass + noise reduce │
    │  • Whisper STT (CUDA)      │
    │  → transcribed text        │
    └────────┬───────────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ CommandInterpreter (LLM)   │
    │  • Conversation history    │
    │  • System prompt + schema  │
    │  • Ollama qwen2.5:1.5b    │
    │  • JSON response parsing   │
    │  → [{action, target, args, reply}]
    └────────┬───────────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │   CommandExecutor          │
    │  _do_{action}(target,args) │
    │  • 30+ system commands     │
    │  • subprocess / API calls  │
    │  → reply text              │
    └────────┬───────────────────┘
             │
             ▼
      ┌────────────────┐
      │   TTS Module   │
      │ XTTS v2 (GPU)  │
      │ → Kokoro (CPU) │
      │ → Piper        │
      │ → espeak-ng    │
      │ + interrupt    │
      └────────┬───────┘
             │
             ▼
    ┌────────────────────┐
    │  Audio Output      │
    │  (speakers)        │
    └────────────────────┘
```

## Component Dependency Map

| Component | Depends On | Used By |
|-----------|-----------|---------|
| VoiceAssistant | All components | main.py |
| ClapDetector | sounddevice, numpy | VoiceAssistant |
| WakeWordDetector | sounddevice, Whisper, VAD, audio_utils | VoiceAssistant |
| SpeechRecognizer | sounddevice, faster_whisper, VAD, audio_utils | VoiceAssistant |
| CommandInterpreter | requests, torch, commands | VoiceAssistant |
| CommandExecutor | subprocess, requests, TTS | VoiceAssistant |
| TTS | torch, sounddevice, coqui-tts | VoiceAssistant, CommandExecutor |
| VAD | torch (Silero model via torch.hub) | WakeWordDetector, SpeechRecognizer |
| audio_utils | scipy, noisereduce, numpy | SpeechRecognizer, WakeWordDetector |
| FaceAnimator | threading, sys, math | VoiceAssistant |

## File Structure

```
orion/
├── main.py                     # Entry point: banner, signal handling, starts VoiceAssistant
├── requirements.txt            # Python dependencies
├── install.sh                  # Complete system installation (6 stages)
├── start.sh                    # Launcher: CUDA setup, venv, ollama check
├── stop.sh                     # Kill running instance
├── calibrate.py                # Clap detection threshold calibration
├── CLAUDE.md                   # Dev guidelines
├── README.md                   # Portuguese documentation
├── assets/
│   ├── demo.mp3               # Demo mode background music
│   └── voice_ref.wav          # XTTS voice reference sample
└── orion/                     # Python package
    ├── __init__.py
    ├── voice_assistant.py      # Main orchestrator
    ├── clap_detector.py        # Dual-clap activation
    ├── wake_word_detector.py   # "Orion" keyword detection
    ├── speech_recognizer.py    # Audio recording + Whisper STT
    ├── command_interpreter.py  # LLM-based command parsing
    ├── command_executor.py     # System command handlers
    ├── commands.py             # Command registry & config
    ├── tts.py                  # Multi-backend TTS
    ├── vad.py                  # Silero VAD wrapper
    ├── audio_utils.py          # Bandpass filter + noise reduction
    └── face.py                 # Terminal ASCII face animator
```

## Startup Flow

```
./start.sh
├── Check/start ollama serve
├── Activate .venv
├── Export CUDA lib paths (LD_LIBRARY_PATH)
└── python main.py
    ├── Print ORION ASCII banner
    ├── VoiceAssistant.__init__()
    │   ├── Face (terminal animator)
    │   ├── TTS (load XTTS → Kokoro → Piper → espeak)
    │   ├── SpeechRecognizer (Whisper large-v3, VAD, noise calibration)
    │   ├── CommandInterpreter (Ollama connection, memory, learnings)
    │   ├── CommandExecutor (command handlers)
    │   ├── ClapDetector (RMS energy listener)
    │   └── WakeWordDetector (VAD + Whisper listener)
    ├── Signal handlers (SIGINT, SIGTERM)
    └── assistant.start()
        ├── Face.setup() → clear screen, start animation thread
        ├── Time-based greeting (bom dia/boa tarde/boa noite)
        ├── TTS speak greeting
        └── _start_listeners()
            ├── detector.start() → 44.1kHz audio stream
            └── wake_word.start() → 16kHz audio stream
```

## Main Loop (Conversation Cycle)

1. **Waiting**: ClapDetector + WakeWordDetector run in background threads
2. **Activation**: Either trigger calls `_on_activate()` (thread-safe lock)
3. **Listening**: Stop detectors, set face to LISTENING, play beep
4. **Conversation loop**:
   - `SpeechRecognizer.record_and_transcribe()` → text
   - Check stop words: "para", "pare", "parar", "chega", "dispensado"
   - `CommandInterpreter.interpret(text)` → JSON commands
   - For each command: `CommandExecutor._do_{action}()` → reply
   - `TTS.speak(reply)` with interrupt monitoring
   - Repeat until timeout/stop/no commands
5. **Deactivation**: Face → IDLE, beep, resume listeners

## Key Design Patterns

- **Thread Safety**: Lock in `_on_activate()` prevents concurrent conversations
- **Fallback Chains**: TTS (XTTS→Kokoro→Piper→espeak), Weather (wttr.in→DuckDuckGo)
- **Offline-First**: All ML models local. Network only for weather/news/web search
- **GPU Management**: Dynamic VRAM swap between XTTS and vision model (moondream)
- **Self-Learning**: Extract patterns from conversations, remember user preferences
- **Error Isolation**: Try/except in all external calls, bad LLM responses not saved
