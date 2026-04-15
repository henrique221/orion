import os

import yaml

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.yaml")

_DEFAULTS = {
    "language": "pt_BR",
}


def load_config():
    """Read config.yaml and return dict with defaults applied."""
    try:
        with open(_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        data = {}
    merged = {**_DEFAULTS, **data}
    return merged


def save_config(data):
    """Write dict to config.yaml."""
    with open(_CONFIG_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def get_language():
    """Shortcut: return the current language setting."""
    return load_config()["language"]
