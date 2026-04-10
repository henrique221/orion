# Orion - Commands Reference

## Command JSON Schema

The LLM returns commands in this format:
```json
{
  "commands": [
    {
      "action": "action_name",
      "target": "optional_target",
      "args": "optional_args",
      "reply": "Portuguese response to speak"
    }
  ]
}
```

Multiple commands can be chained (e.g., "abre Chrome, aumenta volume e tira print" → 3 commands).

## All Available Actions

### Application Control

| Action | Target | Args | Description |
|--------|--------|------|-------------|
| open_app | app name (from APP_MAP) | — | Open application |
| close_app | app name | — | Close specific application |
| close_all | — | — | Close all open windows |
| start_work | — | — | Open predefined workspace apps |

### Audio Control

| Action | Target | Args | Description |
|--------|--------|------|-------------|
| volume_up | — | — | Increase volume 10% |
| volume_down | — | — | Decrease volume 10% |
| mute | — | — | Toggle mute |

### Display

| Action | Target | Args | Description |
|--------|--------|------|-------------|
| screenshot | — | — | Take screenshot (gnome-screenshot/scrot) |
| brightness_up | — | — | Increase brightness |
| brightness_down | — | — | Decrease brightness |
| analyze_screen | — | user question | Screenshot → moondream vision → LLM summary |

### System

| Action | Target | Args | Description |
|--------|--------|------|-------------|
| show_time | — | — | Speak current time |
| lock_screen | — | — | Lock desktop |
| unlock_screen | — | — | Unlock desktop |
| shutdown | — | — | **Requires confirmation** before executing |
| restart | — | — | Restart system |
| suspend | — | — | Suspend/sleep |
| logout | — | — | Log out of session |
| empty_trash | — | — | Empty trash bin |
| battery | — | — | Report battery percentage |
| system_info | — | — | CPU, RAM, disk usage report |

### Web & Information

| Action | Target | Args | Description |
|--------|--------|------|-------------|
| search_web | search query | — | Open DuckDuckGo search in browser |
| open_url | URL | — | Open URL in default browser |
| weather | — | — | Fetch weather (wttr.in → LLM summary) |
| news | topic (optional) | — | Scrape DuckDuckGo news → LLM summary |

### Smart Home (IFTTT)

| Action | Target | Args | Description |
|--------|--------|------|-------------|
| smart_home | device name | on/off | Trigger IFTTT webhook |

### Workspace

| Action | Target | Args | Description |
|--------|--------|------|-------------|
| switch_workspace | workspace number | — | Switch virtual desktop |

### Utilities

| Action | Target | Args | Description |
|--------|--------|------|-------------|
| run_command | shell command | — | Execute arbitrary shell command |
| list_windows | — | — | List all open windows |
| analyze_selection | — | instruction | Get clipboard text → LLM analysis |
| timer | — | seconds | Set countdown timer |
| demo | — | — | Run demo mode (30s with music) |
| chat | — | — | Free conversation (no system action) |

## Solo Actions

These actions cannot be combined with others in a single response:
- `shutdown`, `restart`, `suspend`, `logout`
- `weather`, `news`
- `analyze_screen`, `analyze_selection`
- `demo`, `chat`

## Stop Words (End Conversation)

Portuguese stop words that end the conversation loop:
- "para", "pare", "parar", "chega", "dispensado"

## Adding a New Command

1. **commands.py**: Add action to `COMMANDS` dict with description and notes
2. **command_executor.py**: Add `_do_{action_name}(self, target, args)` method
3. **command_interpreter.py**: The system prompt auto-generates command list from `COMMANDS`
4. **install.sh**: If new dependencies needed, update installation steps

The LLM system prompt auto-includes all commands from the `COMMANDS` dict, so no prompt editing is needed.
