import json
import os
import threading

import requests

from orion.commands import build_json_schema, build_prompt_mappings, build_prompt_notes, get_action_enum


class CommandInterpreter:
    OLLAMA_URL = "http://localhost:11434"
    MODEL = "qwen2.5:1.5b"
    MAX_HISTORY = 10
    CLEANUP_EVERY = 10  # Run cleanup every N interactions
    MEMORY_DIR = os.path.expanduser("~/.local/share/orion")
    MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")
    LEARNINGS_FILE = os.path.join(MEMORY_DIR, "learnings.json")
    MAX_LEARNINGS = 30

    def __init__(self, strings):
        self._strings = strings
        self._history = []
        self._learnings = []
        self._interaction_count = 0
        self._cleaning = False
        self._base_prompt = self._strings["system_prompt"].format(
            mappings=build_prompt_mappings(strings),
            notes=build_prompt_notes(strings),
        )
        self._json_schema = build_json_schema(strings)
        self._valid_actions = set(get_action_enum(strings))
        self._load_memory()
        self._load_learnings()
        self._system_prompt = self._build_full_prompt()
        self._check_ollama()
        self._warmup()

    # Actions that should never appear alongside other actions
    SOLO_ACTIONS = {"show_time", "analyze_screen", "analyze_selection", "weather",
                    "news", "system_info", "battery", "demo", "shutdown",
                    "restart", "suspend", "logout"}

    def _load_memory(self):
        try:
            if os.path.isfile(self.MEMORY_FILE):
                with open(self.MEMORY_FILE, "r") as f:
                    data = json.load(f)
                raw = data.get("history", [])[-self.MAX_HISTORY:]
                # Sanitize on load: drop orphaned or malformed entries
                self._history = self._sanitize_history(raw)
                print(f"  {self._strings['terminal']['memory_loaded'].format(count=len(self._history))}")
        except Exception as e:
            print(f"  {self._strings['terminal']['memory_load_error'].format(error=e)}")
            self._history = []

    def _sanitize_history(self, history):
        """Remove malformed pairs and keep only valid user→assistant sequences."""
        clean = []
        i = 0
        while i < len(history) - 1:
            user_msg = history[i]
            asst_msg = history[i + 1]
            if user_msg.get("role") != "user" or asst_msg.get("role") != "assistant":
                i += 1
                continue
            # Validate assistant content
            try:
                parsed = json.loads(asst_msg["content"])
                cmds = parsed.get("commands", [parsed])
                actions = [c.get("action") for c in cmds]
                if all(a in self._valid_actions for a in actions):
                    clean.append(user_msg)
                    clean.append(asst_msg)
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass  # Drop malformed
            i += 2
        return clean

    def _compact_response(self, commands):
        """Build a minimal JSON response to save in history (fewer tokens)."""
        compact_cmds = []
        for c in commands:
            entry = {"action": c.get("action", "")}
            if c.get("target"):
                entry["target"] = c["target"]
            if c.get("args"):
                entry["args"] = c["args"]
            # Skip reply — it wastes tokens and doesn't help interpretation
            compact_cmds.append(entry)
        return json.dumps({"commands": compact_cmds}, ensure_ascii=False, separators=(",", ":"))

    def record_execution_results(self, results):
        """Update the last assistant history entry with what was actually spoken to the user."""
        if not self._history or self._history[-1]["role"] != "assistant":
            return
        try:
            entry = json.loads(self._history[-1]["content"])
            commands = entry.get("commands", [])
            for i, result in enumerate(results):
                if i < len(commands) and result:
                    commands[i]["result"] = result[:150]
            self._history[-1]["content"] = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
            self._save_memory()
        except (json.JSONDecodeError, KeyError):
            pass

    def _validate_response(self, commands):
        """Check if the response makes structural sense."""
        if not commands:
            return False
        actions = [c.get("action") for c in commands]
        # All actions must be valid
        if not all(a in self._valid_actions for a in actions):
            return False
        # Solo actions should not appear with other actions (except chat)
        non_chat = [a for a in actions if a != "chat"]
        if len(non_chat) > 1:
            for a in non_chat:
                if a in self.SOLO_ACTIONS:
                    print(f"  {self._strings['terminal']['validate_solo'].format(action=a)}")
                    return False
        # Detect duplicate consecutive actions (stuck pattern)
        if len(actions) > 1 and len(set(actions)) == 1 and actions[0] != "smart_home":
            print(f"  {self._strings['terminal']['validate_duplicate'].format(action=actions[0])}")
            return False
        return True

    def _save_memory(self):
        try:
            os.makedirs(self.MEMORY_DIR, exist_ok=True)
            with open(self.MEMORY_FILE, "w") as f:
                json.dump({"history": self._history[-self.MAX_HISTORY:]}, f,
                          ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            print(f"  {self._strings['terminal']['memory_save_error'].format(error=e)}")

    def _load_learnings(self):
        try:
            if os.path.isfile(self.LEARNINGS_FILE):
                with open(self.LEARNINGS_FILE, "r") as f:
                    self._learnings = json.load(f)[-self.MAX_LEARNINGS:]
                print(f"  {self._strings['terminal']['learnings_loaded'].format(count=len(self._learnings))}")
        except Exception:
            self._learnings = []

    def _save_learnings(self):
        try:
            os.makedirs(self.MEMORY_DIR, exist_ok=True)
            with open(self.LEARNINGS_FILE, "w") as f:
                json.dump(self._learnings[-self.MAX_LEARNINGS:], f, ensure_ascii=False)
        except Exception as e:
            print(f"  {self._strings['terminal']['learnings_save_error'].format(error=e)}")

    def _build_full_prompt(self):
        prompt = self._base_prompt
        if self._learnings:
            prompt += f"\n\n{self._strings['executor']['learnings_header']}\n"
            prompt += "\n".join(f"- {l}" for l in self._learnings)
        return prompt

    def _maybe_cleanup(self):
        """Triggers background history cleanup + learning every CLEANUP_EVERY interactions."""
        self._interaction_count += 1
        if self._interaction_count >= self.CLEANUP_EVERY and not self._cleaning:
            self._interaction_count = 0
            threading.Thread(target=self._cleanup_and_learn, daemon=True).start()

    def _cleanup_and_learn(self):
        self._cleanup_history()
        self._extract_learnings()

    def _cleanup_history(self):
        """Uses the LLM to evaluate and prune bad history entries."""
        if len(self._history) < 6:
            return
        self._cleaning = True
        try:
            # Build pairs for evaluation
            pairs = []
            i = 0
            while i < len(self._history) - 1:
                if (self._history[i]["role"] == "user"
                        and self._history[i + 1]["role"] == "assistant"):
                    pairs.append((i, self._history[i], self._history[i + 1]))
                    i += 2
                else:
                    i += 1

            if not pairs:
                return

            # Format pairs for LLM review
            review = []
            for idx, (_, user_msg, asst_msg) in enumerate(pairs):
                review.append(f"[{idx}] User: {user_msg['content']}")
                try:
                    parsed = json.loads(asst_msg["content"])
                    cmds = parsed.get("commands", [parsed])
                    actions = [c.get("action", "?") for c in cmds]
                    review.append(f"[{idx}] Actions: {', '.join(actions)}")
                except (json.JSONDecodeError, TypeError):
                    review.append(f"[{idx}] Response: {asst_msg['content'][:100]}")

            prompt = (
                "You are reviewing a voice assistant's command history. "
                f"Valid actions are: {', '.join(sorted(self._valid_actions))}\n\n"
                "For each pair, decide if the action(s) CORRECTLY match the user's request.\n"
                "Bad examples: user asks time but gets open_app, user asks about screen but gets search_web, "
                "repeated/stuck patterns, nonsensical responses.\n\n"
                "History:\n" + "\n".join(review) + "\n\n"
                "Return ONLY a JSON object: {\"keep\": [list of pair indices to keep]}. "
                "Keep pairs where the action correctly matches the user intent. "
                "Remove bad, corrupted, or incorrect pairs."
            )

            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0, "num_predict": 100},
                },
                timeout=20,
            )
            result = json.loads(r.json()["response"])
            keep_indices = set(result.get("keep", []))

            # Rebuild history with only good pairs
            new_history = []
            for idx, (_, user_msg, asst_msg) in enumerate(pairs):
                if idx in keep_indices:
                    new_history.append(user_msg)
                    new_history.append(asst_msg)

            removed = len(pairs) - len(keep_indices)
            if removed > 0:
                self._history = new_history
                self._save_memory()
                print(f"  {self._strings['terminal']['cleanup_removed'].format(count=removed)}")
            else:
                print(f"  {self._strings['terminal']['cleanup_clean']}")

        except Exception as e:
            print(f"  {self._strings['terminal']['cleanup_error'].format(error=e)}")
        finally:
            self._cleaning = False

    def _extract_learnings(self):
        """Extracts useful insights from recent history to improve future interactions."""
        if len(self._history) < 4:
            return
        try:
            # Format recent history for analysis
            recent = []
            for msg in self._history[-self.MAX_HISTORY:]:
                role = msg["role"]
                content = msg["content"][:200]
                recent.append(f"{role}: {content}")

            existing = ""
            if self._learnings:
                existing = "Aprendizados já salvos:\n" + "\n".join(f"- {l}" for l in self._learnings) + "\n\n"

            prompt = (
                "You are analyzing a voice assistant's conversation history to extract useful learnings.\n\n"
                f"{existing}"
                "Recent conversations:\n" + "\n".join(recent) + "\n\n"
                "Extract ONLY important new insights. Good learnings:\n"
                "- User preferences for how they phrase commands\n"
                "- Personal info mentioned in chat (name, location, interests)\n"
                "- Corrections the user made (wrong action → right action)\n"
                "- Patterns in what the user commonly asks\n\n"
                "Do NOT include:\n"
                "- Things already in the existing learnings\n"
                "- Generic/obvious facts\n"
                "- Specific timestamps or one-time requests\n\n"
                "Return ONLY a JSON object: {\"learnings\": [\"insight 1\", \"insight 2\"]}. "
                "Each insight should be a short sentence in Portuguese. "
                "Return {\"learnings\": []} if nothing new is worth saving."
            )

            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0.1, "num_predict": 200},
                },
                timeout=20,
            )
            result = json.loads(r.json()["response"])
            new_learnings = result.get("learnings", [])

            if new_learnings:
                self._learnings.extend(new_learnings)
                # Deduplicate: keep only unique learnings
                if len(self._learnings) > self.MAX_LEARNINGS:
                    self._learnings = self._learnings[-self.MAX_LEARNINGS:]
                self._save_learnings()
                self._system_prompt = self._build_full_prompt()
                print(f"  {self._strings['terminal']['learn_new'].format(count=len(new_learnings), items=new_learnings)}")
            else:
                print(f"  {self._strings['terminal']['learn_none']}")

        except Exception as e:
            print(f"  {self._strings['terminal']['learn_error'].format(error=e)}")

    def _check_ollama(self):
        try:
            r = requests.get(f"{self.OLLAMA_URL}/api/tags", timeout=5)
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            found = any(m.startswith(self.MODEL) for m in models)
            if not found:
                print(f"  {self._strings['terminal']['ollama_not_found'].format(model=self.MODEL, available=models)}")
                print(f"  {self._strings['terminal']['ollama_pull_hint'].format(model=self.MODEL)}")
            else:
                print(f"  {self._strings['terminal']['ollama_ok'].format(model=self.MODEL)}")
        except requests.ConnectionError:
            print(f"  {self._strings['terminal']['ollama_not_running']}")
        except Exception as e:
            print(f"  {self._strings['terminal']['ollama_check_error'].format(error=e)}")

    def _warmup(self):
        """Pré-carrega o modelo na CPU para evitar cold start."""
        try:
            requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.MODEL,
                    "prompt": "oi",
                    "keep_alive": 0,
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=120,
            )
            print(f"  {self._strings['terminal']['llm_preloaded']}")
        except Exception:
            pass

    def interpret(self, text):
        if not text:
            return None

        self._history.append({"role": "user", "content": text})
        if len(self._history) > self.MAX_HISTORY:
            self._history = self._history[-self.MAX_HISTORY:]

        messages = [
            {"role": "system", "content": self._system_prompt},
            *self._history,
        ]

        try:
            response = requests.post(
                f"{self.OLLAMA_URL}/api/chat",
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "format": self._json_schema,
                    "stream": False,
                    "keep_alive": 0,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 4096,
                        "num_predict": 300,
                    },
                },
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            assistant_content = result["message"]["content"]
            parsed = json.loads(assistant_content)
            commands = parsed["commands"] if "commands" in parsed else [parsed]

            if self._validate_response(commands):
                # Save compact version to minimize token usage
                compact = self._compact_response(commands)
                self._history.append({"role": "assistant", "content": compact})
                self._save_memory()
                self._maybe_cleanup()
            else:
                # Bad response — don't poison history, drop user msg too
                if self._history and self._history[-1]["role"] == "user":
                    self._history.pop()

            return commands
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  {self._strings['terminal']['llm_parse_error'].format(error=e)}")
            return [{
                "action": "chat",
                "target": "",
                "args": "",
                "reply": self._strings["terminal"]["llm_default_error"],
            }]
        except requests.RequestException as e:
            print(f"  {self._strings['terminal']['llm_comm_error'].format(error=e)}")
            return [{
                "action": "chat",
                "target": "",
                "args": "",
                "reply": self._strings["terminal"]["llm_request_error"],
            }]
