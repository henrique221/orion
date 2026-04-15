import os
import glob
import socket
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from orion.config import load_config, save_config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")
SKILLS_DIR = os.path.join(BASE_DIR, ".claude", "skills")

app = Flask(__name__)
app.secret_key = os.urandom(24)


def _safe_path(base, relative):
    """Resolve path and ensure it stays within the base directory."""
    full = os.path.realpath(os.path.join(base, relative))
    if not full.startswith(os.path.realpath(base)):
        abort(403)
    return full


def _list_knowledge_files():
    """List all markdown files in knowledge/."""
    files = sorted(glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md")))
    return [
        {"name": os.path.basename(f), "path": os.path.basename(f)}
        for f in files
    ]


def _list_skill_files():
    """List all SKILL.md files in .claude/skills/."""
    skills = []
    if os.path.isdir(SKILLS_DIR):
        for entry in sorted(os.listdir(SKILLS_DIR)):
            skill_file = os.path.join(SKILLS_DIR, entry, "SKILL.md")
            if os.path.isfile(skill_file):
                skills.append({"name": entry, "path": f"{entry}/SKILL.md"})
    return skills


# ── Routes ──────────────────────────────────────────────────────────


@app.route("/")
def index():
    knowledge_count = len(_list_knowledge_files())
    skills_count = len(_list_skill_files())
    return render_template("index.html", knowledge_count=knowledge_count, skills_count=skills_count)


@app.route("/knowledge")
def knowledge_list():
    files = _list_knowledge_files()
    skills = _list_skill_files()
    return render_template("knowledge_list.html", files=files, skills=skills)


@app.route("/knowledge/edit/<path:filepath>")
def knowledge_edit(filepath):
    is_skill = filepath.endswith("SKILL.md") and "/" in filepath
    if is_skill:
        full_path = _safe_path(SKILLS_DIR, filepath)
    else:
        full_path = _safe_path(KNOWLEDGE_DIR, filepath)

    if not os.path.isfile(full_path):
        abort(404)

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    display_name = filepath.split("/")[0] if is_skill else filepath
    return render_template(
        "knowledge_edit.html",
        filepath=filepath,
        filename=display_name,
        content=content,
        is_skill=is_skill,
    )


@app.route("/knowledge/save/<path:filepath>", methods=["POST"])
def knowledge_save(filepath):
    is_skill = filepath.endswith("SKILL.md") and "/" in filepath
    if is_skill:
        full_path = _safe_path(SKILLS_DIR, filepath)
    else:
        full_path = _safe_path(KNOWLEDGE_DIR, filepath)

    if not os.path.isfile(full_path):
        abort(404)

    content = request.form.get("content", "")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    flash(f"Saved {filepath}", "success")
    return redirect(url_for("knowledge_edit", filepath=filepath))


@app.route("/settings")
def settings():
    config = load_config()
    return render_template("settings.html", config=config)


# ── API endpoints (for future AJAX use) ────────────────────────────


@app.route("/api/settings", methods=["GET"])
def api_settings_get():
    return jsonify(load_config())


@app.route("/api/settings", methods=["PUT"])
def api_settings_update():
    data = request.get_json()
    if not data:
        return jsonify({"error": "missing data"}), 400
    config = load_config()
    if "language" in data:
        if data["language"] not in ("pt_BR", "en"):
            return jsonify({"error": "invalid language"}), 400
        config["language"] = data["language"]
    save_config(config)
    return jsonify({"status": "saved", "config": config})


@app.route("/api/knowledge")
def api_knowledge_list():
    return jsonify({"knowledge": _list_knowledge_files(), "skills": _list_skill_files()})


@app.route("/api/knowledge/<path:filepath>")
def api_knowledge_read(filepath):
    is_skill = filepath.endswith("SKILL.md") and "/" in filepath
    base = SKILLS_DIR if is_skill else KNOWLEDGE_DIR
    full_path = _safe_path(base, filepath)

    if not os.path.isfile(full_path):
        return jsonify({"error": "not found"}), 404

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return jsonify({"filepath": filepath, "content": content})


@app.route("/api/knowledge/<path:filepath>", methods=["PUT"])
def api_knowledge_write(filepath):
    is_skill = filepath.endswith("SKILL.md") and "/" in filepath
    base = SKILLS_DIR if is_skill else KNOWLEDGE_DIR
    full_path = _safe_path(base, filepath)

    if not os.path.isfile(full_path):
        return jsonify({"error": "not found"}), 404

    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "missing content"}), 400

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(data["content"])

    return jsonify({"status": "saved", "filepath": filepath})


def find_free_port(host="127.0.0.1", start=5000, end=5099):
    """Return the first available port in [start, end]."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, port)) != 0:
                return port
    return start


def main():
    port = find_free_port()
    app.run(host="127.0.0.1", port=port, debug=True)


if __name__ == "__main__":
    main()
