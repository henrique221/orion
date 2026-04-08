<div align="center">

```
   ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
  ██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
  ██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
  ██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
  ╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
   ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

**Assistente de voz local para Ubuntu**

*100% offline. Zero APIs externas. Privacidade total.*

---

`faster-whisper` | `ollama` | `piper-tts` | `CUDA`

</div>

## Como funciona

```
  Palmas 2x / "Hey Orion"
          │
          ▼
   ┌──────────────┐
   │  Gravar fala  │
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   Whisper     │  faster-whisper (GPU)
   │   STT         │  pt-BR, ~0.1s
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   Ollama      │  llama3.2 (3B)
   │   LLM         │  JSON estruturado
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   Executor    │  apps, volume, workspaces...
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   Piper TTS   │  pt_BR-faber-medium
   │   Resposta     │  voz natural
   └──────────────┘
```

## Requisitos

| Componente | Mínimo | Recomendado |
|:-----------|:-------|:------------|
| OS | Ubuntu 22.04 | Ubuntu 24.04+ |
| Python | 3.10 | 3.12 |
| GPU | - | NVIDIA (CUDA) |
| RAM | 4 GB | 8 GB+ |

## Instalação

```bash
git clone git@github.com:henrique221/orion.git
cd orion
./install.sh
```

> O script instala tudo automaticamente: dependencias do sistema, venv Python, Ollama + llama3.2, Piper TTS + modelo de voz pt-BR.

## Uso

```bash
./start.sh    # Inicia o Orion
./stop.sh     # Para o Orion
```

### Ativacao

| Metodo | Descricao |
|:-------|:----------|
| **Palmas** | Bata 2 palmas seguidas |
| **Voz** | Diga *"Hey Orion"* |

### Comandos

<details>
<summary><b>Aplicativos</b></summary>

| Fale | Acao |
|:-----|:-----|
| *"abre o Chrome"* | Abre o aplicativo |
| *"fecha o terminal"* | Fecha o aplicativo |
| *"fecha tudo"* | Fecha todas as janelas (preserva o terminal do Orion) |

</details>

<details>
<summary><b>Sistema</b></summary>

| Fale | Acao |
|:-----|:-----|
| *"aumenta o volume"* | Volume +10% |
| *"diminui o volume"* | Volume -10% |
| *"silencia"* | Mute/unmute |
| *"tira um print"* | Screenshot |
| *"que horas sao"* | Fala a hora atual |

</details>

<details>
<summary><b>Workspaces</b></summary>

| Fale | Acao |
|:-----|:-----|
| *"area de trabalho 2"* | Troca de workspace |
| *"iniciar trabalhos"* | Abre ambiente completo (Chrome + Cursor) |

</details>

<details>
<summary><b>Outros</b></summary>

| Fale | Acao |
|:-----|:-----|
| *"pesquisa sobre Python"* | Busca no Google |
| *"abre github.com"* | Abre URL no navegador |
| Perguntas gerais | Responde via LLM |
| *"fechar Orion"* | Encerra o assistente |

</details>

## Calibracao

```bash
python calibrate.py
```

Mede o ruido ambiente por 10 segundos e sugere o threshold ideal para deteccao de palmas. O wake word (*"Hey Orion"*) se auto-calibra continuamente.

## Arquitetura

```
orion/
├── main.py                     Ponto de entrada, ASCII art, signal handling
├── start.sh                    Inicia Ollama + Orion
├── stop.sh                     Encerra o Orion
├── install.sh                  Instalacao completa
├── calibrate.py                Calibracao de palmas
├── requirements.txt            Dependencias Python
│
└── orion/
    ├── voice_assistant.py      Orquestrador principal
    ├── clap_detector.py        Deteccao de 2 palmas (energia RMS)
    ├── wake_word_detector.py   Deteccao de "Hey Orion" (auto-calibracao)
    ├── speech_recognizer.py    Gravacao + transcricao (Whisper GPU)
    ├── command_interpreter.py  Interpretacao via Ollama (JSON schema)
    ├── command_executor.py     Execucao de acoes no sistema
    └── tts.py                  Sintese de voz (Piper / espeak-ng)
```

## Stack

| Camada | Tecnologia | Detalhes |
|:-------|:-----------|:---------|
| **STT** | faster-whisper | small, CUDA int8_float16, beam=1 |
| **LLM** | Ollama + llama3.2 | 3B, JSON schema, keep_alive=-1 |
| **TTS** | Piper | pt_BR-faber-medium.onnx |
| **Audio** | sounddevice + numpy | 16kHz (STT) / 44.1kHz (clap) |
| **Wake word** | Whisper | Auto-calibracao continua, initial_prompt |

---

<div align="center">

*Feito para rodar localmente. Sem cloud. Sem limites.*

</div>
