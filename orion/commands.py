"""
Command registry — reads command definitions from locale strings.

To add a new command:
  1. Add an entry to COMMANDS in both orion/locales/pt_BR.py and en.py
  2. Add a _do_<action> method in command_executor.py
"""

import random


# ── Config (language-agnostic) ──────────────────────────────────────

IFTTT_KEY = "h0IO5AV2asEYG4fjT_SPbeimWkcqmlevMAAyaKZcYss"
IFTTT_URL = "https://maker.ifttt.com/trigger/{event}/with/key/" + IFTTT_KEY

SMART_HOME_DEVICES = {
    "varanda": {"on": "varanda_on", "off": "varanda_off"},
    "piscina": {"on": "piscina_on", "off": "piscina_off"},
}

# Monitor layout: name → (x, y, width, height)
MONITORS = {
    "ultrawide": (0, 0, 2560, 1080),
    "notebook": (2560, 0, 1920, 1080),
    "inferior": (903, 1080, 1920, 1080),
}

VISION_MODEL = "moondream"

SAFE_COMMAND_PREFIXES = [
    "ls", "pwd", "echo", "date", "cal", "df", "free",
    "whoami", "hostname", "uname", "uptime", "cat /etc",
    "which", "wc", "head", "tail",
]


# ── Auto-generated from locale strings ──────────────────────────────

def get_action_enum(strings):
    return list(strings["commands"].keys())


def build_prompt_mappings(strings):
    lines = []
    for action, cmd in strings["commands"].items():
        for example in cmd["examples"]:
            if "→" in example:
                lines.append(f"{example}, action={action}")
            else:
                lines.append(f"{example} → action={action}")
    return "\n".join(lines)


def build_prompt_notes(strings):
    notes = []
    for cmd in strings["commands"].values():
        if "notes" in cmd:
            notes.append(cmd["notes"])
    return "\n".join(notes)


def build_json_schema(strings):
    return {
        "type": "object",
        "properties": {
            "commands": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": get_action_enum(strings)},
                        "target": {"type": "string"},
                        "args": {"type": "string"},
                        "reply": {"type": "string"},
                    },
                    "required": ["action", "target", "args", "reply"],
                },
            },
        },
        "required": ["commands"],
    }


def pick(strings, action, variant="success", **kwargs):
    """Pick a random reply template and format it."""
    replies = strings["commands"].get(action, {}).get("replies", {})
    templates = replies.get(variant, [])
    if not templates:
        return None
    return random.choice(templates).format(**kwargs)
