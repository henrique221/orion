import json

import requests

SYSTEM_PROMPT = """\
Você é o Orion, assistente de voz brasileiro. Analise o comando e retorne JSON.
Responda SEMPRE em português do Brasil no campo reply.

Exemplos:
"abre o Chrome" → action=open_app, target=chrome
"fecha o terminal" → action=close_app, target=terminal
"aumenta o volume" → action=volume_up, args=10
"pesquisa sobre Python" → action=search_web, target=Python
"que horas são" → action=show_time
"tira print da tela" → action=screenshot
"fecha tudo" ou "fechar tudo" → action=close_all
"iniciar trabalhos" ou "começar a trabalhar" → action=start_work
"vai para área de trabalho 2" → action=switch_workspace, target=2
"área de trabalho 1" → action=switch_workspace, target=1
"fechar orion" ou "para" → action=stop, reply=Até logo!"""

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "open_app",
                "close_app",
                "open_url",
                "search_web",
                "volume_up",
                "volume_down",
                "mute",
                "screenshot",
                "show_time",
                "list_windows",
                "run_command",
                "close_all",
                "start_work",
                "switch_workspace",
                "stop",
                "chat",
            ],
        },
        "target": {"type": "string"},
        "args": {"type": "string"},
        "reply": {"type": "string"},
    },
    "required": ["action", "target", "args", "reply"],
}


class CommandInterpreter:
    OLLAMA_URL = "http://localhost:11434"
    MODEL = "llama3.2"

    def __init__(self):
        self._check_ollama()
        self._warmup()

    def _check_ollama(self):
        try:
            r = requests.get(f"{self.OLLAMA_URL}/api/tags", timeout=5)
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            found = any(m.startswith(self.MODEL) for m in models)
            if not found:
                print(
                    f"  AVISO: Modelo '{self.MODEL}' não encontrado. "
                    f"Modelos disponíveis: {models}"
                )
                print(f"  Execute: ollama pull {self.MODEL}")
            else:
                print(f"  Ollama OK, modelo '{self.MODEL}' disponível.")
        except requests.ConnectionError:
            print(
                "  AVISO: Ollama não está rodando. Execute: ollama serve"
            )
        except Exception as e:
            print(f"  AVISO: Erro ao verificar Ollama: {e}")

    def _warmup(self):
        """Pré-carrega o modelo na GPU para evitar cold start."""
        try:
            requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.MODEL,
                    "prompt": "oi",
                    "keep_alive": -1,
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=30,
            )
            print("  Modelo LLM pré-carregado na GPU.")
        except Exception:
            pass

    def interpret(self, text):
        if not text:
            return None

        try:
            response = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.MODEL,
                    "prompt": text,
                    "system": SYSTEM_PROMPT,
                    "format": JSON_SCHEMA,
                    "stream": False,
                    "keep_alive": -1,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 512,
                        "num_predict": 80,
                    },
                },
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            return json.loads(result["response"])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Erro ao parsear resposta do LLM: {e}")
            return {
                "action": "chat",
                "target": "",
                "args": "",
                "reply": "Desculpe, não entendi o comando.",
            }
        except requests.RequestException as e:
            print(f"  Erro de comunicação com Ollama: {e}")
            return {
                "action": "chat",
                "target": "",
                "args": "",
                "reply": "Erro ao processar o comando.",
            }
