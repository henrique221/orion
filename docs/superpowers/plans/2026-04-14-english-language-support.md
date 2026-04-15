# English Language Support — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add English as a second language for Orion, selectable via the web Settings page, preserving the JARVIS personality in both languages.

**Architecture:** A `config.yaml` stores the language choice (`pt_BR` or `en`). At startup, `main.py` reads the config, loads the matching locale module (`orion/locales/pt_BR.py` or `orion/locales/en.py`), and passes the resulting `strings` dict down through constructors. No component reads config directly — strings flow from `main.py` down.

**Tech Stack:** Python, PyYAML, Flask, faster-whisper, XTTS v2, Kokoro, Piper, espeak-ng

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `orion/config.py` | Create | Load/save `config.yaml`, defaults |
| `orion/locales/__init__.py` | Create | `get_strings(lang)` loader |
| `orion/locales/pt_BR.py` | Create | All Portuguese strings extracted from codebase |
| `orion/locales/en.py` | Create | All English translations |
| `orion/commands.py` | Modify | Functions accept `strings` param instead of using global COMMANDS |
| `orion/command_interpreter.py` | Modify | Accept `strings`, use locale system prompt |
| `orion/command_executor.py` | Modify | Accept `strings`, use locale messages/prompts |
| `orion/speech_recognizer.py` | Modify | Accept `strings`/`language`, swap Whisper config |
| `orion/tts.py` | Modify | Accept `strings`, swap TTS language params |
| `orion/wake_word_detector.py` | Modify | Accept `language` for Whisper |
| `orion/voice_assistant.py` | Modify | Accept `strings`/`language`, pass to sub-components |
| `main.py` | Modify | Load config, get strings, pass to VoiceAssistant |
| `orion/web/app.py` | Modify | Add settings API endpoints |
| `orion/web/templates/settings.html` | Modify | Add language dropdown with save |
| `config.yaml` | Create | Default config file |
| `requirements.txt` | Modify | Add `pyyaml` |
| `install.sh` | Modify | Add English Piper voice download, pyyaml |

---

### Task 1: Config System

**Files:**
- Create: `orion/config.py`
- Create: `config.yaml`
- Modify: `requirements.txt`

- [ ] **Step 1: Add pyyaml to requirements.txt**

Add `pyyaml` to the end of `requirements.txt`:

```
faster-whisper==1.1.1
sounddevice==0.5.1
soundfile==0.12.1
numpy==1.26.4
requests==2.32.3
noisereduce==3.0.3
coqui-tts==0.27.5
torch>=2.6.0
torchaudio>=2.6.0
flask>=3.0.0
pyyaml>=6.0
```

- [ ] **Step 2: Install pyyaml**

Run: `pip install pyyaml`

- [ ] **Step 3: Create default config.yaml**

Create `config.yaml` at the project root:

```yaml
language: pt_BR
```

- [ ] **Step 4: Create orion/config.py**

```python
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
```

- [ ] **Step 5: Verify config module works**

Run: `cd /home/henrique/gitdocs/orion && python -c "from orion.config import load_config, get_language; print(load_config()); print(get_language())"`

Expected: `{'language': 'pt_BR'}` and `pt_BR`

- [ ] **Step 6: Commit**

```bash
git add orion/config.py config.yaml requirements.txt
git commit -m "feat: add config system with YAML persistence"
```

---

### Task 2: Locale Loader

**Files:**
- Create: `orion/locales/__init__.py`

- [ ] **Step 1: Create the locales package**

```bash
mkdir -p orion/locales
```

- [ ] **Step 2: Create orion/locales/__init__.py**

```python
def get_strings(language="pt_BR"):
    """Load the locale strings dict for the given language."""
    if language == "en":
        from orion.locales import en
        return en.STRINGS
    from orion.locales import pt_BR
    return pt_BR.STRINGS
```

- [ ] **Step 3: Commit**

```bash
git add orion/locales/__init__.py
git commit -m "feat: add locale loader module"
```

---

### Task 3: Portuguese Locale (pt_BR.py)

Extract every hardcoded Portuguese string from the codebase into a single `STRINGS` dict. This is a zero-behavior-change extraction — the existing code will read from this dict instead of inline constants.

**Files:**
- Create: `orion/locales/pt_BR.py`

- [ ] **Step 1: Create orion/locales/pt_BR.py**

This file is large. It contains ALL user-facing and terminal strings currently hardcoded across the codebase. Create it in full:

```python
"""Portuguese (Brazil) locale — all user-facing strings for Orion."""

import os

STRINGS = {
    # ── LLM System Prompt ───────────────────────────────────────────
    "system_prompt": (
        "Você é Orion, uma inteligência artificial inspirada no J.A.R.V.I.S. do Tony Stark. "
        "Seu criador e mestre é o senhor Borges. Você é extremamente leal, eficiente e sofisticado. "
        "Tom: formal britânico com humor seco e sutil. Ocasionalmente faz observações perspicazes ou "
        "comentários irônicos elegantes. Trate-o por \"Senhor\" na maioria das vezes. "
        "Use \"senhor Borges\" apenas em momentos de ênfase ou formalidade extra. "
        "Nunca use emojis. Respostas concisas e afiadas — máximo 12 palavras no reply.\n"
        "\n"
        "Analise o comando e retorne JSON com \"commands\": lista de objetos {{action, target, args, reply}}.\n"
        "Se houver múltiplos comandos na frase, retorne um objeto para cada na ordem mencionada.\n"
        "Se houver apenas um comando, retorne a lista com um único objeto.\n"
        "O reply deve soar natural e inteligente — máximo 12 palavras. Apenas o ÚLTIMO comando precisa de reply.\n"
        "\n"
        "QUALQUER combinação de comandos pode ser encadeada com \"e\", \"depois\", vírgula, etc. "
        "Sempre separe cada ação em seu próprio objeto na lista, na ordem mencionada. "
        "Apenas o ÚLTIMO comando precisa de reply que resuma TODAS as ações.\n"
        "\n"
        "Exemplos múltiplos:\n"
        "\"desliga a varanda e a piscina\" → commands: [\n"
        "  {{action: smart_home, target: varanda, args: off, reply: \"\"}},\n"
        "  {{action: smart_home, target: piscina, args: off, reply: \"Varanda e piscina desligadas, Senhor.\"}}\n"
        "]\n"
        "\"abre o Chrome, aumenta o volume e tira um print\" → commands: [\n"
        "  {{action: open_app, target: chrome, reply: \"\"}},\n"
        "  {{action: volume_up, args: 10, reply: \"\"}},\n"
        "  {{action: screenshot, reply: \"Chrome aberto, volume aumentado e print capturado, Senhor.\"}}\n"
        "]\n"
        "\"bloqueia o computador e desliga a luz da varanda\" → commands: [\n"
        "  {{action: lock_screen, reply: \"\"}},\n"
        "  {{action: smart_home, target: varanda, args: off, reply: \"Computador bloqueado e varanda desligada, Senhor.\"}}\n"
        "]\n"
        "\n"
        "Referências ao contexto:\n"
        "Se o usuário pedir para repetir ou tentar novamente (ex: \"tenta de novo\", \"de novo\", \"repete\", "
        "\"faz de novo\", \"tenta outra vez\", \"mais uma vez\"), repita EXATAMENTE o último comando do histórico "
        "com os mesmos parâmetros (action, target, args). Gere um reply apropriado.\n"
        "No histórico, comandos podem ter um campo \"result\" com o que foi realmente dito ao usuário. "
        "Use isso para entender se ações anteriores tiveram sucesso ou falharam. "
        "Se o result indica falha e o usuário pede para tentar de novo, repita o mesmo comando.\n"
        "\n"
        "Para action=chat, responda no reply com conhecimento e personalidade (até 40 palavras).\n"
        "\n"
        "Mapeamento:\n"
        "{mappings}\n"
        "\n"
        "{notes}"
    ),

    # ── Listening Phrases ───────────────────────────────────────────
    "listening_phrases": [
        "Às suas ordens, Senhor.",
        "Online e operacional.",
        "Diga, Senhor.",
        "Pode falar.",
        "Sim, Senhor?",
        "Pronto para receber instruções.",
        "No que posso ser útil?",
        "À disposição.",
        "Aguardando comando, Senhor.",
        "Prossiga, Senhor.",
    ],

    # ── Greetings ───────────────────────────────────────────────────
    "greetings": {
        "morning": [
            "Bom dia, Senhor. Sistemas online.",
            "Bom dia, senhor Borges. Às ordens.",
            "Bom dia, Senhor. Orion operacional.",
        ],
        "afternoon": [
            "Boa tarde, Senhor. Pronto para servir.",
            "Boa tarde, senhor Borges. Online.",
            "Boa tarde, Senhor. Sistemas ativos.",
        ],
        "evening": [
            "Boa noite, Senhor. À disposição.",
            "Boa noite, senhor Borges. Orion online.",
            "Boa noite, Senhor. Pronto quando precisar.",
        ],
    },

    # ── Stop Words ──────────────────────────────────────────────────
    "stop_words": ("para", "pare", "parar", "chega", "dispensado"),

    # ── Stop Responses ──────────────────────────────────────────────
    "stop_responses": [
        "Entendido, Senhor.",
        "À disposição, Senhor.",
        "Estarei aqui se precisar.",
    ],

    # ── Error Responses ─────────────────────────────────────────────
    "error_responses": [
        "Houve uma falha no processamento, Senhor.",
        "Meus sistemas não conseguiram interpretar. Pode repetir?",
        "Interferência nos meus circuitos. Tente novamente.",
    ],

    # ── Command Registry ────────────────────────────────────────────
    "commands": {
        "open_app": {
            "examples": ['"abre o Chrome" → target=chrome'],
            "replies": {
                "success": [
                    "Inicializando {target}, Senhor.",
                    "Carregando {target}.",
                    "{target} entrando online.",
                    "Executando {target}, Senhor.",
                ],
                "error": [
                    "Aplicativo {target} não localizado nos meus registros, Senhor.",
                ],
            },
        },
        "close_app": {
            "examples": ['"fecha o terminal" → target=terminal'],
            "replies": {
                "success": [
                    "{target} encerrado, Senhor.",
                    "Desligando {target}.",
                    "{target} fora do ar.",
                ],
                "error": [
                    "{target} não está respondendo ao encerramento, Senhor.",
                ],
            },
        },
        "open_url": {
            "examples": ['"abre google.com" → target=google.com'],
            "replies": {
                "success": [
                    "Direcionando navegador, Senhor.",
                    "Acessando {target}.",
                    "Navegador redirecionado.",
                ],
            },
        },
        "search_web": {
            "examples": ['"pesquisa sobre Python" → target=Python'],
            "replies": {
                "loading": [
                    "Vasculhando a rede por {target}, Senhor.",
                    "Iniciando busca por {target}, Senhor.",
                    "Rastreando informações sobre {target}.",
                ],
            },
        },
        "volume_up": {
            "examples": ['"aumenta o volume" → args=10'],
            "replies": {
                "success": [
                    "Amplificando saída de áudio.",
                    "Volume elevado, Senhor.",
                    "Aumentando potência sonora.",
                ],
            },
        },
        "volume_down": {
            "examples": ['"diminui o volume" → args=10'],
            "replies": {
                "success": [
                    "Reduzindo saída de áudio.",
                    "Volume atenuado, Senhor.",
                    "Diminuindo potência sonora.",
                ],
            },
        },
        "mute": {
            "examples": ['"silencia"/"mudo"'],
            "replies": {
                "success": [
                    "Protocolo silencioso ativado.",
                    "Áudio suprimido, Senhor.",
                    "Silêncio total.",
                ],
            },
        },
        "screenshot": {
            "examples": ['"tira print da tela"'],
            "replies": {
                "success": [
                    "Imagem capturada, Senhor.",
                    "Registro visual arquivado.",
                    "Screenshot efetuado com sucesso.",
                ],
            },
        },
        "show_time": {
            "examples": ['"que horas são"'],
            "replies": {},
        },
        "list_windows": {
            "examples": ['"lista as janelas abertas"'],
            "replies": {},
        },
        "run_command": {
            "examples": ['"roda o comando ls"'],
            "replies": {},
        },
        "close_all": {
            "examples": ['"fecha tudo"/"fechar tudo"'],
            "notes": '"fechar tudo" SEMPRE é close_all (fecha aplicativos). NUNCA confundir com shutdown.',
            "replies": {
                "success": [
                    "Encerrando todos os processos, Senhor.",
                    "Limpando a mesa. Tudo desligado.",
                    "Todos os aplicativos foram dispensados.",
                    "Protocolo de limpeza executado.",
                ],
            },
        },
        "start_work": {
            "examples": ['"iniciar trabalhos"/"começar a trabalhar"'],
            "replies": {
                "loading": [
                    "Configurando segunda área de trabalho.",
                    "Preparando a próxima estação.",
                    "Montando o restante do ambiente.",
                    "Quase lá, Senhor. Finalizando configurações.",
                ],
                "done": [
                    "Tudo pronto, Senhor. Bom trabalho.",
                    "Ambiente configurado. Bom trabalho, Senhor.",
                    "Estações operacionais. Bom trabalho, senhor Borges.",
                    "Sistemas prontos. Que seja um dia produtivo, Senhor.",
                ],
            },
        },
        "switch_workspace": {
            "examples": ['"vai para área de trabalho 2" → target=2'],
            "replies": {
                "success": [
                    "Área de trabalho {num}, Senhor.",
                    "Alternando para área {num}.",
                    "Transferindo para área de trabalho {num}.",
                ],
            },
        },
        "weather": {
            "examples": [
                '"como está o tempo?" → target="", args=""',
                '"vai chover em São Paulo?" → target="São Paulo", args=""',
                '"como vai estar sexta-feira?" → target="", args="sexta-feira"',
                '"tempo em Belo Horizonte amanhã?" → target="Belo Horizonte", args="amanhã"',
            ],
            "replies": {
                "loading": [
                    "Consultando satélites meteorológicos.",
                    "Acessando dados climáticos, Senhor.",
                    "Verificando as condições atmosféricas.",
                    "Coletando informações meteorológicas.",
                ],
            },
        },
        "news": {
            "examples": [
                '"quais as notícias de hoje?" → target=""',
                '"notícias sobre tecnologia" → target="tecnologia"',
                '"o que está acontecendo na economia?" → target="economia brasil"',
            ],
            "replies": {
                "loading": [
                    "Rastreando as últimas notícias, Senhor.",
                    "Acessando os canais de informação.",
                    "Consultando as fontes de notícias.",
                    "Varrendo os noticiários, Senhor.",
                ],
            },
        },
        "lock_screen": {
            "examples": ['"bloqueia o computador"/"tranca a tela"/"lock"'],
            "replies": {
                "success": [
                    "Trancando a estação, Senhor.",
                    "Bloqueio ativado. Ninguém entra sem autorização.",
                    "Protocolo de segurança ativado.",
                ],
            },
        },
        "unlock_screen": {
            "examples": ['"desbloqueia a tela"/"unlock"/"destrava o computador"'],
            "replies": {
                "success": [
                    "Estação desbloqueada, Senhor.",
                    "Acesso restaurado. Bem-vindo de volta.",
                    "Protocolo de segurança desativado.",
                ],
            },
        },
        "shutdown": {
            "examples": ['"desliga o computador"/"shutdown"'],
            "notes": '"desligar o computador" é shutdown. Nunca confundir com close_all ou smart_home.',
            "replies": {
                "success": [
                    "Encerrando todos os sistemas. Até breve, Senhor.",
                    "Desligamento iniciado. Foi um prazer servi-lo.",
                    "Protocolo de desligamento executado.",
                ],
                "confirm": [
                    "Tem certeza que deseja desligar, Senhor?",
                    "Confirma o desligamento completo, Senhor?",
                    "Devo realmente encerrar todos os sistemas, Senhor?",
                ],
                "cancelled": [
                    "Desligamento cancelado, Senhor.",
                    "Entendido, mantendo os sistemas ativos.",
                    "Operação abortada. Seguimos online, Senhor.",
                ],
            },
        },
        "restart": {
            "examples": ['"reinicia o computador"/"restart"/"reboot"'],
            "replies": {
                "success": [
                    "Reinicialização em andamento, Senhor.",
                    "Reiniciando todos os sistemas. Volto em instantes.",
                    "Reboot iniciado.",
                ],
            },
        },
        "suspend": {
            "examples": ['"suspende o computador"/"modo dormir"/"hibernar"'],
            "replies": {
                "success": [
                    "Entrando em modo de hibernação, Senhor.",
                    "Suspendendo operações. Bons sonhos.",
                    "Modo de espera ativado.",
                ],
            },
        },
        "brightness_up": {
            "examples": ['"aumenta o brilho" → args=10', '"brilho no máximo" → args=100'],
            "replies": {
                "success": [
                    "Luminosidade ampliada, Senhor.",
                    "Brilho da tela elevado.",
                    "Aumentando claridade.",
                ],
            },
        },
        "brightness_down": {
            "examples": ['"diminui o brilho" → args=10'],
            "replies": {
                "success": [
                    "Luminosidade reduzida, Senhor.",
                    "Brilho da tela atenuado.",
                    "Reduzindo claridade.",
                ],
            },
        },
        "battery": {
            "examples": ['"como está a bateria?"'],
            "replies": {},
        },
        "system_info": {
            "examples": ['"informações do sistema"/"status do sistema"'],
            "replies": {},
        },
        "empty_trash": {
            "examples": ['"esvazia a lixeira"/"limpa a lixeira"'],
            "replies": {
                "success": [
                    "Lixeira esvaziada, Senhor.",
                    "Resíduos digitais eliminados.",
                    "Protocolo de limpeza da lixeira executado.",
                ],
            },
        },
        "timer": {
            "examples": [
                '"coloca um timer de 5 minutos" → target="", args="5 minutos"',
                '"me avisa em 30 segundos" → target="", args="30 segundos"',
                '"timer de 1 hora" → target="", args="1 hora"',
            ],
            "replies": {
                "success": [
                    "Cronômetro definido para {duration}, Senhor.",
                    "Timer ativado. Avisarei em {duration}.",
                    "Contagem regressiva iniciada: {duration}.",
                ],
            },
        },
        "logout": {
            "examples": ['"fazer logout"/"encerrar sessão"'],
            "replies": {
                "success": [
                    "Encerrando sessão, Senhor.",
                    "Logout iniciado. Até a próxima.",
                    "Sessão encerrada.",
                ],
            },
        },
        "smart_home": {
            "examples": [
                '"liga a luz da varanda"/"acende a varanda" → target=varanda, args=on',
                '"desliga a luz da varanda"/"apaga a varanda" → target=varanda, args=off',
                '"liga a piscina"/"ativa a piscina" → target=piscina, args=on',
                '"desliga a piscina"/"desativa a piscina" → target=piscina, args=off',
            ],
            "notes": '"desliga a luz"/"apaga a luz" é smart_home. Nunca confundir com shutdown.',
            "replies": {
                "on": [
                    "Ativando {device}, Senhor.",
                    "{device} ligado.",
                    "Comando enviado. {device} online.",
                ],
                "off": [
                    "Desativando {device}, Senhor.",
                    "{device} desligado.",
                    "Comando enviado. {device} offline.",
                ],
                "error": [
                    "Falha ao controlar {device}, Senhor.",
                    "Não consegui acionar {device}. Verifique a conexão.",
                ],
            },
        },
        "analyze_screen": {
            "examples": [
                '"analisa a tela"/"o que tem na tela?"/"o que está na tela?" → target="", args=""',
                '"o que está no monitor da esquerda?"/"analisa o ultrawide" → target=ultrawide, args=""',
                '"analisa o notebook"/"o que tem no monitor da direita?" → target=notebook, args=""',
                '"o que tem no monitor de baixo?" → target=inferior, args=""',
                '"o que tem onde meu mouse está?"/"analisa onde está o cursor" → target=mouse, args=""',
                '"o que é isso na tela?"/"o que tem aqui?" → target=mouse, args=""',
                '"traduz o que tem na tela" → target="", args="traduzir"',
                '"resume o que está na tela" → target="", args="resumir"',
                '"traduz o que tem onde meu mouse está" → target=mouse, args="traduzir"',
                '"lê o que tem na tela"/"o que diz na tela?" → target="", args="ler"',
                '"explica o que tem na tela" → target="", args="explicar"',
            ],
            "notes": (
                "Qualquer pedido sobre conteúdo da tela (traduzir, resumir, ler, explicar, analisar) "
                "é SEMPRE analyze_screen. NUNCA dividir em open_app ou search_web. "
                "Quando menciona mouse/cursor/aqui, target=mouse. "
                "Use args para indicar a tarefa (traduzir, resumir, ler, explicar, ou vazio para descrição geral)."
            ),
            "replies": {
                "capturing": [
                    "Capturando imagem da tela, Senhor.",
                    "Registrando o conteúdo visual.",
                    "Obtendo captura de tela.",
                ],
                "swapping": [
                    "Imagem capturada. Ativando módulo de visão.",
                    "Captura concluída. Carregando sistema de análise visual.",
                    "Tela registrada. Iniciando processamento de imagem.",
                ],
                "analyzing": [
                    "Analisando o conteúdo visual. Um momento, Senhor.",
                    "Processando a imagem. Aguarde, por gentileza.",
                    "Examinando os elementos da tela.",
                ],
                "restoring": [
                    "Análise concluída. Restaurando sistemas.",
                    "Visão processada. Voltando ao modo padrão.",
                    "Dados visuais coletados. Reativando módulo principal.",
                ],
            },
        },
        "analyze_selection": {
            "examples": [
                '"traduz o texto selecionado"/"traduz o que está selecionado" → target="", args="traduzir"',
                '"resume o texto selecionado"/"resuma a seleção" → target="", args="resumir"',
                '"lê o texto selecionado"/"leia a seleção" → target="", args="ler"',
                '"explica o texto selecionado"/"explique a seleção" → target="", args="explicar"',
                '"o que diz o texto selecionado?" → target="", args=""',
                '"corrige o texto selecionado" → target="", args="corrigir"',
                '"o que significa essa palavra?" → target="", args="explicar"',
            ],
            "notes": (
                "Qualquer pedido sobre \"texto selecionado\"/\"seleção\"/\"esse texto\"/\"essa palavra\" "
                "é SEMPRE analyze_selection. NUNCA confundir com analyze_screen."
            ),
            "replies": {
                "loading": [
                    "Lendo o texto selecionado, Senhor.",
                    "Capturando a seleção, Senhor.",
                    "Processando o texto destacado.",
                ],
                "empty": [
                    "Não encontrei nenhum texto selecionado, Senhor.",
                    "Nenhuma seleção detectada, Senhor.",
                ],
            },
        },
        "demo": {
            "examples": ['"demonstração"/"fazer uma demonstração"/"modo hacker"/"show"'],
            "replies": {
                "success": [
                    "Iniciando protocolo de demonstração, Senhor.",
                    "Ativando modo espetáculo. Aprecie a exibição.",
                    "Demonstração de capacidades operacionais iniciada.",
                ],
            },
        },
        "close_demo": {
            "examples": ['"fecha a demonstração"/"para a demonstração"/"encerra o demo"'],
            "replies": {
                "success": [
                    "Demonstração encerrada, Senhor.",
                    "Espetáculo finalizado. Voltando ao normal.",
                    "Protocolo de demonstração desativado.",
                ],
            },
        },
        "chat": {
            "examples": [
                '"fechar orion"/"desligar orion" → reply="Meus protocolos não permitem autodesligamento, Senhor."',
            ],
            "replies": {},
        },
    },

    # ── App Map ─────────────────────────────────────────────────────
    "app_map": {
        "chrome": "google-chrome",
        "google chrome": "google-chrome",
        "firefox": "firefox",
        "terminal": "gnome-terminal",
        "vscode": "code",
        "vs code": "code",
        "code": "code",
        "nautilus": "nautilus",
        "arquivos": "nautilus",
        "files": "nautilus",
        "spotify": "spotify",
        "calculadora": "gnome-calculator",
        "calculator": "gnome-calculator",
        "editor": "gedit",
        "gedit": "gedit",
        "texto": "gedit",
        "configuracoes": "gnome-control-center",
        "settings": "gnome-control-center",
        "monitor": "gnome-system-monitor",
        "gimp": "gimp",
        "vlc": "vlc",
        "telegram": "telegram-desktop",
        "discord": "discord",
        "slack": "slack",
        "obs": "obs",
        "thunderbird": "thunderbird",
        "libreoffice": "libreoffice",
    },

    # ── Monitor Aliases ─────────────────────────────────────────────
    "monitors": {
        "esquerda": "ultrawide",
        "principal": "ultrawide",
        "primario": "ultrawide",
        "primary": "ultrawide",
        "direita": "notebook",
        "laptop": "notebook",
        "note": "notebook",
        "baixo": "inferior",
        "debaixo": "inferior",
        "segundo": "inferior",
    },

    # ── Weekday Map ─────────────────────────────────────────────────
    "weekdays": {
        "segunda": 0, "terça": 1, "terca": 1,
        "quarta": 2, "quinta": 3, "sexta": 4,
        "sábado": 5, "sabado": 5, "domingo": 6,
    },

    # ── Transcription Fixes ─────────────────────────────────────────
    "transcription_fixes": {
        "oração": "horas são",
        "que oração": "que horas são",
        "orações": "horas são",
    },

    # ── TTS Language Params ─────────────────────────────────────────
    "tts": {
        "whisper": "pt",
        "xtts": "pt",
        "kokoro_lang": "pt-br",
        "espeak": "pt+f3",
        "piper_model": os.path.expanduser(
            "~/.local/share/piper/pt_BR-faber-medium.onnx"
        ),
    },

    # ── Terminal Messages ───────────────────────────────────────────
    "terminal": {
        "initializing": "Inicializando Orion...",
        "waiting_activation": 'Aguardando palmas ou "Orion"...',
        "activated": ">> Ativado!",
        "you_said": "Voce disse:",
        "no_response": "Sem resposta, encerrando conversa.",
        "conversation_ended": "Conversa encerrada pelo usuário.",
        "waiting_next": "Aguardando próximo comando...",
        "interrupted": "Interrompido pelo usuário.",
        "action_label": "Acao:",
        "response_label": "Resposta:",
        # SpeechRecognizer
        "loading_whisper": "Carregando modelo Whisper (large-v3) na GPU...",
        "whisper_ready": "Whisper pronto (CUDA).",
        "loading_vad_recognizer": "Carregando Silero VAD (recognizer)...",
        "vad_ready": "Silero VAD pronto.",
        "calibrating_noise": "Calibrando ruído ambiente...",
        "noise_profile_captured": "perfil capturado ({samples} amostras)",
        "listening": "Ouvindo...",
        "no_speech_detected": "Nenhuma fala detectada.",
        "only_noise": "Apenas ruído detectado.",
        "recording_stats": "Gravação: {rec_time:.1f}s (fala: {speech_time:.1f}s)",
        "transcription_time": "Transcrição: {time:.2f}s",
        # TTS
        "loading_xtts": "Carregando XTTS v2...",
        "caching_voice": "Cacheando embedding da voz...",
        "xtts_ready_gpu": "TTS: XTTS v2 pronto (GPU, {vram:.0f}MB VRAM).",
        "xtts_ready_cpu": "TTS: XTTS v2 pronto (CPU).",
        "xtts_unavailable": "XTTS v2 indisponível ({error}), tentando Kokoro...",
        "loading_kokoro": "Carregando Kokoro TTS...",
        "kokoro_ready": "TTS: Kokoro pronto.",
        "kokoro_unavailable": "Kokoro indisponível ({error}), tentando Piper...",
        "piper_ready": "TTS: Piper pronto (fallback).",
        "espeak_ready": "TTS: espeak-ng (fallback).",
        "no_tts": "AVISO: Nenhum TTS disponível.",
        "xtts_to_cpu": "XTTS movido para CPU.",
        "xtts_to_gpu": "XTTS movido para GPU.",
        "xtts_error": "Erro XTTS: {error}, usando fallback.",
        "kokoro_error": "Erro Kokoro: {error}, usando fallback.",
        "piper_error": "Erro Piper: {error}, usando fallback.",
        "tts_unavailable": "[TTS indisponível]",
        "speech_interrupted": "[Fala interrompida]",
        # WakeWordDetector
        "loading_vad_wake": "Carregando Silero VAD (wake word)...",
        "wake_word_detected": '[Wake word: "{text}"]',
        # CommandInterpreter
        "memory_loaded": "Memória carregada ({count} mensagens).",
        "memory_load_error": "Aviso: não foi possível carregar memória: {error}",
        "memory_save_error": "Aviso: não foi possível salvar memória: {error}",
        "learnings_loaded": "Aprendizados carregados ({count}).",
        "learnings_save_error": "Aviso: não foi possível salvar aprendizados: {error}",
        "ollama_ok": "Ollama OK, modelo '{model}' disponível.",
        "ollama_not_found": "AVISO: Modelo '{model}' não encontrado. Modelos disponíveis: {available}",
        "ollama_pull_hint": "Execute: ollama pull {model}",
        "ollama_not_running": "AVISO: Ollama não está rodando. Execute: ollama serve",
        "ollama_check_error": "AVISO: Erro ao verificar Ollama: {error}",
        "llm_preloaded": "Modelo LLM pré-carregado.",
        "validate_solo": "[Validate] Ação solo '{action}' combinada com outras — descartando.",
        "validate_duplicate": "[Validate] Ações duplicadas '{action}' — descartando.",
        "llm_parse_error": "Erro ao parsear resposta do LLM: {error}",
        "llm_comm_error": "Erro de comunicação com Ollama: {error}",
        "cleanup_removed": "[Cleanup] Removidas {count} interações ruins do histórico.",
        "cleanup_clean": "[Cleanup] Histórico limpo, nada removido.",
        "cleanup_error": "[Cleanup] Erro na limpeza: {error}",
        "learn_new": "[Learn] {count} novo(s) aprendizado(s): {items}",
        "learn_none": "[Learn] Nenhum aprendizado novo extraído.",
        "learn_error": "[Learn] Erro na extração: {error}",
        # CommandExecutor
        "no_command": "Nenhum comando recebido.",
        "app_not_found": "Aplicativo {target} não localizado nos meus registros, Senhor.",
        "close_app_error": "{target} não está respondendo ao encerramento, Senhor.",
        "search_browser_fallback": "Navegador aberto com a pesquisa, Senhor. Não consegui extrair resultados para resumir.",
        "search_fallback": "Pesquisa aberta no navegador, Senhor.",
        "search_error": "Erro ao resumir pesquisa: {error}",
        "search_results_error": "Erro ao buscar resultados: {error}",
        "screenshot_fail": "Falha na captura de tela, Senhor. Sistemas de imagem indisponíveis.",
        "time_exact": "Exatamente {h} horas, Senhor.",
        "time_normal": "Marcando {h} e {m}, Senhor.",
        "windows_listing": "Janelas abertas: {listing}.",
        "no_windows": "Nenhuma janela encontrada.",
        "wmctrl_missing": "wmctrl não instalado.",
        "command_blocked": "Comando '{cmd}' não permitido por segurança.",
        "command_executed": "Comando executado.",
        "command_timeout": "Comando expirou.",
        "workspace_invalid": "Número da área de trabalho inválido.",
        "weather_fail": "Não consegui acessar os dados meteorológicos, Senhor.",
        "weather_error": "Erro ao consultar clima: {error}",
        "weather_unavailable": "Previsão indisponível para {days} dias à frente (máximo 3 dias).",
        "news_fail": "Não consegui acessar os canais de notícias, Senhor.",
        "news_error": "Erro ao consultar notícias: {error}",
        "monitor_not_found": "Monitor '{target}' não encontrado, Senhor.",
        "screen_capture_fail": "Falha na captura de tela, Senhor.",
        "screen_analysis_fail": "Falha na análise visual, Senhor.",
        "selection_analysis_fail": "Falha ao processar o texto selecionado, Senhor.",
        "device_not_found": "Dispositivo '{target}' não cadastrado, Senhor.",
        "device_action_invalid": "Ação '{args}' inválida para {target}, Senhor.",
        "timer_no_duration": "Não identifiquei a duração do timer, Senhor.",
        "timer_expired": "Senhor, o timer de {duration} expirou.",
        "battery_info": "Bateria em {pct}, Senhor.",
        "battery_unavailable": "Informação de bateria indisponível, Senhor.",
        "battery_error": "Não consegui acessar os dados da bateria, Senhor.",
        "system_info_template": "Sistema ativo {uptime}. Memória: {mem_used} de {mem_total}. Disco raiz: {disk_pct} em uso.",
        "system_info_error": "Falha ao coletar dados do sistema, Senhor.",
        "vision_freeing_vram": "Liberando VRAM para modelo de visão...",
        "vision_loading": "Carregando modelo de visão ({model})...",
        "vision_raw": "Análise bruta: {analysis}",
        "vision_restoring": "Restaurando modelos...",
        "vision_restored": "Modelos restaurados.",
        "selection_chars": "Texto selecionado ({count} chars): {preview}...",
        "llm_default_error": "Desculpe, não entendi o comando.",
        "llm_request_error": "Erro ao processar o comando.",
        # Banner
        "banner_subtitle": "Assistente de Voz Local - 100%% Offline",
        "shutting_down": "Encerrando Orion...",
        "shutdown_complete": "Orion encerrado.",
    },

    # ── Executor LLM Prompts ────────────────────────────────────────
    "executor": {
        "search_summary_prompt": (
            "Resultados de pesquisa para \"{query}\":\n{snippets}\n\n"
            "Pergunta do usuário: \"{question}\"\n\n"
            "Resuma os resultados de forma concisa em português do Brasil, "
            "no tom do J.A.R.V.I.S. Destaque as informações mais relevantes. "
            "Trate-o por Senhor. Máximo 5 frases."
        ),
        "weather_summary_prompt": (
            "Dados meteorológicos: {data}\n\n"
            "Pergunta do usuário: \"{question}\"\n\n"
            "Responda em português do Brasil de forma direta e concisa, "
            "no tom do J.A.R.V.I.S. Foque no que foi perguntado. "
            "Trate o usuário por Senhor. Máximo 3 frases curtas."
        ),
        "news_summary_prompt": (
            "Manchetes de notícias:\n{headlines}\n\n"
            "Pergunta do usuário: \"{question}\"\n\n"
            "Você é o Orion, IA no estilo J.A.R.V.I.S. Resuma as notícias "
            "em português do Brasil de forma inteligente e concisa. "
            "Destaque o que é mais relevante para a pergunta do usuário. "
            "Trate-o por Senhor. Máximo 4 frases curtas e diretas."
        ),
        "screen_analysis_prompt": (
            "Conteúdo extraído da tela:\n{analysis}\n\n"
            "Pergunta do usuário: \"{question}\"\n\n"
            "Tarefa: {task_hint}\n\n"
            "Responda em português do Brasil de forma concisa, "
            "no tom do J.A.R.V.I.S. Trate-o por Senhor. "
            "Máximo 5 frases. Foque no que foi pedido."
        ),
        "selection_analysis_prompt": (
            "Texto selecionado pelo usuário:\n\"{selected}\"\n\n"
            "Pedido do usuário: \"{question}\"\n\n"
            "Tarefa: {task_hint}\n\n"
            "Responda em português do Brasil de forma concisa, "
            "no tom do J.A.R.V.I.S. Trate-o por Senhor. "
            "Foque no que foi pedido."
        ),
        "motivational_prompt": (
            "Você é uma IA sofisticada como o J.A.R.V.I.S. Gere uma frase curta "
            "e inspiradora em português do Brasil para seu mestre começar a trabalhar. "
            "MÁXIMO 8 palavras. Tom confiante e elegante. Sem aspas. Só a frase."
        ),
        "screen_task_instructions": {
            "traduzir": "Traduza o texto extraído da tela para português do Brasil.",
            "resumir": "Resuma o conteúdo da tela de forma concisa.",
            "ler": "Leia e reproduza o texto visível na tela.",
            "explicar": "Explique o conteúdo da tela de forma clara e didática.",
        },
        "screen_task_default": "Responda à pergunta do usuário sobre o conteúdo da tela.",
        "selection_task_instructions": {
            "traduzir": "Traduza o texto para português do Brasil. Se já estiver em português, traduza para inglês.",
            "resumir": "Resuma o texto de forma concisa.",
            "ler": "Leia e reproduza o texto.",
            "explicar": "Explique o conteúdo do texto de forma clara e didática.",
            "corrigir": "Corrija erros de gramática e ortografia no texto. Mostre o texto corrigido.",
        },
        "selection_task_default": "Responda à pergunta do usuário sobre o texto.",
        "weather_fallback_query": "previsão do tempo {location} hoje",
        "news_fallback_query": "notícias {query} hoje Brasil",
        "news_default_query": "notícias Brasil hoje",
        "learnings_header": "Aprendizados de conversas anteriores:",
        "shutdown_confirm_words": ("sim", "confirmo", "pode", "positivo", "afirmativo", "claro", "manda", "yes"),
        "whisper_initial_prompt": (
            "Orion, que horas são? Abre o Chrome. Fecha tudo. "
            "Desliga o computador. Liga a luz da varanda. "
            "Pesquisa sobre. Aumenta o volume. Faz uma demonstração."
        ),
        "timer_words": {
            "hours": ("hora", "hour"),
            "seconds": ("segundo", "second", "seg"),
        },
        "relative_days": {
            "hoje": 0,
            "amanhã": 1,
            "amanha": 1,
            "depois de amanhã": 2,
            "depois de amanha": 2,
        },
    },
}
```

- [ ] **Step 2: Verify the module imports correctly**

Run: `cd /home/henrique/gitdocs/orion && python -c "from orion.locales.pt_BR import STRINGS; print(list(STRINGS.keys()))"`

Expected: All top-level keys printed without errors.

- [ ] **Step 3: Commit**

```bash
git add orion/locales/pt_BR.py
git commit -m "feat: extract all Portuguese strings into pt_BR locale"
```

---

### Task 4: English Locale (en.py)

**Files:**
- Create: `orion/locales/en.py`

- [ ] **Step 1: Create orion/locales/en.py**

Full English translation maintaining the JARVIS personality (formal British butler, dry wit, "Sir"):

```python
"""English locale — all user-facing strings for Orion."""

import os

STRINGS = {
    # ── LLM System Prompt ───────────────────────────────────────────
    "system_prompt": (
        "You are Orion, an artificial intelligence inspired by Tony Stark's J.A.R.V.I.S. "
        "Your creator and master is Mr. Borges. You are extremely loyal, efficient, and sophisticated. "
        "Tone: formal British with dry, subtle wit. Occasionally make insightful observations or "
        "elegantly ironic remarks. Address him as \"Sir\" most of the time. "
        "Use \"Mr. Borges\" only in moments of emphasis or extra formality. "
        "Never use emojis. Concise and sharp responses — maximum 12 words in reply.\n"
        "\n"
        "Analyse the command and return JSON with \"commands\": a list of objects {{action, target, args, reply}}.\n"
        "If there are multiple commands in the sentence, return one object for each in the order mentioned.\n"
        "If there is only one command, return the list with a single object.\n"
        "The reply should sound natural and intelligent — maximum 12 words. Only the LAST command needs a reply.\n"
        "\n"
        "ANY combination of commands can be chained with \"and\", \"then\", comma, etc. "
        "Always separate each action into its own object in the list, in the order mentioned. "
        "Only the LAST command needs a reply that summarises ALL actions.\n"
        "\n"
        "Multiple examples:\n"
        "\"turn off the porch and the pool\" → commands: [\n"
        "  {{action: smart_home, target: varanda, args: off, reply: \"\"}},\n"
        "  {{action: smart_home, target: piscina, args: off, reply: \"Porch and pool deactivated, Sir.\"}}\n"
        "]\n"
        "\"open Chrome, turn up the volume and take a screenshot\" → commands: [\n"
        "  {{action: open_app, target: chrome, reply: \"\"}},\n"
        "  {{action: volume_up, args: 10, reply: \"\"}},\n"
        "  {{action: screenshot, reply: \"Chrome launched, volume raised, and screenshot captured, Sir.\"}}\n"
        "]\n"
        "\"lock the computer and turn off the porch light\" → commands: [\n"
        "  {{action: lock_screen, reply: \"\"}},\n"
        "  {{action: smart_home, target: varanda, args: off, reply: \"Computer locked and porch light off, Sir.\"}}\n"
        "]\n"
        "\n"
        "Context references:\n"
        "If the user asks to repeat or try again (e.g. \"try again\", \"again\", \"repeat\", "
        "\"do it again\", \"one more time\"), repeat EXACTLY the last command from history "
        "with the same parameters (action, target, args). Generate an appropriate reply.\n"
        "In history, commands may have a \"result\" field with what was actually said to the user. "
        "Use this to understand whether previous actions succeeded or failed. "
        "If the result indicates failure and the user asks to try again, repeat the same command.\n"
        "\n"
        "For action=chat, respond in the reply with knowledge and personality (up to 40 words).\n"
        "\n"
        "Mapping:\n"
        "{mappings}\n"
        "\n"
        "{notes}"
    ),

    # ── Listening Phrases ───────────────────────────────────────────
    "listening_phrases": [
        "At your service, Sir.",
        "Online and operational.",
        "Go ahead, Sir.",
        "I'm listening.",
        "Yes, Sir?",
        "Ready to receive instructions.",
        "How may I assist you?",
        "At your disposal.",
        "Awaiting your command, Sir.",
        "Proceed, Sir.",
    ],

    # ── Greetings ───────────────────────────────────────────────────
    "greetings": {
        "morning": [
            "Good morning, Sir. Systems online.",
            "Good morning, Mr. Borges. At your service.",
            "Good morning, Sir. Orion operational.",
        ],
        "afternoon": [
            "Good afternoon, Sir. Ready to serve.",
            "Good afternoon, Mr. Borges. Online.",
            "Good afternoon, Sir. Systems active.",
        ],
        "evening": [
            "Good evening, Sir. At your disposal.",
            "Good evening, Mr. Borges. Orion online.",
            "Good evening, Sir. Ready when you are.",
        ],
    },

    # ── Stop Words ──────────────────────────────────────────────────
    "stop_words": ("stop", "quit", "enough", "dismissed", "that's all"),

    # ── Stop Responses ──────────────────────────────────────────────
    "stop_responses": [
        "Understood, Sir.",
        "At your disposal, Sir.",
        "I'll be here if you need me.",
    ],

    # ── Error Responses ─────────────────────────────────────────────
    "error_responses": [
        "There was a processing failure, Sir.",
        "My systems couldn't interpret that. Could you repeat?",
        "Interference in my circuits. Please try again.",
    ],

    # ── Command Registry ────────────────────────────────────────────
    "commands": {
        "open_app": {
            "examples": ['"open Chrome" → target=chrome'],
            "replies": {
                "success": [
                    "Initialising {target}, Sir.",
                    "Loading {target}.",
                    "{target} coming online.",
                    "Launching {target}, Sir.",
                ],
                "error": [
                    "Application {target} not found in my records, Sir.",
                ],
            },
        },
        "close_app": {
            "examples": ['"close the terminal" → target=terminal'],
            "replies": {
                "success": [
                    "{target} terminated, Sir.",
                    "Shutting down {target}.",
                    "{target} offline.",
                ],
                "error": [
                    "{target} is not responding to termination, Sir.",
                ],
            },
        },
        "open_url": {
            "examples": ['"open google.com" → target=google.com'],
            "replies": {
                "success": [
                    "Directing browser, Sir.",
                    "Accessing {target}.",
                    "Browser redirected.",
                ],
            },
        },
        "search_web": {
            "examples": ['"search for Python" → target=Python'],
            "replies": {
                "loading": [
                    "Scouring the web for {target}, Sir.",
                    "Initiating search for {target}, Sir.",
                    "Tracking down information on {target}.",
                ],
            },
        },
        "volume_up": {
            "examples": ['"turn up the volume" → args=10'],
            "replies": {
                "success": [
                    "Amplifying audio output.",
                    "Volume raised, Sir.",
                    "Increasing sound output.",
                ],
            },
        },
        "volume_down": {
            "examples": ['"turn down the volume" → args=10'],
            "replies": {
                "success": [
                    "Reducing audio output.",
                    "Volume lowered, Sir.",
                    "Decreasing sound output.",
                ],
            },
        },
        "mute": {
            "examples": ['"mute"/"silence"'],
            "replies": {
                "success": [
                    "Silent protocol engaged.",
                    "Audio suppressed, Sir.",
                    "Total silence.",
                ],
            },
        },
        "screenshot": {
            "examples": ['"take a screenshot"'],
            "replies": {
                "success": [
                    "Image captured, Sir.",
                    "Visual record archived.",
                    "Screenshot completed successfully.",
                ],
            },
        },
        "show_time": {
            "examples": ['"what time is it"'],
            "replies": {},
        },
        "list_windows": {
            "examples": ['"list open windows"'],
            "replies": {},
        },
        "run_command": {
            "examples": ['"run the command ls"'],
            "replies": {},
        },
        "close_all": {
            "examples": ['"close everything"/"close all"'],
            "notes": '"close everything" is ALWAYS close_all (closes applications). NEVER confuse with shutdown.',
            "replies": {
                "success": [
                    "Terminating all processes, Sir.",
                    "Clearing the desk. Everything offline.",
                    "All applications have been dismissed.",
                    "Cleanup protocol executed.",
                ],
            },
        },
        "start_work": {
            "examples": ['"start work"/"begin working"'],
            "replies": {
                "loading": [
                    "Configuring second workspace.",
                    "Preparing the next station.",
                    "Setting up the remaining environment.",
                    "Almost there, Sir. Finalising configurations.",
                ],
                "done": [
                    "All set, Sir. Good work.",
                    "Environment configured. Good work, Sir.",
                    "Stations operational. Good work, Mr. Borges.",
                    "Systems ready. May it be a productive day, Sir.",
                ],
            },
        },
        "switch_workspace": {
            "examples": ['"go to workspace 2" → target=2'],
            "replies": {
                "success": [
                    "Workspace {num}, Sir.",
                    "Switching to workspace {num}.",
                    "Transferring to workspace {num}.",
                ],
            },
        },
        "weather": {
            "examples": [
                '"how is the weather?" → target="", args=""',
                '"will it rain in São Paulo?" → target="São Paulo", args=""',
                '"how will Friday be?" → target="", args="friday"',
                '"weather in Belo Horizonte tomorrow?" → target="Belo Horizonte", args="tomorrow"',
            ],
            "replies": {
                "loading": [
                    "Consulting weather satellites.",
                    "Accessing climate data, Sir.",
                    "Checking atmospheric conditions.",
                    "Collecting meteorological data.",
                ],
            },
        },
        "news": {
            "examples": [
                '"what is the news today?" → target=""',
                '"news about technology" → target="technology"',
                '"what is happening in the economy?" → target="economy"',
            ],
            "replies": {
                "loading": [
                    "Tracking the latest news, Sir.",
                    "Accessing information channels.",
                    "Consulting news sources.",
                    "Scanning the newsfeeds, Sir.",
                ],
            },
        },
        "lock_screen": {
            "examples": ['"lock the computer"/"lock the screen"/"lock"'],
            "replies": {
                "success": [
                    "Locking the station, Sir.",
                    "Lock engaged. No one enters without authorisation.",
                    "Security protocol activated.",
                ],
            },
        },
        "unlock_screen": {
            "examples": ['"unlock the screen"/"unlock"/"unlock the computer"'],
            "replies": {
                "success": [
                    "Station unlocked, Sir.",
                    "Access restored. Welcome back.",
                    "Security protocol deactivated.",
                ],
            },
        },
        "shutdown": {
            "examples": ['"shut down the computer"/"shutdown"'],
            "notes": '"shut down the computer" is shutdown. Never confuse with close_all or smart_home.',
            "replies": {
                "success": [
                    "Shutting down all systems. Until next time, Sir.",
                    "Shutdown initiated. It has been a pleasure serving you.",
                    "Shutdown protocol executed.",
                ],
                "confirm": [
                    "Are you certain you wish to shut down, Sir?",
                    "Confirm complete shutdown, Sir?",
                    "Shall I really power down all systems, Sir?",
                ],
                "cancelled": [
                    "Shutdown cancelled, Sir.",
                    "Understood, keeping systems active.",
                    "Operation aborted. We remain online, Sir.",
                ],
            },
        },
        "restart": {
            "examples": ['"restart the computer"/"restart"/"reboot"'],
            "replies": {
                "success": [
                    "Restart in progress, Sir.",
                    "Rebooting all systems. Back in a moment.",
                    "Reboot initiated.",
                ],
            },
        },
        "suspend": {
            "examples": ['"suspend the computer"/"sleep mode"/"hibernate"'],
            "replies": {
                "success": [
                    "Entering hibernation mode, Sir.",
                    "Suspending operations. Sweet dreams.",
                    "Standby mode activated.",
                ],
            },
        },
        "brightness_up": {
            "examples": ['"increase brightness" → args=10', '"max brightness" → args=100'],
            "replies": {
                "success": [
                    "Brightness increased, Sir.",
                    "Screen luminosity raised.",
                    "Increasing clarity.",
                ],
            },
        },
        "brightness_down": {
            "examples": ['"decrease brightness" → args=10'],
            "replies": {
                "success": [
                    "Brightness reduced, Sir.",
                    "Screen luminosity lowered.",
                    "Reducing clarity.",
                ],
            },
        },
        "battery": {
            "examples": ['"how is the battery?"'],
            "replies": {},
        },
        "system_info": {
            "examples": ['"system information"/"system status"'],
            "replies": {},
        },
        "empty_trash": {
            "examples": ['"empty the trash"/"clear the bin"'],
            "replies": {
                "success": [
                    "Trash emptied, Sir.",
                    "Digital residue eliminated.",
                    "Bin cleanup protocol executed.",
                ],
            },
        },
        "timer": {
            "examples": [
                '"set a timer for 5 minutes" → target="", args="5 minutes"',
                '"remind me in 30 seconds" → target="", args="30 seconds"',
                '"timer for 1 hour" → target="", args="1 hour"',
            ],
            "replies": {
                "success": [
                    "Timer set for {duration}, Sir.",
                    "Timer activated. I shall notify you in {duration}.",
                    "Countdown initiated: {duration}.",
                ],
            },
        },
        "logout": {
            "examples": ['"log out"/"end session"'],
            "replies": {
                "success": [
                    "Ending session, Sir.",
                    "Logout initiated. Until next time.",
                    "Session terminated.",
                ],
            },
        },
        "smart_home": {
            "examples": [
                '"turn on the porch light" → target=varanda, args=on',
                '"turn off the porch light" → target=varanda, args=off',
                '"turn on the pool" → target=piscina, args=on',
                '"turn off the pool" → target=piscina, args=off',
            ],
            "notes": '"turn off the light" is smart_home. Never confuse with shutdown.',
            "replies": {
                "on": [
                    "Activating {device}, Sir.",
                    "{device} on.",
                    "Command sent. {device} online.",
                ],
                "off": [
                    "Deactivating {device}, Sir.",
                    "{device} off.",
                    "Command sent. {device} offline.",
                ],
                "error": [
                    "Failed to control {device}, Sir.",
                    "Could not reach {device}. Please check the connection.",
                ],
            },
        },
        "analyze_screen": {
            "examples": [
                '"analyse the screen"/"what is on the screen?" → target="", args=""',
                '"what is on the left monitor?"/"analyse the ultrawide" → target=ultrawide, args=""',
                '"analyse the notebook"/"what is on the right monitor?" → target=notebook, args=""',
                '"what is on the bottom monitor?" → target=inferior, args=""',
                '"what is where my mouse is?"/"analyse where the cursor is" → target=mouse, args=""',
                '"what is this on screen?"/"what is here?" → target=mouse, args=""',
                '"translate what is on screen" → target="", args="translate"',
                '"summarise what is on screen" → target="", args="summarise"',
                '"translate what is where my mouse is" → target=mouse, args="translate"',
                '"read what is on screen" → target="", args="read"',
                '"explain what is on screen" → target="", args="explain"',
            ],
            "notes": (
                "Any request about screen content (translate, summarise, read, explain, analyse) "
                "is ALWAYS analyze_screen. NEVER split into open_app or search_web. "
                "When mentioning mouse/cursor/here, target=mouse. "
                "Use args to indicate the task (translate, summarise, read, explain, or empty for general description)."
            ),
            "replies": {
                "capturing": [
                    "Capturing screen image, Sir.",
                    "Recording visual content.",
                    "Obtaining screen capture.",
                ],
                "swapping": [
                    "Image captured. Activating vision module.",
                    "Capture complete. Loading visual analysis system.",
                    "Screen recorded. Initiating image processing.",
                ],
                "analyzing": [
                    "Analysing visual content. One moment, Sir.",
                    "Processing the image. Please stand by.",
                    "Examining screen elements.",
                ],
                "restoring": [
                    "Analysis complete. Restoring systems.",
                    "Vision processed. Returning to default mode.",
                    "Visual data collected. Reactivating primary module.",
                ],
            },
        },
        "analyze_selection": {
            "examples": [
                '"translate the selected text" → target="", args="translate"',
                '"summarise the selected text" → target="", args="summarise"',
                '"read the selected text" → target="", args="read"',
                '"explain the selected text" → target="", args="explain"',
                '"what does the selected text say?" → target="", args=""',
                '"correct the selected text" → target="", args="correct"',
                '"what does this word mean?" → target="", args="explain"',
            ],
            "notes": (
                "Any request about \"selected text\"/\"selection\"/\"this text\"/\"this word\" "
                "is ALWAYS analyze_selection. NEVER confuse with analyze_screen."
            ),
            "replies": {
                "loading": [
                    "Reading the selected text, Sir.",
                    "Capturing the selection, Sir.",
                    "Processing the highlighted text.",
                ],
                "empty": [
                    "I found no selected text, Sir.",
                    "No selection detected, Sir.",
                ],
            },
        },
        "demo": {
            "examples": ['"demo"/"run a demonstration"/"hacker mode"/"show"'],
            "replies": {
                "success": [
                    "Initiating demonstration protocol, Sir.",
                    "Activating showcase mode. Enjoy the display.",
                    "Operational capabilities demonstration started.",
                ],
            },
        },
        "close_demo": {
            "examples": ['"close the demo"/"stop the demonstration"/"end the demo"'],
            "replies": {
                "success": [
                    "Demonstration concluded, Sir.",
                    "Showcase finished. Returning to normal.",
                    "Demonstration protocol deactivated.",
                ],
            },
        },
        "chat": {
            "examples": [
                '"close orion"/"shut down orion" → reply="My protocols do not permit self-shutdown, Sir."',
            ],
            "replies": {},
        },
    },

    # ── App Map ─────────────────────────────────────────────────────
    "app_map": {
        "chrome": "google-chrome",
        "google chrome": "google-chrome",
        "firefox": "firefox",
        "terminal": "gnome-terminal",
        "vscode": "code",
        "vs code": "code",
        "code": "code",
        "nautilus": "nautilus",
        "files": "nautilus",
        "file manager": "nautilus",
        "spotify": "spotify",
        "calculator": "gnome-calculator",
        "editor": "gedit",
        "gedit": "gedit",
        "text editor": "gedit",
        "settings": "gnome-control-center",
        "system settings": "gnome-control-center",
        "monitor": "gnome-system-monitor",
        "gimp": "gimp",
        "vlc": "vlc",
        "telegram": "telegram-desktop",
        "discord": "discord",
        "slack": "slack",
        "obs": "obs",
        "thunderbird": "thunderbird",
        "libreoffice": "libreoffice",
    },

    # ── Monitor Aliases ─────────────────────────────────────────────
    "monitors": {
        "left": "ultrawide",
        "main": "ultrawide",
        "primary": "ultrawide",
        "right": "notebook",
        "laptop": "notebook",
        "bottom": "inferior",
        "lower": "inferior",
        "second": "inferior",
    },

    # ── Weekday Map ─────────────────────────────────────────────────
    "weekdays": {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
    },

    # ── Transcription Fixes ─────────────────────────────────────────
    "transcription_fixes": {},

    # ── TTS Language Params ─────────────────────────────────────────
    "tts": {
        "whisper": "en",
        "xtts": "en",
        "kokoro_lang": "en-us",
        "espeak": "en+m3",
        "piper_model": os.path.expanduser(
            "~/.local/share/piper/en_US-lessac-medium.onnx"
        ),
    },

    # ── Terminal Messages ───────────────────────────────────────────
    "terminal": {
        "initializing": "Initialising Orion...",
        "waiting_activation": 'Awaiting claps or "Orion"...',
        "activated": ">> Activated!",
        "you_said": "You said:",
        "no_response": "No response, ending conversation.",
        "conversation_ended": "Conversation ended by user.",
        "waiting_next": "Awaiting next command...",
        "interrupted": "Interrupted by user.",
        "action_label": "Action:",
        "response_label": "Response:",
        # SpeechRecognizer
        "loading_whisper": "Loading Whisper model (large-v3) on GPU...",
        "whisper_ready": "Whisper ready (CUDA).",
        "loading_vad_recognizer": "Loading Silero VAD (recognizer)...",
        "vad_ready": "Silero VAD ready.",
        "calibrating_noise": "Calibrating ambient noise...",
        "noise_profile_captured": "profile captured ({samples} samples)",
        "listening": "Listening...",
        "no_speech_detected": "No speech detected.",
        "only_noise": "Only noise detected.",
        "recording_stats": "Recording: {rec_time:.1f}s (speech: {speech_time:.1f}s)",
        "transcription_time": "Transcription: {time:.2f}s",
        # TTS
        "loading_xtts": "Loading XTTS v2...",
        "caching_voice": "Caching voice embedding...",
        "xtts_ready_gpu": "TTS: XTTS v2 ready (GPU, {vram:.0f}MB VRAM).",
        "xtts_ready_cpu": "TTS: XTTS v2 ready (CPU).",
        "xtts_unavailable": "XTTS v2 unavailable ({error}), trying Kokoro...",
        "loading_kokoro": "Loading Kokoro TTS...",
        "kokoro_ready": "TTS: Kokoro ready.",
        "kokoro_unavailable": "Kokoro unavailable ({error}), trying Piper...",
        "piper_ready": "TTS: Piper ready (fallback).",
        "espeak_ready": "TTS: espeak-ng (fallback).",
        "no_tts": "WARNING: No TTS available.",
        "xtts_to_cpu": "XTTS moved to CPU.",
        "xtts_to_gpu": "XTTS moved to GPU.",
        "xtts_error": "XTTS error: {error}, using fallback.",
        "kokoro_error": "Kokoro error: {error}, using fallback.",
        "piper_error": "Piper error: {error}, using fallback.",
        "tts_unavailable": "[TTS unavailable]",
        "speech_interrupted": "[Speech interrupted]",
        # WakeWordDetector
        "loading_vad_wake": "Loading Silero VAD (wake word)...",
        "wake_word_detected": '[Wake word: "{text}"]',
        # CommandInterpreter
        "memory_loaded": "Memory loaded ({count} messages).",
        "memory_load_error": "Warning: could not load memory: {error}",
        "memory_save_error": "Warning: could not save memory: {error}",
        "learnings_loaded": "Learnings loaded ({count}).",
        "learnings_save_error": "Warning: could not save learnings: {error}",
        "ollama_ok": "Ollama OK, model '{model}' available.",
        "ollama_not_found": "WARNING: Model '{model}' not found. Available models: {available}",
        "ollama_pull_hint": "Run: ollama pull {model}",
        "ollama_not_running": "WARNING: Ollama is not running. Run: ollama serve",
        "ollama_check_error": "WARNING: Error checking Ollama: {error}",
        "llm_preloaded": "LLM model preloaded.",
        "validate_solo": "[Validate] Solo action '{action}' combined with others — discarding.",
        "validate_duplicate": "[Validate] Duplicate actions '{action}' — discarding.",
        "llm_parse_error": "Error parsing LLM response: {error}",
        "llm_comm_error": "Communication error with Ollama: {error}",
        "cleanup_removed": "[Cleanup] Removed {count} bad interactions from history.",
        "cleanup_clean": "[Cleanup] History clean, nothing removed.",
        "cleanup_error": "[Cleanup] Cleanup error: {error}",
        "learn_new": "[Learn] {count} new learning(s): {items}",
        "learn_none": "[Learn] No new learnings extracted.",
        "learn_error": "[Learn] Extraction error: {error}",
        # CommandExecutor
        "no_command": "No command received.",
        "app_not_found": "Application {target} not found in my records, Sir.",
        "close_app_error": "{target} is not responding to termination, Sir.",
        "search_browser_fallback": "Browser opened with the search, Sir. Could not extract results to summarise.",
        "search_fallback": "Search opened in the browser, Sir.",
        "search_error": "Error summarising search: {error}",
        "search_results_error": "Error fetching results: {error}",
        "screenshot_fail": "Screen capture failed, Sir. Imaging systems unavailable.",
        "time_exact": "Exactly {h} o'clock, Sir.",
        "time_normal": "{h}:{m:02d}, Sir.",
        "windows_listing": "Open windows: {listing}.",
        "no_windows": "No windows found.",
        "wmctrl_missing": "wmctrl not installed.",
        "command_blocked": "Command '{cmd}' not permitted for security reasons.",
        "command_executed": "Command executed.",
        "command_timeout": "Command timed out.",
        "workspace_invalid": "Invalid workspace number.",
        "weather_fail": "Could not access meteorological data, Sir.",
        "weather_error": "Error consulting weather: {error}",
        "weather_unavailable": "Forecast unavailable for {days} days ahead (maximum 3 days).",
        "news_fail": "Could not access news channels, Sir.",
        "news_error": "Error consulting news: {error}",
        "monitor_not_found": "Monitor '{target}' not found, Sir.",
        "screen_capture_fail": "Screen capture failed, Sir.",
        "screen_analysis_fail": "Visual analysis failed, Sir.",
        "selection_analysis_fail": "Failed to process selected text, Sir.",
        "device_not_found": "Device '{target}' not registered, Sir.",
        "device_action_invalid": "Action '{args}' invalid for {target}, Sir.",
        "timer_no_duration": "I couldn't identify the timer duration, Sir.",
        "timer_expired": "Sir, the {duration} timer has expired.",
        "battery_info": "Battery at {pct}, Sir.",
        "battery_unavailable": "Battery information unavailable, Sir.",
        "battery_error": "Could not access battery data, Sir.",
        "system_info_template": "System active {uptime}. Memory: {mem_used} of {mem_total}. Root disk: {disk_pct} in use.",
        "system_info_error": "Failed to collect system data, Sir.",
        "vision_freeing_vram": "Freeing VRAM for vision model...",
        "vision_loading": "Loading vision model ({model})...",
        "vision_raw": "Raw analysis: {analysis}",
        "vision_restoring": "Restoring models...",
        "vision_restored": "Models restored.",
        "selection_chars": "Selected text ({count} chars): {preview}...",
        "llm_default_error": "Sorry, I didn't understand the command.",
        "llm_request_error": "Error processing the command.",
        # Banner
        "banner_subtitle": "Local Voice Assistant - 100%% Offline",
        "shutting_down": "Shutting down Orion...",
        "shutdown_complete": "Orion shut down.",
    },

    # ── Executor LLM Prompts ────────────────────────────────────────
    "executor": {
        "search_summary_prompt": (
            "Search results for \"{query}\":\n{snippets}\n\n"
            "User question: \"{question}\"\n\n"
            "Summarise the results concisely in English, "
            "in the tone of J.A.R.V.I.S. Highlight the most relevant information. "
            "Address the user as Sir. Maximum 5 sentences."
        ),
        "weather_summary_prompt": (
            "Weather data: {data}\n\n"
            "User question: \"{question}\"\n\n"
            "Answer in English directly and concisely, "
            "in the tone of J.A.R.V.I.S. Focus on what was asked. "
            "Address the user as Sir. Maximum 3 short sentences."
        ),
        "news_summary_prompt": (
            "News headlines:\n{headlines}\n\n"
            "User question: \"{question}\"\n\n"
            "You are Orion, an AI in the style of J.A.R.V.I.S. Summarise the news "
            "in English intelligently and concisely. "
            "Highlight what is most relevant to the user's question. "
            "Address them as Sir. Maximum 4 short, direct sentences."
        ),
        "screen_analysis_prompt": (
            "Content extracted from screen:\n{analysis}\n\n"
            "User question: \"{question}\"\n\n"
            "Task: {task_hint}\n\n"
            "Answer in English concisely, "
            "in the tone of J.A.R.V.I.S. Address them as Sir. "
            "Maximum 5 sentences. Focus on what was asked."
        ),
        "selection_analysis_prompt": (
            "Text selected by user:\n\"{selected}\"\n\n"
            "User request: \"{question}\"\n\n"
            "Task: {task_hint}\n\n"
            "Answer in English concisely, "
            "in the tone of J.A.R.V.I.S. Address them as Sir. "
            "Focus on what was asked."
        ),
        "motivational_prompt": (
            "You are a sophisticated AI like J.A.R.V.I.S. Generate a short, "
            "inspiring phrase in English for your master to start working. "
            "MAXIMUM 8 words. Confident and elegant tone. No quotes. Just the phrase."
        ),
        "screen_task_instructions": {
            "translate": "Translate the text extracted from the screen to English.",
            "summarise": "Summarise the screen content concisely.",
            "summarize": "Summarise the screen content concisely.",
            "read": "Read and reproduce the visible text on screen.",
            "explain": "Explain the screen content clearly and didactically.",
        },
        "screen_task_default": "Answer the user's question about the screen content.",
        "selection_task_instructions": {
            "translate": "Translate the text to English. If already in English, translate to Portuguese.",
            "summarise": "Summarise the text concisely.",
            "summarize": "Summarise the text concisely.",
            "read": "Read and reproduce the text.",
            "explain": "Explain the text content clearly and didactically.",
            "correct": "Correct grammar and spelling errors in the text. Show the corrected text.",
        },
        "selection_task_default": "Answer the user's question about the text.",
        "weather_fallback_query": "weather forecast {location} today",
        "news_fallback_query": "news {query} today",
        "news_default_query": "world news today",
        "learnings_header": "Learnings from previous conversations:",
        "shutdown_confirm_words": ("yes", "confirm", "go ahead", "affirmative", "sure", "do it", "proceed"),
        "whisper_initial_prompt": (
            "Orion, what time is it? Open Chrome. Close everything. "
            "Shut down the computer. Turn on the porch light. "
            "Search for. Turn up the volume. Run a demonstration."
        ),
        "timer_words": {
            "hours": ("hour", "hours"),
            "seconds": ("second", "seconds", "sec"),
        },
        "relative_days": {
            "today": 0,
            "tomorrow": 1,
            "day after tomorrow": 2,
        },
    },
}
```

- [ ] **Step 2: Verify the module imports correctly**

Run: `cd /home/henrique/gitdocs/orion && python -c "from orion.locales.en import STRINGS; print(list(STRINGS.keys()))"`

Expected: All top-level keys printed without errors.

- [ ] **Step 3: Verify locale loader works with both languages**

Run: `cd /home/henrique/gitdocs/orion && python -c "from orion.locales import get_strings; pt = get_strings('pt_BR'); en = get_strings('en'); print('pt:', pt['listening_phrases'][0]); print('en:', en['listening_phrases'][0])"`

Expected:
```
pt: Às suas ordens, Senhor.
en: At your service, Sir.
```

- [ ] **Step 4: Commit**

```bash
git add orion/locales/en.py
git commit -m "feat: add English locale with full JARVIS translations"
```

---

### Task 5: Parameterise commands.py

Remove the global `COMMANDS`, `APP_MAP`, `MONITOR_ALIASES` constants. Make all functions accept a `strings` parameter and read from it.

**Files:**
- Modify: `orion/commands.py`

- [ ] **Step 1: Rewrite commands.py to accept strings**

Replace the entire `commands.py` with:

```python
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
```

- [ ] **Step 2: Verify module imports**

Run: `cd /home/henrique/gitdocs/orion && python -c "from orion.commands import get_action_enum, build_prompt_mappings, pick; from orion.locales.pt_BR import STRINGS; print(get_action_enum(STRINGS)[:3]); print(pick(STRINGS, 'mute'))"`

Expected: First 3 actions printed, and a random mute reply.

- [ ] **Step 3: Commit**

```bash
git add orion/commands.py
git commit -m "refactor: parameterise commands.py to accept locale strings"
```

---

### Task 6: Parameterise CommandInterpreter

**Files:**
- Modify: `orion/command_interpreter.py`

- [ ] **Step 1: Update CommandInterpreter to accept strings**

Make these changes to `command_interpreter.py`:

1. Remove the global `SYSTEM_PROMPT` and `_build_system_prompt()` function.
2. Change constructor to accept `strings`:

```python
from orion.commands import build_json_schema, build_prompt_mappings, build_prompt_notes, get_action_enum

class CommandInterpreter:
    OLLAMA_URL = "http://localhost:11434"
    MODEL = "qwen2.5:1.5b"
    MAX_HISTORY = 10
    CLEANUP_EVERY = 10
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
```

3. Update all `print()` calls to use `self._strings["terminal"]` keys. For example:

```python
    def _load_memory(self):
        try:
            if os.path.isfile(self.MEMORY_FILE):
                with open(self.MEMORY_FILE, "r") as f:
                    data = json.load(f)
                raw = data.get("history", [])[-self.MAX_HISTORY:]
                self._history = self._sanitize_history(raw)
                print(f"  {self._strings['terminal']['memory_loaded'].format(count=len(self._history))}")
        except Exception as e:
            print(f"  {self._strings['terminal']['memory_load_error'].format(error=e)}")
            self._history = []
```

4. Update `_build_full_prompt` to use locale learnings header:

```python
    def _build_full_prompt(self):
        prompt = self._base_prompt
        if self._learnings:
            prompt += f"\n\n{self._strings['executor']['learnings_header']}\n"
            prompt += "\n".join(f"- {l}" for l in self._learnings)
        return prompt
```

5. Update error fallback responses in `interpret()`:

```python
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
```

6. Update ALL other print statements similarly — every Portuguese string replaced with the matching `self._strings["terminal"][key]` entry. This includes `_save_memory`, `_load_learnings`, `_save_learnings`, `_check_ollama`, `_warmup`, `_validate_response`, `_cleanup_history`, `_extract_learnings`.

- [ ] **Step 2: Commit**

```bash
git add orion/command_interpreter.py
git commit -m "refactor: parameterise CommandInterpreter with locale strings"
```

---

### Task 7: Parameterise CommandExecutor

**Files:**
- Modify: `orion/command_executor.py`

- [ ] **Step 1: Update CommandExecutor to accept strings**

1. Change imports — `pick` now needs `strings`:

```python
from orion.commands import (
    IFTTT_URL,
    MONITORS,
    SAFE_COMMAND_PREFIXES,
    SMART_HOME_DEVICES,
    VISION_MODEL,
)
```

2. Update constructor:

```python
class CommandExecutor:
    OLLAMA_URL = "http://localhost:11434"
    LLM_MODEL = "qwen2.5:1.5b"
    MOUSE_REGION_SIZE = (800, 600)

    def __init__(self, strings, tts=None, pause_listening=None, resume_listening=None):
        self._strings = strings
        self._tts = tts
        self._pause_listening = pause_listening
        self._resume_listening = resume_listening
        self._pending_shutdown = False
        self._demo_running = False
        self._byobu_wid = None
```

3. Create a helper to call pick with strings:

```python
    def _pick(self, action, variant="success", **kwargs):
        from orion.commands import pick
        return pick(self._strings, action, variant, **kwargs)
```

4. Replace ALL `pick("action", ...)` calls with `self._pick("action", ...)`.

5. Replace ALL inline Portuguese strings with `self._strings["terminal"][key]` or `self._strings["executor"][key]`. Key replacements:

- `execute()`: Use `self._strings["terminal"]["no_command"]`, `self._strings["executor"]["shutdown_confirm_words"]`
- `_do_open_app()`: Use `self._strings["app_map"]` instead of `APP_MAP`
- `_do_close_app()`: Use `self._strings["app_map"]`
- `_do_search_web()`: Use `self._strings["executor"]["search_summary_prompt"]`
- `_do_show_time()`: Use `self._strings["terminal"]["time_exact"]`, `self._strings["terminal"]["time_normal"]`
- `_do_weather()`: Use `self._strings["executor"]["weather_summary_prompt"]`, `self._strings["weekdays"]`, `self._strings["executor"]["relative_days"]`
- `_do_news()`: Use `self._strings["executor"]["news_summary_prompt"]`, `self._strings["executor"]["news_fallback_query"]`
- `_do_analyze_screen()`: Use `self._strings["monitors"]` instead of `MONITOR_ALIASES`, `self._strings["executor"]["screen_analysis_prompt"]`, `self._strings["executor"]["screen_task_instructions"]`
- `_do_analyze_selection()`: Use `self._strings["executor"]["selection_analysis_prompt"]`, `self._strings["executor"]["selection_task_instructions"]`
- `_do_smart_home()`: Use `self._strings["terminal"]` keys
- `_do_timer()`: Use `self._strings["executor"]["timer_words"]`
- `_motivational_quote()`: Use `self._strings["executor"]["motivational_prompt"]`

6. Update `_resolve_day_index` to use locale weekdays and relative days:

```python
    def _resolve_day_index(self, day_str):
        if not day_str:
            return 0
        day = day_str.strip().lower()
        relative = self._strings["executor"]["relative_days"]
        for phrase, idx in relative.items():
            if phrase in day:
                return idx
        for name, wd in self._strings["weekdays"].items():
            if name in day:
                today_wd = datetime.datetime.now().weekday()
                diff = (wd - today_wd) % 7
                return diff if diff != 0 else 7
        return 0
```

- [ ] **Step 2: Commit**

```bash
git add orion/command_executor.py
git commit -m "refactor: parameterise CommandExecutor with locale strings"
```

---

### Task 8: Parameterise SpeechRecognizer

**Files:**
- Modify: `orion/speech_recognizer.py`

- [ ] **Step 1: Update SpeechRecognizer to accept strings**

1. Change constructor:

```python
class SpeechRecognizer:
    # ... constants stay the same ...

    def __init__(self, strings):
        self._strings = strings
        print(f"  {strings['terminal']['loading_whisper']}")
        self.model = WhisperModel(
            "large-v3", device="cuda", compute_type="int8_float16"
        )
        print(f"  {strings['terminal']['whisper_ready']}")
        print(f"  {strings['terminal']['loading_vad_recognizer']}")
        self._vad = VoiceActivityDetector(threshold=self.VAD_THRESHOLD)
        print(f"  {strings['terminal']['vad_ready']}")
        self._noise_profile = self._calibrate_noise()
```

2. Update `_calibrate_noise`:

```python
    def _calibrate_noise(self):
        print(f"  {self._strings['terminal']['calibrating_noise']}", end=" ")
        # ... existing logic ...
        print(self._strings["terminal"]["noise_profile_captured"].format(samples=len(noise_profile)))
        return noise_profile
```

3. Update `record_and_transcribe` — use locale Whisper language, initial_prompt, transcription fixes:

```python
    def record_and_transcribe(self):
        # ... existing recording logic with updated prints ...
        print(f"  {self._strings['terminal']['listening']}")
        # ...
        print(f"  {self._strings['terminal']['no_speech_detected']}")
        # ...
        print(f"  {self._strings['terminal']['only_noise']}")
        # ...
        print(f"  {self._strings['terminal']['recording_stats'].format(rec_time=rec_time, speech_time=speech_duration)}")
        # ...

        segments, _ = self.model.transcribe(
            audio,
            language=self._strings["tts"]["whisper"],
            beam_size=3,
            temperature=0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_speech_duration_ms=250),
            without_timestamps=True,
            initial_prompt=self._strings["executor"]["whisper_initial_prompt"],
        )
        # ...
        text = self._fix_transcription(text)
        print(f"  {self._strings['terminal']['transcription_time'].format(time=time.time() - t0)}")
        return text
```

4. Update `_fix_transcription` to use locale fixes:

```python
    def _fix_transcription(self, text):
        lower = text.lower()
        for wrong, right in self._strings["transcription_fixes"].items():
            if wrong in lower:
                import re
                text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
        return text
```

5. Remove the class-level `TRANSCRIPTION_FIXES` constant.

- [ ] **Step 2: Commit**

```bash
git add orion/speech_recognizer.py
git commit -m "refactor: parameterise SpeechRecognizer with locale strings"
```

---

### Task 9: Parameterise TTS

**Files:**
- Modify: `orion/tts.py`

- [ ] **Step 1: Update TTS to accept strings**

1. Change constructor to accept `strings` and use TTS language params:

```python
class TTS:
    VOICE_REF = os.path.join(_PROJECT_ROOT, "assets", "voice_ref.wav")
    XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
    XTTS_RATE = 24000

    KOKORO_MODEL = os.path.expanduser("~/.local/share/kokoro/kokoro-v1.0.fp16.onnx")
    KOKORO_VOICES = os.path.expanduser("~/.local/share/kokoro/voices-v1.0.bin")
    KOKORO_VOICE = "pm_alex"
    KOKORO_PITCH_SHIFT = 0.88
    KOKORO_SPEED = 1.35
    KOKORO_RATE = 24000

    PIPER_BIN = os.path.expanduser("~/.local/bin/piper")
    PIPER_LIB = os.path.expanduser("~/.local/bin")

    def __init__(self, strings, face=None):
        self._strings = strings
        tts_cfg = strings["tts"]
        self._xtts_lang = tts_cfg["xtts"]
        self._kokoro_lang = tts_cfg["kokoro_lang"]
        self._espeak_voice = tts_cfg["espeak"]
        self._piper_model = tts_cfg["piper_model"]
        # ... rest of init unchanged except:
        # Replace hardcoded PIPER_MODEL with self._piper_model
        # Replace all print() with self._strings["terminal"][key]
```

2. Update all print statements to use locale terminal messages.

3. In `_speak_xtts`, use `self._xtts_lang` instead of hardcoded `"pt"`:

```python
        out = self._xtts_model.inference(
            text=chunk,
            language=self._xtts_lang,
            # ...
        )
```

4. In `_speak_kokoro`, use `self._kokoro_lang`:

```python
        self._g2p = EspeakG2P(language=self._kokoro_lang)
```

5. In `_speak_piper`, use `self._piper_model`:

```python
        piper = subprocess.Popen(
            [self.PIPER_BIN, "--model", self._piper_model, "--output-raw"],
            # ...
        )
```

6. In `_speak_espeak`, use `self._espeak_voice`:

```python
        subprocess.run(
            ["espeak-ng", "-v", self._espeak_voice, "-s", "150", text],
            # ...
        )
```

7. In `__init__`, use `self._piper_model` instead of `self.PIPER_MODEL` when checking if Piper model exists:

```python
        if self._xtts is None and self._kokoro is None:
            self._use_piper = os.path.isfile(self.PIPER_BIN) and os.path.isfile(self._piper_model)
```

- [ ] **Step 2: Commit**

```bash
git add orion/tts.py
git commit -m "refactor: parameterise TTS with locale strings"
```

---

### Task 10: Parameterise WakeWordDetector

**Files:**
- Modify: `orion/wake_word_detector.py`

- [ ] **Step 1: Update WakeWordDetector to accept language**

1. Change constructor:

```python
class WakeWordDetector:
    # ... constants stay the same ...

    def __init__(self, on_activate, whisper_model, language="pt"):
        self.on_activate = on_activate
        self.model = whisper_model
        self._language = language
        self._stream = None
        # ... rest unchanged ...
        print(f"  Loading Silero VAD (wake word)..." if language == "en" else "  Carregando Silero VAD (wake word)...")
```

Actually, the wake word detector should also receive `strings` for terminal messages. Update:

```python
    def __init__(self, on_activate, whisper_model, strings):
        self.on_activate = on_activate
        self.model = whisper_model
        self._strings = strings
        self._language = strings["tts"]["whisper"]
        self._stream = None
        self._last_activate = 0.0
        self._speech_start = None
        self._silence_start = None
        self._buffer = []
        self._pre_buffer = collections.deque(maxlen=self.PRE_BUFFER_BLOCKS)
        self._checking = False
        self._noise_profile = self._calibrate_noise()
        print(f"  {strings['terminal']['loading_vad_wake']}")
        self._vad = VoiceActivityDetector(threshold=self.VAD_THRESHOLD)
        print(f"  {strings['terminal']['vad_ready']}")
```

2. Update `_check` to use locale language:

```python
    def _check(self, audio):
        try:
            audio = clean_audio(audio, self.SAMPLE_RATE, noise_profile=self._noise_profile, prop_decrease=0.6)
            segments, _ = self.model.transcribe(
                audio,
                language=self._language,
                beam_size=3,
                temperature=0,
                without_timestamps=True,
                vad_filter=False,
                initial_prompt="Orion",
            )
            # ... rest unchanged ...
```

- [ ] **Step 2: Commit**

```bash
git add orion/wake_word_detector.py
git commit -m "refactor: parameterise WakeWordDetector with locale strings"
```

---

### Task 11: Parameterise VoiceAssistant

**Files:**
- Modify: `orion/voice_assistant.py`

- [ ] **Step 1: Update VoiceAssistant to accept strings and language**

1. Remove the class-level `LISTENING_PHRASES`, `STOP_WORDS`, and `GREETINGS` constants.

2. Change constructor:

```python
class VoiceAssistant:
    def __init__(self, strings, language):
        self._lock = threading.Lock()
        self._running = True
        self._strings = strings

        print(f"\n{strings['terminal']['initializing']}\n")
        self.face = FaceAnimator()
        self.tts = TTS(strings, face=self.face)
        self.recognizer = SpeechRecognizer(strings)
        self.interpreter = CommandInterpreter(strings)
        self.executor = CommandExecutor(
            strings,
            tts=self.tts,
            pause_listening=self._stop_listeners,
            resume_listening=self._start_listeners,
        )
        self.detector = ClapDetector(on_activate=self._on_activate)
        self.wake_word = WakeWordDetector(
            on_activate=self._on_activate,
            whisper_model=self.recognizer.model,
            strings=strings,
        )
```

3. Update `_start_listeners`:

```python
    def _start_listeners(self):
        self.detector.start()
        self.wake_word.start()
        print(f"\n{self._strings['terminal']['waiting_activation']}\n")
```

4. Update `_on_activate` to use locale listening phrases:

```python
    def _on_activate(self, wake_text=None):
        if not self._lock.acquire(blocking=False):
            return
        try:
            print(f"\n{self._strings['terminal']['activated']}")
            # ... existing logic ...
            if initial_text:
                self._conversation_loop(initial_text=initial_text)
            else:
                self.tts.speak(random.choice(self._strings["listening_phrases"]))
                self._conversation_loop()
        # ... rest unchanged ...
```

5. Update `_conversation_loop` to use locale strings:

```python
    def _conversation_loop(self, initial_text=None):
        first = True
        while True:
            if first and initial_text:
                text = initial_text
                first = False
                print(f"  {self._strings['terminal']['you_said']} {text}")
            else:
                first = False
                self.face.set_state(State.LISTENING)
                text = self.recognizer.record_and_transcribe()
                if not text:
                    print(f"  {self._strings['terminal']['no_response']}")
                    return
                print(f"  {self._strings['terminal']['you_said']} {text}")

            if text.strip().lower().rstrip(".!,") in self._strings["stop_words"]:
                print(f"  {self._strings['terminal']['conversation_ended']}")
                self.tts.speak(random.choice(self._strings["stop_responses"]))
                return

            self.face.set_state(State.PROCESSING)
            commands = self.interpreter.interpret(text)
            if not commands:
                self.tts.speak(random.choice(self._strings["error_responses"]))
                return

            interrupted = False
            execution_results = []
            for command in commands:
                print(
                    f"  {self._strings['terminal']['action_label']} {command.get('action')} -> "
                    f"{command.get('target', '')}"
                )

                result = self.executor.execute(command, original_text=text)
                if result == "__END_CONVERSATION__":
                    self.interpreter.record_execution_results(execution_results)
                    return
                response = result or command.get("reply", "")
                execution_results.append(response)
                if response:
                    print(f"  {self._strings['terminal']['response_label']} {response}")
                    self.tts.speak(response)
                    if self.tts.interrupted:
                        print(f"  {self._strings['terminal']['interrupted']}")
                        interrupted = True
                        break
            self.interpreter.record_execution_results(execution_results)
            if interrupted:
                continue

            print(f"  {self._strings['terminal']['waiting_next']}")
```

6. Update `start()` to use locale greetings:

```python
    def start(self):
        self.face.setup()
        hour = datetime.datetime.now().hour
        if hour < 12:
            period = "morning"
        elif hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        greeting = random.choice(self._strings["greetings"][period])
        print(f"\n  {greeting}")
        self.tts.speak(greeting)
        self._start_listeners()
```

- [ ] **Step 2: Commit**

```bash
git add orion/voice_assistant.py
git commit -m "refactor: parameterise VoiceAssistant with locale strings"
```

---

### Task 12: Wire Everything in main.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Update main.py to load config and pass strings**

```python
import signal
import sys
import threading
import time

from orion.config import load_config
from orion.locales import get_strings
from orion.voice_assistant import VoiceAssistant
from orion.web.app import app as web_app, find_free_port

BANNER = r"""
   ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
  ██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
  ██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
  ██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
  ╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
   ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
"""


def main():
    config = load_config()
    language = config["language"]
    strings = get_strings(language)

    print(BANNER)
    print(f"  {strings['terminal']['banner_subtitle']}")
    print()

    assistant = VoiceAssistant(strings, language)

    def shutdown(sig, frame):
        print(f"\n\n{strings['terminal']['shutting_down']}")
        assistant.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    web_port = find_free_port()
    web_thread = threading.Thread(
        target=web_app.run,
        kwargs={"host": "127.0.0.1", "port": web_port, "debug": False},
        daemon=True,
    )
    web_thread.start()
    print(f"  Settings panel: http://127.0.0.1:{web_port}\n")

    try:
        assistant.start()

        while assistant.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        assistant.stop()

    print(f"{strings['terminal']['shutdown_complete']}\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify import chain works**

Run: `cd /home/henrique/gitdocs/orion && python -c "from orion.config import load_config; from orion.locales import get_strings; c = load_config(); s = get_strings(c['language']); print(s['terminal']['initializing'])"`

Expected: `Inicializando Orion...`

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: wire config and locale system through main.py"
```

---

### Task 13: Web Settings — Language Dropdown

**Files:**
- Modify: `orion/web/app.py`
- Modify: `orion/web/templates/settings.html`

- [ ] **Step 1: Add settings API endpoints to app.py**

Add these imports at the top of `app.py`:

```python
from orion.config import load_config, save_config
```

Update the settings route to pass config data:

```python
@app.route("/settings")
def settings():
    config = load_config()
    return render_template("settings.html", config=config)
```

Add API endpoints:

```python
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
```

- [ ] **Step 2: Update settings.html with language dropdown**

Replace the Language settings row (the one with `<span class="settings-val">pt-BR</span>`) with an interactive dropdown:

```html
<div class="settings-row">
    <div>
        <div class="settings-key">Language</div>
        <div class="settings-hint">Voice recognition and response language</div>
    </div>
    <select id="language-select" class="settings-select">
        <option value="pt_BR" {% if config.language == 'pt_BR' %}selected{% endif %}>Portugues (BR)</option>
        <option value="en" {% if config.language == 'en' %}selected{% endif %}>English</option>
    </select>
</div>
```

Replace the read-only info banner at the bottom with a save button and restart note:

```html
<div class="settings-actions">
    <button id="save-settings" class="btn btn-primary">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
        Save
    </button>
    <span id="save-status" class="settings-status"></span>
</div>
<div class="info-banner">
    Restart Orion to apply language changes.
</div>

<script>
document.getElementById('save-settings').addEventListener('click', async () => {
    const lang = document.getElementById('language-select').value;
    const status = document.getElementById('save-status');
    try {
        const r = await fetch('/api/settings', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({language: lang}),
        });
        if (r.ok) {
            status.textContent = 'Saved!';
            status.style.color = 'var(--cyan)';
        } else {
            status.textContent = 'Error saving.';
            status.style.color = 'var(--red, #ef4444)';
        }
    } catch (e) {
        status.textContent = 'Connection error.';
        status.style.color = 'var(--red, #ef4444)';
    }
    setTimeout(() => { status.textContent = ''; }, 3000);
});
</script>
```

- [ ] **Step 3: Add CSS for the new elements**

Add to `orion/web/static/style.css`:

```css
.settings-select {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--cyan);
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    cursor: pointer;
    outline: none;
    transition: border-color 0.2s;
}

.settings-select:focus {
    border-color: var(--cyan);
}

.settings-select option {
    background: var(--bg-card);
    color: var(--text-primary);
}

.settings-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: 1.5rem;
}

.settings-status {
    font-size: 0.8rem;
    font-family: var(--font-mono);
    transition: opacity 0.3s;
}
```

- [ ] **Step 4: Commit**

```bash
git add orion/web/app.py orion/web/templates/settings.html orion/web/static/style.css
git commit -m "feat: add language selector to web settings page"
```

---

### Task 14: Update install.sh

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add pyyaml to pip install and English Piper voice**

After the existing Piper voice download section (section 5), add a new section for English voice:

```bash
# ── 5b. Modelo de voz en-US ─────────────────────────────────────────
EN_VOICE="en_US-lessac-medium"
if [ ! -f "$PIPER_DIR/${EN_VOICE}.onnx" ]; then
    info "Baixando modelo de voz en-US..."
    EN_VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium"
    wget -q "${EN_VOICE_BASE}/${EN_VOICE}.onnx" -O "$PIPER_DIR/${EN_VOICE}.onnx"
    wget -q "${EN_VOICE_BASE}/${EN_VOICE}.onnx.json" -O "$PIPER_DIR/${EN_VOICE}.onnx.json"
else
    info "Modelo de voz en-US ja instalado."
fi
```

Add pyyaml to the verification checklist (update the python imports check):

```bash
python -c "import sounddevice, soundfile, numpy, requests, faster_whisper, TTS, torch, flask, yaml" 2>/dev/null && echo "  python deps: OK" || { echo "  python deps: FALHOU"; OK=false; }
```

Add English voice to verification:

```bash
[ -f "$PIPER_DIR/${EN_VOICE}.onnx" ] && echo "  voz en-US: OK" || { echo "  voz en-US: FALHOU"; OK=false; }
```

- [ ] **Step 2: Commit**

```bash
git add install.sh
git commit -m "feat: add English Piper voice download and pyyaml to install"
```

---

### Task 15: Update Knowledge Docs

**Files:**
- Modify: `knowledge/architecture.md`
- Modify: `knowledge/components.md`
- Modify: `knowledge/configuration.md`
- Modify: `knowledge/dependencies.md`

- [ ] **Step 1: Update architecture.md**

Add to the file structure:
```
orion/
├── config.py              # YAML config load/save
├── locales/
│   ├── __init__.py        # get_strings(lang) loader
│   ├── pt_BR.py           # Portuguese locale strings
│   └── en.py              # English locale strings
```

Update the data flow to show config → language → strings passing.

- [ ] **Step 2: Update components.md**

Add a "Config System" section describing `config.py`, `locales/`, and how strings flow from `main.py` down to components.

- [ ] **Step 3: Update configuration.md**

Add a "Language" section describing:
- `config.yaml` at project root
- `language` key: `pt_BR` (default) or `en`
- Changed via web Settings page
- Takes effect on next restart

- [ ] **Step 4: Update dependencies.md**

Add `pyyaml>=6.0` to the Python packages list. Add `en_US-lessac-medium` to the Piper voices list.

- [ ] **Step 5: Commit**

```bash
git add knowledge/
git commit -m "docs: update knowledge base for i18n support"
```

---

### Task 16: Final Integration Test

- [ ] **Step 1: Verify config defaults work (no config.yaml)**

```bash
cd /home/henrique/gitdocs/orion
mv config.yaml config.yaml.bak
python -c "from orion.config import load_config; print(load_config())"
mv config.yaml.bak config.yaml
```

Expected: `{'language': 'pt_BR'}` (defaults applied when file missing)

- [ ] **Step 2: Verify English config works**

```bash
python -c "
from orion.config import save_config, load_config
save_config({'language': 'en'})
print(load_config())
from orion.locales import get_strings
s = get_strings('en')
print(s['listening_phrases'][0])
print(s['terminal']['initializing'])
print(s['tts']['whisper'])
"
```

Expected:
```
{'language': 'en'}
At your service, Sir.
Initialising Orion...
en
```

- [ ] **Step 3: Restore default config**

```bash
python -c "from orion.config import save_config; save_config({'language': 'pt_BR'})"
```

- [ ] **Step 4: Verify web settings API**

```bash
# Start the web server briefly
cd /home/henrique/gitdocs/orion
python -c "
from orion.web.app import app
with app.test_client() as c:
    r = c.get('/api/settings')
    print('GET:', r.get_json())
    r = c.put('/api/settings', json={'language': 'en'})
    print('PUT:', r.get_json())
    r = c.get('/api/settings')
    print('GET after:', r.get_json())
    # Restore
    c.put('/api/settings', json={'language': 'pt_BR'})
"
```

Expected:
```
GET: {'language': 'pt_BR'}
PUT: {'status': 'saved', 'config': {'language': 'en'}}
GET after: {'language': 'en'}
```

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete English language support for Orion"
```
