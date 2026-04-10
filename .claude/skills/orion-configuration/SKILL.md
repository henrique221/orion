---
name: orion-configuration
description: Use when tuning Orion parameters, changing thresholds, modifying app mappings, updating monitor layout, switching LLM models, or adjusting any hard-coded settings
---

# Orion Configuration

## Where Settings Live

All config is hard-coded — no external config file. Each setting is in its source file.

| Category | File |
|----------|------|
| Clap detection | `orion/clap_detector.py` |
| Wake word | `orion/wake_word_detector.py` |
| Speech recognition | `orion/speech_recognizer.py` |
| Audio cleaning | `orion/audio_utils.py` |
| LLM settings | `orion/command_interpreter.py` |
| TTS settings | `orion/tts.py` |
| App mappings | `orion/commands.py` |
| Monitor layout | `orion/commands.py` |
| Smart home | `orion/commands.py` |
| Weather location | `orion/command_executor.py` |

## Common Tuning Tasks

### Clap sensitivity
Run `python calibrate.py`, then adjust `ENERGY_THRESHOLD` in `clap_detector.py` (default: 0.25).

### Wake word sensitivity
Adjust `VAD_THRESHOLD` in `wake_word_detector.py` (default: 0.35). Lower = more sensitive.

### LLM model swap
Change `MODEL` in `command_interpreter.py` and `LLM_MODEL` in `command_executor.py`. Update `install.sh` with `ollama pull` for the new model.

### Add application mapping
Add entry to `APP_MAP` dict in `commands.py`.

### Change monitor layout
Update `MONITORS` dict in `commands.py` with (x, y, width, height) tuples.

### Change weather location
Update `WEATHER_LOCATION` in `command_executor.py`.

## Full Parameter Reference

See `knowledge/configuration.md` for the complete table of all parameters, values, and tuning notes.

## Dependency Rule

From CLAUDE.md: whenever changing a dependency (Python, apt, Ollama model), you MUST update `install.sh` to match.
