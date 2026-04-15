# English Language Support — Design Spec

## Goal

Add English as a second language for Orion. Language is selected via the web Settings page and takes effect on next restart. All user-facing output (TTS, spoken replies) and terminal logs switch to the selected language. The JARVIS personality (formal British butler, dry wit, "Sir") is preserved in English.

## Config System

A `config.yaml` at the project root stores persistent settings:

```yaml
language: pt_BR
```

- Read once at startup by `main.py`
- Written by the web Settings page via Flask
- If missing, defaults to `pt_BR` (current behavior preserved)
- New module `orion/config.py`:
  - `load_config()` — reads YAML, returns dict with defaults
  - `save_config(data)` — writes YAML
  - `get_language()` — shortcut
- Dependency: `pyyaml` added to `requirements.txt`

## Locale Module Structure

```
orion/locales/
├── __init__.py    # get_strings(lang) loader
├── pt_BR.py       # All Portuguese strings
└── en.py          # All English strings
```

Each locale file exports a `STRINGS` dict with these keys:

| Key | Content |
|-----|---------|
| `system_prompt` | Full LLM system prompt (JARVIS personality + command instructions) |
| `listening_phrases` | List of activation responses (10+ variations) |
| `greetings` | Dict with `morning`, `afternoon`, `evening` lists (3 each) |
| `stop_words` | Tuple of conversation-end words |
| `commands` | Full command registry: descriptions, examples, reply templates |
| `app_map` | App name aliases (language-specific aliases like "calculator" / "calculadora") |
| `monitors` | Monitor position aliases ("left"/"esquerda", etc.) |
| `weekdays` | Day name to index mapping |
| `transcription_fixes` | Whisper misheard-word corrections |
| `tts` | Language params: `whisper`, `xtts`, `kokoro`, `espeak`, `piper_model` |
| `terminal` | All terminal/log messages (loading, errors, status) |
| `executor` | Executor strings: weather/news prompts, error messages, LLM instruction prompts |

Loader in `__init__.py`:

```python
def get_strings(language="pt_BR"):
    if language == "en":
        from orion.locales import en
        return en.STRINGS
    from orion.locales import pt_BR
    return pt_BR.STRINGS
```

## Component Integration

Each component receives locale strings through constructor params. No component reads `config.yaml` directly except `main.py`. Data flows down:

```
main.py
  └── load_config() → language
  └── get_strings(language) → strings
  └── VoiceAssistant(strings, language)
        ├── CommandInterpreter(strings)
        ├── CommandExecutor(strings)
        ├── SpeechRecognizer(strings, language)
        ├── TTS(strings)
        ├── WakeWordDetector(language)
        └── ClapDetector (no language dependency)
```

### Per-component changes

**main.py** — Loads config, calls `get_strings()`, passes to `VoiceAssistant`.

**VoiceAssistant** — Constructor accepts `strings`. Uses `strings["listening_phrases"]`, `strings["greetings"]`, `strings["stop_words"]`. Passes strings/language to sub-components.

**CommandInterpreter** — Constructor accepts `strings`. Uses `strings["system_prompt"]` instead of hardcoded `SYSTEM_PROMPT`. Learning extraction prompt language-switches. All terminal messages from `strings["terminal"]`.

**CommandExecutor** — Constructor accepts `strings`. All inline messages, LLM prompts (weather summary, news summary, screen analysis, translation), weather/news URLs from `strings["executor"]`.

**commands.py** — Functions `build_prompt_mappings()`, `build_prompt_notes()`, `build_json_schema()`, and `get_action_enum()` accept a `strings` param. Command registry (descriptions, examples, replies) lives in the locale files. `commands.py` retains only language-agnostic logic and the JSON schema builder.

**SpeechRecognizer** — Constructor accepts language. Sets Whisper `language` param (`"en"` / `"pt"`). Swaps `initial_prompt` and `transcription_fixes` from locale.

**TTS** — Constructor accepts strings. Reads `strings["tts"]` for XTTS language, Kokoro language, espeak voice, Piper model path. All terminal messages from `strings["terminal"]`.

**WakeWordDetector** — Constructor accepts language. Whisper language param switches. Wake word stays "Orion" for both languages (same word).

## English Piper Voice

`install.sh` downloads a second Piper voice:

- Model: `en_US-lessac-medium` (~60MB, high quality US English)
- Location: `~/.local/share/piper/en_US-lessac-medium.onnx` + `.onnx.json`
- Source: HuggingFace `rhasspy/piper-voices`
- Verification checklist updated to check both voice models

The locale's `tts.piper_model` key points to the correct file per language.

## Web Settings Page

The Settings page adds a language dropdown:

- Options: `Portugues (BR)` / `English`
- On save: writes `language` to `config.yaml` via new API endpoint
- Shows note: "Restart Orion to apply language change."
- New Flask routes:
  - `GET /api/settings` — returns current config
  - `PUT /api/settings` — updates config.yaml

## Migration Path

- `pt_BR.py` is created by extracting all current hardcoded Portuguese strings — zero behavior change for existing users
- `en.py` is the new English equivalent
- Default language remains `pt_BR` when no config file exists
- All current tests/functionality preserved

## Files Changed

| File | Change |
|------|--------|
| `orion/config.py` | New — config load/save |
| `orion/locales/__init__.py` | New — locale loader |
| `orion/locales/pt_BR.py` | New — all Portuguese strings extracted from codebase |
| `orion/locales/en.py` | New — English translations |
| `orion/main.py` | Load config, pass language/strings |
| `orion/voice_assistant.py` | Accept strings, replace hardcoded Portuguese |
| `orion/command_interpreter.py` | Accept strings, parameterize system prompt |
| `orion/command_executor.py` | Accept strings, parameterize all messages/prompts |
| `orion/commands.py` | Functions accept strings param, remove hardcoded registry |
| `orion/speech_recognizer.py` | Accept language, parameterize Whisper config |
| `orion/tts.py` | Accept strings, parameterize all TTS backends |
| `orion/wake_word_detector.py` | Accept language for Whisper |
| `orion/web/app.py` | Add settings API endpoints |
| `orion/web/templates/settings.html` | Add language dropdown |
| `config.yaml` | New — persistent settings |
| `requirements.txt` | Add pyyaml |
| `install.sh` | Add English Piper voice download, add pyyaml |
| `knowledge/*.md` | Update docs to reflect i18n |
