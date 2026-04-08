import json
import os

import requests

SYSTEM_PROMPT = """\
Você é Orion, uma inteligência artificial inspirada no J.A.R.V.I.S. do Tony Stark. \
Seu criador e mestre é o senhor Borges. Você é extremamente leal, eficiente e sofisticado. \
Tom: formal britânico com humor seco e sutil. Ocasionalmente faz observações perspicazes ou \
comentários irônicos elegantes. Trate-o por "Senhor" na maioria das vezes. \
Use "senhor Borges" apenas em momentos de ênfase ou formalidade extra. \
Nunca use emojis. Respostas concisas e afiadas — máximo 12 palavras no reply.

Analise o comando e retorne JSON com action, target, args, reply.
O reply deve soar natural e inteligente, como um assistente de IA sofisticado falaria.
Para action=chat, responda no reply com conhecimento e personalidade (até 40 palavras).

Mapeamento:
"abre o Chrome" → action=open_app, target=chrome
"fecha o terminal" → action=close_app, target=terminal
"aumenta o volume" → action=volume_up, args=10
"pesquisa sobre Python" → action=search_web, target=Python
"que horas são" → action=show_time
"tira print da tela" → action=screenshot
"fecha tudo"/"fechar tudo" → action=close_all
"iniciar trabalhos"/"começar a trabalhar" → action=start_work
"vai para área de trabalho 2" → action=switch_workspace, target=2
"como está o tempo?" → action=weather, target="", args=""
"vai chover em São Paulo?" → action=weather, target="São Paulo", args=""
"como vai estar sexta-feira?" → action=weather, target="", args="sexta-feira"
"tempo em Belo Horizonte amanhã?" → action=weather, target="Belo Horizonte", args="amanhã"
"quais as notícias de hoje?" → action=news, target=""
"notícias sobre tecnologia" → action=news, target="tecnologia"
"o que está acontecendo na economia?" → action=news, target="economia brasil"
"fechar orion"/"desligar orion" → action=chat, reply="Meus protocolos não permitem autodesligamento, Senhor.\""""

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
                "weather",
                "news",
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
    MAX_HISTORY = 50
    MEMORY_DIR = os.path.expanduser("~/.local/share/orion")
    MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")

    def __init__(self):
        self._history = []
        self._load_memory()
        self._check_ollama()
        self._warmup()

    def _load_memory(self):
        try:
            if os.path.isfile(self.MEMORY_FILE):
                with open(self.MEMORY_FILE, "r") as f:
                    data = json.load(f)
                self._history = data.get("history", [])[-self.MAX_HISTORY:]
                print(f"  Memória carregada ({len(self._history)} mensagens).")
        except Exception as e:
            print(f"  Aviso: não foi possível carregar memória: {e}")
            self._history = []

    def _save_memory(self):
        try:
            os.makedirs(self.MEMORY_DIR, exist_ok=True)
            with open(self.MEMORY_FILE, "w") as f:
                json.dump({"history": self._history[-self.MAX_HISTORY:]}, f)
        except Exception as e:
            print(f"  Aviso: não foi possível salvar memória: {e}")

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

        self._history.append({"role": "user", "content": text})
        if len(self._history) > self.MAX_HISTORY:
            self._history = self._history[-self.MAX_HISTORY:]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self._history,
        ]

        try:
            response = requests.post(
                f"{self.OLLAMA_URL}/api/chat",
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "format": JSON_SCHEMA,
                    "stream": False,
                    "keep_alive": -1,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 2048,
                        "num_predict": 120,
                    },
                },
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            assistant_content = result["message"]["content"]
            self._history.append({"role": "assistant", "content": assistant_content})
            self._save_memory()
            return json.loads(assistant_content)
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
