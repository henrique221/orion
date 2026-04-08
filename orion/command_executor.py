import datetime
import os
import random
import subprocess
import threading
import time

import requests


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

REPLIES = {
    "open_app": [
        "Inicializando {target}, Senhor.",
        "Carregando {target}.",
        "{target} entrando online.",
        "Executando {target}, Senhor.",
    ],
    "close_app": [
        "{target} encerrado, Senhor.",
        "Desligando {target}.",
        "{target} fora do ar.",
    ],
    "open_url": [
        "Direcionando navegador, Senhor.",
        "Acessando {target}.",
        "Navegador redirecionado.",
    ],
    "search_web": [
        "Vasculhando a rede por {target}.",
        "Iniciando busca por {target}, Senhor.",
        "Rastreando informações sobre {target}.",
    ],
    "volume_up": [
        "Amplificando saída de áudio.",
        "Volume elevado, Senhor.",
        "Aumentando potência sonora.",
    ],
    "volume_down": [
        "Reduzindo saída de áudio.",
        "Volume atenuado, Senhor.",
        "Diminuindo potência sonora.",
    ],
    "mute": [
        "Protocolo silencioso ativado.",
        "Áudio suprimido, Senhor.",
        "Silêncio total.",
    ],
    "screenshot": [
        "Imagem capturada, Senhor.",
        "Registro visual arquivado.",
        "Screenshot efetuado com sucesso.",
    ],
    "close_all": [
        "Encerrando todos os processos, Senhor.",
        "Limpando a mesa. Tudo desligado.",
        "Todos os aplicativos foram dispensados.",
        "Protocolo de limpeza executado.",
    ],
    "start_work_loading": [
        "Configurando segunda área de trabalho.",
        "Preparando a próxima estação.",
        "Montando o restante do ambiente.",
        "Quase lá, Senhor. Finalizando configurações.",
    ],
    "switch_workspace": [
        "Área de trabalho {num}, Senhor.",
        "Alternando para área {num}.",
        "Transferindo para área de trabalho {num}.",
    ],
}


def _pick(action, **kwargs):
    templates = REPLIES.get(action, [])
    if not templates:
        return None
    return random.choice(templates).format(**kwargs)


SAFE_COMMAND_PREFIXES = [
    "ls",
    "pwd",
    "echo",
    "date",
    "cal",
    "df",
    "free",
    "whoami",
    "hostname",
    "uname",
    "uptime",
    "cat /etc",
    "which",
    "wc",
    "head",
    "tail",
]


class CommandExecutor:
    def __init__(self, tts=None):
        self._tts = tts

    def execute(self, command, original_text=""):
        if not command:
            return "Nenhum comando recebido."

        action = command.get("action", "chat")
        target = command.get("target", "")
        args = command.get("args", "")
        reply = command.get("reply", "")
        self._original_text = original_text

        handler = getattr(self, f"_do_{action}", None)
        if handler:
            result = handler(target, args)
            return result if result else reply
        return reply

    def _do_open_app(self, target, args):
        app = APP_MAP.get(target.lower(), target)
        try:
            subprocess.Popen(
                [app],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return _pick("open_app", target=target.capitalize())
        except FileNotFoundError:
            return f"Aplicativo {target} não localizado nos meus registros, Senhor."

    def _do_close_app(self, target, args):
        app = APP_MAP.get(target.lower(), target)
        try:
            subprocess.run(["wmctrl", "-c", target], capture_output=True)
            return _pick("close_app", target=target.capitalize())
        except FileNotFoundError:
            try:
                subprocess.run(["pkill", "-f", app], capture_output=True)
                return _pick("close_app", target=target.capitalize())
            except Exception:
                return f"{target} não está respondendo ao encerramento, Senhor."

    def _do_open_url(self, target, args):
        url = target if target.startswith("http") else f"https://{target}"
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return _pick("open_url", target=target)

    def _do_search_web(self, target, args):
        query = target.replace(" ", "+")
        url = f"https://www.google.com/search?q={query}"
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return _pick("search_web", target=target)

    def _do_volume_up(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{pct}%"],
            capture_output=True,
        )
        return _pick("volume_up")

    def _do_volume_down(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{pct}%"],
            capture_output=True,
        )
        return _pick("volume_down")

    def _do_mute(self, target, args):
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
            capture_output=True,
        )
        return _pick("mute")

    def _do_screenshot(self, target, args):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/screenshot_{ts}.png")
        result = subprocess.run(
            ["gnome-screenshot", "-f", path], capture_output=True
        )
        if result.returncode == 0:
            return _pick("screenshot")
        result = subprocess.run(["scrot", path], capture_output=True)
        if result.returncode == 0:
            return _pick("screenshot")
        return "Falha na captura de tela, Senhor. Sistemas de imagem indisponíveis."

    def _do_show_time(self, target, args):
        now = datetime.datetime.now()
        h, m = now.hour, now.minute
        if m == 0:
            return f"Exatamente {h} horas, Senhor."
        return f"Marcando {h} e {m}, Senhor."

    def _do_list_windows(self, target, args):
        try:
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True
            )
            lines = result.stdout.strip().split("\n")
            windows = [
                line.split(None, 4)[-1]
                for line in lines
                if line.strip()
            ]
            if windows:
                listing = ", ".join(windows[:10])
                return f"Janelas abertas: {listing}."
            return "Nenhuma janela encontrada."
        except FileNotFoundError:
            return "wmctrl não instalado."

    def _do_run_command(self, target, args):
        cmd = target.strip()
        if not any(cmd.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES):
            return f"Comando '{cmd}' não permitido por segurança."
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout.strip()
            return output if output else "Comando executado."
        except subprocess.TimeoutExpired:
            return "Comando expirou."

    def _move_window_to_ultrawide(self, title_match):
        """Move a janela que contém title_match no título para a HDMI-1-0."""
        for _ in range(20):
            time.sleep(0.5)
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True
            )
            for line in result.stdout.strip().split("\n"):
                if title_match.lower() in line.lower():
                    wid = line.split()[0]
                    subprocess.run(
                        ["wmctrl", "-i", "-r", wid, "-b", "remove,maximized_vert,maximized_horz"],
                        capture_output=True,
                    )
                    time.sleep(0.3)
                    subprocess.run(
                        ["wmctrl", "-i", "-r", wid, "-e", "0,0,0,2560,1080"],
                        capture_output=True,
                    )
                    return

    def _open_cursor_on_ultrawide(self, project_path):
        path = os.path.expanduser(project_path)
        project_name = os.path.basename(path)
        subprocess.Popen(
            ["cursor", "--new-window", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self._move_window_to_ultrawide(project_name)

    def _speak_async(self, text):
        if self._tts:
            t = threading.Thread(
                target=self._tts.speak, args=(text,), daemon=True
            )
            t.start()
            return t
        return None

    def _do_start_work(self, target, args):
        # Frase motivacional enquanto abre workspace 1
        quote = self._motivational_quote()
        t = self._speak_async(quote)

        # Workspace 1: Chrome com Slack + Cursor com skyportal
        subprocess.Popen(
            [
                "google-chrome",
                "--new-window",
                "--window-position=2560,0",
                "--window-size=1920,1080",
                "https://app.slack.com/client/T07PM9G3D9T",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self._open_cursor_on_ultrawide("~/gitdocs/skyportal-website")

        if t:
            t.join()
        # Frase de loading enquanto abre workspace 2
        t = self._speak_async(_pick("start_work_loading"))

        time.sleep(3)
        subprocess.run(["wmctrl", "-s", "1"], capture_output=True)
        time.sleep(0.5)
        subprocess.Popen(
            [
                "google-chrome",
                "--new-window",
                "--window-position=2560,0",
                "--window-size=1920,1080",
                "https://app.slack.com/client/T04KMP7QU",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self._open_cursor_on_ultrawide("~/gitdocs/gloo")

        if t:
            t.join()
        return None

    def _motivational_quote(self):
        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": (
                        "Você é uma IA sofisticada como o J.A.R.V.I.S. Gere uma frase curta "
                        "e inspiradora em português do Brasil para seu mestre começar a trabalhar. "
                        "MÁXIMO 8 palavras. Tom confiante e elegante. Sem aspas. Só a frase."
                    ),
                    "stream": False,
                    "keep_alive": -1,
                    "options": {"temperature": 0.9, "num_predict": 25},
                },
                timeout=15,
            )
            phrase = r.json()["response"].strip().strip('"')
            return phrase
        except Exception:
            return _pick("start_work")

    def _do_close_all(self, target, args):
        # Descobre o PID do terminal que roda o Orion
        # Sobe a árvore de processos até achar o terminal
        terminal_pid = os.getppid()
        try:
            while terminal_pid > 1:
                cmdline = open(f"/proc/{terminal_pid}/cmdline", "rb").read()
                if b"gnome-terminal" in cmdline or b"xterm" in cmdline or b"konsole" in cmdline or b"alacritty" in cmdline or b"kitty" in cmdline or b"tilix" in cmdline:
                    break
                stat = open(f"/proc/{terminal_pid}/stat").read()
                terminal_pid = int(stat.split(")")[1].split()[1])
        except (FileNotFoundError, ValueError, IndexError):
            terminal_pid = os.getppid()

        result = subprocess.run(
            ["wmctrl", "-l", "-p"], capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split()
            wid = parts[0]
            try:
                win_pid = int(parts[2])
            except (IndexError, ValueError):
                win_pid = -1
            if win_pid == terminal_pid:
                continue
            subprocess.run(["wmctrl", "-i", "-c", wid], capture_output=True)
            time.sleep(0.3)
        return _pick("close_all")

    def _do_switch_workspace(self, target, args):
        import re
        # Extrai o primeiro número de target, args ou texto original
        match = re.search(r"\d+", f"{target} {args} {self._original_text}")
        if not match:
            return "Número da área de trabalho inválido."
        num = int(match.group()) - 1
        subprocess.run(["wmctrl", "-s", str(num)], capture_output=True)
        return _pick("switch_workspace", num=num + 1)

    def _do_chat(self, target, args):
        return None
