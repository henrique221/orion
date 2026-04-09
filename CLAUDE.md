# Orion - Development Guidelines

## Dependencies

Whenever you add, remove, or change a dependency — whether it's a Python package (`requirements.txt`), a system package (apt), or an Ollama model — you MUST also update `install.sh` to reflect that change. This includes:

- Adding/removing apt packages in the `apt-get install` block
- Adding/removing `ollama pull` commands
- Updating the verification checklist at the bottom of `install.sh`
