# Orion - Development Guidelines

## Project Knowledge

The `knowledge/` folder contains detailed project documentation:

- `architecture.md` — system architecture, data flow, startup sequence, file structure
- `components.md` — per-component reference (VoiceAssistant, STT, TTS, LLM, detectors)
- `dependencies.md` — Python packages, system packages, ML models, external services
- `configuration.md` — all hard-coded settings, thresholds, app mappings, monitor layout
- `commands-reference.md` — all 30+ voice commands with parameters and how to add new ones
- `setup-and-running.md` — installation, startup, usage examples, troubleshooting

Whenever you make changes that affect the information in `knowledge/` files or `.claude/skills/`, you MUST update them to stay in sync. This includes:

- Adding/removing/renaming components or files → update `architecture.md`, `components.md`, and `orion-architecture` skill
- Adding/modifying/removing commands → update `commands-reference.md` and `orion-adding-commands` skill
- Changing audio parameters, thresholds, or pipeline → update `configuration.md`, `components.md`, and `orion-audio-pipeline` skill
- Adding/removing dependencies or models → update `dependencies.md`
- Changing configuration values, app mappings, or monitor layout → update `configuration.md` and `orion-configuration` skill
- Changing install/startup process → update `setup-and-running.md`

## Dependencies

Whenever you add, remove, or change a dependency — whether it's a Python package (`requirements.txt`), a system package (apt), or an Ollama model — you MUST also update `install.sh` to reflect that change. This includes:

- Adding/removing apt packages in the `apt-get install` block
- Adding/removing `ollama pull` commands
- Updating the verification checklist at the bottom of `install.sh`
