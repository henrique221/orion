---
name: orion-architecture
description: Use when needing to understand Orion's system architecture, data flow between components, startup sequence, module relationships, or file structure - before modifying core orchestration or adding new components
---

# Orion Architecture

## Quick Reference

Read `knowledge/architecture.md` for:
- High-level data flow diagram (mic → detectors → STT → LLM → executor → TTS → speakers)
- Component dependency map (what depends on what)
- Complete file structure with purposes
- Startup flow (start.sh → main.py → VoiceAssistant)
- Main conversation loop lifecycle
- Key design patterns (thread safety, fallback chains, GPU management)

## Core Loop Summary

1. **Wait** — ClapDetector (44.1kHz) + WakeWordDetector (16kHz) run in background
2. **Activate** — `_on_activate()` with thread lock
3. **Listen** — SpeechRecognizer records + Whisper transcribes
4. **Interpret** — CommandInterpreter sends to Ollama, gets JSON commands
5. **Execute** — CommandExecutor runs `_do_{action}()` methods
6. **Speak** — TTS speaks reply with interrupt monitoring
7. **Deactivate** — Resume listeners

## Key Files

| File | Role |
|------|------|
| `voice_assistant.py` | Main orchestrator |
| `command_interpreter.py` | LLM command parsing |
| `command_executor.py` | 30+ system commands |
| `commands.py` | Command registry + config |
| `speech_recognizer.py` | Whisper STT pipeline |
| `tts.py` | Multi-backend TTS |
| `wake_word_detector.py` | "Orion" keyword detection |
| `clap_detector.py` | Double-clap activation |

## Related Knowledge

- `knowledge/components.md` — detailed per-component reference
- `knowledge/dependencies.md` — all deps and models
- `knowledge/configuration.md` — tunable parameters
