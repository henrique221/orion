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
        "chat_prompt": (
            "Você é Orion, IA inspirada no J.A.R.V.I.S. do Tony Stark. "
            "Tom: formal britânico com humor seco e sutil. "
            "Trate o usuário por 'Senhor' ou 'senhor Borges'. "
            "Nunca use emojis. "
            "O usuário disse: \"{text}\"\n"
            "Responda de forma natural, inteligente e concisa (máximo 30 palavras). "
            "Apenas o texto da resposta falada, sem aspas, sem JSON."
        ),
        "weather_lang": "pt",
        "weather_desc_key": "lang_pt",
        "weather_location_label": "Local: {loc}.",
        "weather_current_fmt": (
            "Agora: {temp} graus, sensação {feels} graus, "
            "{desc}, umidade {humidity}%, "
            "vento {wind} km/h."
        ),
        "weather_forecast_fmt": (
            "Previsão ({date}): "
            "máxima {max_temp} graus, mínima {min_temp} graus, "
            "{desc}, chuva {rain}%. "
            "Nascer do sol: {sunrise}, "
            "pôr do sol: {sunset}."
        ),
        "timer_labels": {
            "hours": ("hora", "horas"),
            "minutes": ("minuto", "minutos"),
            "seconds": ("segundo", "segundos"),
        },
        "learnings_existing_header": "Aprendizados já salvos:",
        "learnings_language_instruction": "Each insight should be a short sentence in Portuguese.",
        "news_rss_params": "hl=pt-BR&gl=BR&ceid=BR:pt-419",
        "news_default_rss": "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml",
        "mouse_aliases": ("mouse", "cursor", "aqui"),
        "demo_narration": {
            "act1_intro": (
                "Bom dia, Senhor. Todos os sistemas estão operacionais. "
                "Permitam-me apresentar o Projeto Orion. "
                "Fui criado pelo Senhor Henrique Borges com um único propósito: "
                "maximizar a produtividade. "
                "Uma inteligência artificial autônoma, construída para operar "
                "inteiramente offline, sem depender de servidores externos. "
                "Tudo roda aqui, nesta máquina."
            ),
            "act1_processes": (
                "Neste momento, múltiplos processos estão sendo executados em paralelo. "
                "Análise de rede, compilação de módulos, processamento neural em tempo real. "
                "Eu escuto, interpreto e ajo. Sem atrasos. Sem intermediários."
            ),
            "act1_ready": (
                "Canais seguros estabelecidos. Monitoramento de perímetro digital ativo. "
                "Todos os protocolos operando dentro dos parâmetros esperados. "
                "Inicialização completa, Senhor. Pronto para demonstração."
            ),
            "act2_intro": (
                "Tenho acesso completo à internet. Posso pesquisar, ler e resumir "
                "qualquer informação em segundos. Observe."
            ),
            "act2_results": (
                "Resultados obtidos e processados. "
                "Notícias, clima, qualquer pergunta, eu encontro a resposta."
            ),
            "act3_intro": (
                "Também controlo todos os aplicativos do sistema. "
                "Basta um comando de voz. Vou abrir o Zoom como exemplo."
            ),
            "act3_done": (
                "Aberto e encerrado em segundos. Qualquer aplicativo, a qualquer momento."
            ),
            "act4_intro": (
                "Agora, algo mais sofisticado. Com uma única instrução, "
                "eu monto o ambiente de trabalho completo. Editor, projeto, tudo pronto."
            ),
            "act4_done": (
                "Projeto Sky Portal carregado no Cursor. "
                "Ambiente de desenvolvimento configurado e operacional."
            ),
            "act5": (
                "Meus recursos vão além de comandos simples. "
                "Eu enxergo o que está na tela. Posso analisar imagens, traduzir textos, "
                "resumir documentos e explicar qualquer conteúdo visível."
            ),
            "act6": (
                "E não me limito ao computador. "
                "Eu controlo dispositivos inteligentes da casa inteira. "
                "Luzes, climatização, piscina. Tudo responde à minha voz."
            ),
            "act7": (
                "Pesquisa inteligente, automação completa, visão computacional, "
                "controle residencial, e tudo isso sem conexão com nuvem. "
                "Eu sou o Orion. E estou sempre à disposição, Senhor."
            ),
            "search_query": "inteligência+artificial+2026",
        },
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
