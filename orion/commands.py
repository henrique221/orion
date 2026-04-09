"""
Command registry — single source of truth for all Orion commands.

To add a new command:
  1. Add an entry to COMMANDS below
  2. Add a _do_<action> method in command_executor.py

Everything else (prompt, schema, replies) is auto-generated.
"""

import random


# ── Command definitions ──────────────────────────────────────────────

COMMANDS = {
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
        "notes": 'Qualquer pedido sobre conteúdo da tela (traduzir, resumir, ler, explicar, analisar) é SEMPRE analyze_screen. NUNCA dividir em open_app ou search_web. Quando menciona mouse/cursor/aqui, target=mouse. Use args para indicar a tarefa (traduzir, resumir, ler, explicar, ou vazio para descrição geral).',
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
            '"traduz o texto selecionado"/"traduz o que está selecionado"/"traduz esse texto"/"traduz essa palavra" → target="", args="traduzir"',
            '"resume o texto selecionado"/"resuma a seleção"/"resume esse texto" → target="", args="resumir"',
            '"lê o texto selecionado"/"leia a seleção"/"lê esse texto" → target="", args="ler"',
            '"explica o texto selecionado"/"explique a seleção"/"explica esse texto"/"explica essa palavra" → target="", args="explicar"',
            '"o que diz o texto selecionado?"/"o que diz esse texto?" → target="", args=""',
            '"corrige o texto selecionado"/"corrige esse texto" → target="", args="corrigir"',
            '"o que significa essa palavra?"/"o que significa esse texto?" → target="", args="explicar"',
        ],
        "notes": 'Qualquer pedido sobre "texto selecionado"/"seleção"/"esse texto"/"essa palavra"/"o que está selecionado" é SEMPRE analyze_selection. NUNCA confundir com analyze_screen.',
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
        "examples": ['"fecha a demonstração"/"para a demonstração"/"encerra o demo"/"fecha o demo"'],
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
}


# ── Config ───────────────────────────────────────────────────────────

APP_MAP = {
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
}

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

MONITOR_ALIASES = {
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
}

VISION_MODEL = "moondream"

SAFE_COMMAND_PREFIXES = [
    "ls", "pwd", "echo", "date", "cal", "df", "free",
    "whoami", "hostname", "uname", "uptime", "cat /etc",
    "which", "wc", "head", "tail",
]


# ── Auto-generated from COMMANDS ────────────────────────────────────

def get_action_enum():
    return list(COMMANDS.keys())


def build_prompt_mappings():
    lines = []
    for action, cmd in COMMANDS.items():
        for example in cmd["examples"]:
            if "→" in example:
                lines.append(f"{example}, action={action}")
            else:
                lines.append(f"{example} → action={action}")
    return "\n".join(lines)


def build_prompt_notes():
    notes = []
    for cmd in COMMANDS.values():
        if "notes" in cmd:
            notes.append(cmd["notes"])
    return "\n".join(notes)


def build_json_schema():
    return {
        "type": "object",
        "properties": {
            "commands": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": get_action_enum()},
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


def pick(action, variant="success", **kwargs):
    """Pick a random reply template and format it."""
    replies = COMMANDS.get(action, {}).get("replies", {})
    templates = replies.get(variant, [])
    if not templates:
        return None
    return random.choice(templates).format(**kwargs)
