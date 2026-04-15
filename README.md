<div align="center">

```
   ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
  ██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
  ██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
  ██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
  ╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
   ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

**Local voice assistant for Ubuntu**

*100% offline. Zero external APIs. Total privacy.*

---

`faster-whisper` | `ollama` | `piper-tts` | `CUDA`

</div>

## How it works

```
  Double clap / "Hey Orion"
          │
          ▼
   ┌──────────────┐
   │  Record speech │
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   Whisper     │  faster-whisper (GPU)
   │   STT         │  pt-BR / en, ~0.1s
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   Ollama      │  qwen2.5 (1.5B)
   │   LLM         │  structured JSON
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   Executor    │  apps, volume, workspaces...
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   XTTS v2     │  voice cloning
   │   Response     │  natural voice
   └──────────────┘
```

## Requirements

| Component | Minimum | Recommended |
|:----------|:--------|:------------|
| OS | Ubuntu 22.04 | Ubuntu 24.04+ |
| Python | 3.10 | 3.12 |
| GPU | - | NVIDIA (CUDA) |
| RAM | 4 GB | 8 GB+ |

## Installation

```bash
git clone git@github.com:henrique221/orion.git
cd orion
./install.sh
```

> The script installs everything automatically: system dependencies, Python venv, Ollama + qwen2.5:1.5b, Piper TTS + voice models, XTTS v2 voice cloning.

## Usage

```bash
./start.sh    # Start Orion
./stop.sh     # Stop Orion
```

### Activation

| Method | Description |
|:-------|:------------|
| **Claps** | Double clap |
| **Voice** | Say *"Hey Orion"* |

### Commands

<details>
<summary><b>Applications</b></summary>

| Say | Action |
|:----|:-------|
| *"open Chrome"* | Opens the application |
| *"close the terminal"* | Closes the application |
| *"close everything"* | Closes all windows (preserves Orion's terminal) |

</details>

<details>
<summary><b>System</b></summary>

| Say | Action |
|:----|:-------|
| *"turn up the volume"* | Volume +10% |
| *"turn down the volume"* | Volume -10% |
| *"mute"* | Mute/unmute |
| *"take a screenshot"* | Screenshot |
| *"what time is it"* | Speaks the current time |

</details>

<details>
<summary><b>Workspaces</b></summary>

| Say | Action |
|:----|:-------|
| *"workspace 2"* | Switches workspace |
| *"start work"* | Opens full work environment (Chrome + Cursor) |

</details>

<details>
<summary><b>Smart Home</b></summary>

| Say | Action |
|:----|:-------|
| *"turn on the porch light"* | Controls smart devices via IFTTT |
| *"turn off the pool"* | Controls smart devices via IFTTT |

</details>

<details>
<summary><b>Screen & Text Analysis</b></summary>

| Say | Action |
|:----|:-------|
| *"analyse the screen"* | Describes screen content using vision model |
| *"translate the selected text"* | Translates clipboard selection |
| *"summarise what is on screen"* | Summarises visible content |

</details>

<details>
<summary><b>Weather & News</b></summary>

| Say | Action |
|:----|:-------|
| *"how is the weather?"* | Current weather report |
| *"what is the news today?"* | Latest news summary |

</details>

<details>
<summary><b>Other</b></summary>

| Say | Action |
|:----|:-------|
| *"search for Python"* | Web search with summary |
| *"open github.com"* | Opens URL in browser |
| *"set a timer for 5 minutes"* | Timer with alarm |
| General questions | Responds via LLM |

</details>

## Language

Orion supports **Portuguese (BR)** and **English**. Language is configured via the web settings page at `http://localhost:5000/settings`. Restart Orion after changing the language.

## Calibration

```bash
python calibrate.py
```

Measures ambient noise for 10 seconds and suggests the ideal threshold for clap detection. The wake word (*"Hey Orion"*) self-calibrates continuously.

## Architecture

```
orion/
├── main.py                     Entry point, ASCII art, signal handling
├── start.sh                    Starts Ollama + Orion
├── stop.sh                     Stops Orion
├── install.sh                  Full installation
├── calibrate.py                Clap calibration
├── config.yaml                 Persistent settings (language, etc.)
├── requirements.txt            Python dependencies
│
└── orion/
    ├── voice_assistant.py      Main orchestrator
    ├── clap_detector.py        Double-clap detection (Silero VAD)
    ├── wake_word_detector.py   "Hey Orion" detection (auto-calibration)
    ├── speech_recognizer.py    Recording + transcription (Whisper GPU)
    ├── command_interpreter.py  Interpretation via Ollama (JSON schema)
    ├── command_executor.py     System action execution
    ├── commands.py             Command registry + schema builder
    ├── tts.py                  Text-to-speech (XTTS v2 / Kokoro / Piper / espeak)
    ├── config.py               YAML config load/save
    ├── locales/                i18n string bundles (pt_BR, en)
    └── web/                    Flask web UI (settings, knowledge base)
```

## Stack

| Layer | Technology | Details |
|:------|:-----------|:--------|
| **STT** | faster-whisper | large-v3, CUDA, Silero VAD |
| **LLM** | Ollama + qwen2.5:1.5b | JSON schema, structured output |
| **TTS** | XTTS v2 | Voice cloning, GPU accelerated |
| **TTS fallback** | Kokoro > Piper > espeak-ng | Cascading fallback chain |
| **Audio** | sounddevice + numpy | 16kHz (STT) / 44.1kHz (clap) |
| **Wake word** | Whisper | Continuous auto-calibration |
| **Vision** | Moondream | Screen analysis, text extraction |
| **Web** | Flask | Settings, knowledge base editor |

---

<div align="center">

*Built to run locally. No cloud. No limits.*

</div>
