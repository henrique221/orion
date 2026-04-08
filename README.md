# Orion

Assistente de voz local para Ubuntu. 100% offline, sem APIs externas.

## O que faz

- Fica ouvindo em background, ativa com **2 palmas** ou **"Hey Orion"**
- Transcreve fala com **faster-whisper** (GPU CUDA)
- Interpreta comandos com **Ollama** (llama3.2)
- Executa ações no sistema (abrir/fechar apps, volume, screenshot, workspaces, etc.)
- Responde em voz com **Piper TTS** (pt-BR)

## Requisitos

- Ubuntu 22.04+
- Python 3.10+
- NVIDIA GPU (recomendado) ou CPU

## Instalação

```bash
./install.sh
```

Instala tudo: pacotes do sistema, venv Python, Ollama + llama3.2, Piper TTS + modelo pt-BR.

## Uso

```bash
./start.sh   # inicia o Orion
./stop.sh    # para o Orion
```

## Comandos suportados

| Comando | Ação |
|---------|------|
| "abre o Chrome" | Abre aplicativo |
| "fecha o terminal" | Fecha aplicativo |
| "fecha tudo" | Fecha todas as janelas (exceto o terminal do Orion) |
| "aumenta/diminui o volume" | Controle de volume via pactl |
| "que horas são" | Fala a hora atual |
| "tira um print" | Captura a tela |
| "pesquisa sobre X" | Busca no Google |
| "área de trabalho 2" | Troca de workspace |
| "iniciar trabalhos" | Abre ambiente de trabalho (Chrome + Cursor) |
| "fechar Orion" | Encerra o assistente |
| Perguntas gerais | Responde via LLM |

## Calibração

```bash
python calibrate.py
```

Mede o ruído ambiente e sugere o threshold ideal para detecção de palmas.

## Estrutura

```
├── main.py                  # Entry point
├── start.sh / stop.sh       # Scripts de controle
├── install.sh               # Instalação completa
├── calibrate.py             # Calibração de palmas
├── requirements.txt         # Dependências Python
└── orion/
    ├── clap_detector.py     # Detecção de palmas
    ├── wake_word_detector.py # Detecção de "Hey Orion"
    ├── speech_recognizer.py # Transcrição com Whisper (GPU)
    ├── command_interpreter.py # Interpretação com Ollama
    ├── command_executor.py  # Execução de ações no sistema
    ├── tts.py               # Síntese de voz (Piper/espeak-ng)
    └── voice_assistant.py   # Orquestrador
```

## Stack

- **STT**: faster-whisper (small, CUDA float16)
- **LLM**: Ollama + llama3.2 (3B)
- **TTS**: Piper (pt_BR-faber-medium) / espeak-ng (fallback)
- **Áudio**: sounddevice + numpy
- **Wake word**: Whisper com auto-calibração contínua
