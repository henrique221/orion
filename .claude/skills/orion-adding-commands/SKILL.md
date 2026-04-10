---
name: orion-adding-commands
description: Use when adding new voice commands, modifying existing command behavior, or working with the command interpretation/execution pipeline - covers the full path from voice input to system action
---

# Adding Commands to Orion

## Quick Steps

1. **`orion/commands.py`** — Add action to `COMMANDS` dict
2. **`orion/command_executor.py`** — Add `_do_{action_name}(self, target, args)` method
3. **`install.sh`** — Update if new dependencies added (CLAUDE.md requirement)

The LLM system prompt auto-generates from `COMMANDS`, so no prompt editing needed.

## Command Structure

```python
# In commands.py COMMANDS dict:
"action_name": {
    "description": "What it does (used in LLM system prompt)",
    "notes": "Extra context for the LLM (optional)",
    "solo": True,  # Cannot combine with other commands (optional)
}
```

## Executor Method

```python
# In command_executor.py:
def _do_action_name(self, target: str, args: str) -> str:
    """target and args come from LLM JSON response."""
    # Do the thing
    return "Response text for TTS to speak"
```

## LLM Response Format

The LLM returns:
```json
{
  "commands": [{
    "action": "action_name",
    "target": "optional",
    "args": "optional",
    "reply": "Portuguese TTS response"
  }]
}
```

## Important Rules

- **Solo actions** (weather, analyze_screen, etc.) can't mix with other commands
- **Validation** in `command_interpreter.py` checks all actions exist in `COMMANDS`
- **Bad responses** are not saved to conversation history (prevents poisoning)
- Actions requiring confirmation (like shutdown) handle it in the executor method

## Full Reference

- `knowledge/commands-reference.md` — all 30+ commands with parameters
- `knowledge/components.md` — CommandInterpreter and CommandExecutor details
- `knowledge/dependencies.md` — dependency management rules
