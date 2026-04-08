import datetime
import os
import random
import subprocess
import threading
import time

import requests


IFTTT_KEY = "h0IO5AV2asEYG4fjT_SPbeimWkcqmlevMAAyaKZcYss"
IFTTT_URL = "https://maker.ifttt.com/trigger/{event}/with/key/" + IFTTT_KEY

SMART_HOME_DEVICES = {
    "varanda": {"on": "varanda_on", "off": "varanda_off"},
    "piscina": {"on": "piscina_on", "off": "piscina_off"},
}

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
    "start_work_done": [
        "Tudo pronto, Senhor. Bom trabalho.",
        "Ambiente configurado. Bom trabalho, Senhor.",
        "Estações operacionais. Bom trabalho, senhor Borges.",
        "Sistemas prontos. Que seja um dia produtivo, Senhor.",
    ],
    "switch_workspace": [
        "Área de trabalho {num}, Senhor.",
        "Alternando para área {num}.",
        "Transferindo para área de trabalho {num}.",
    ],
    "lock_screen": [
        "Trancando a estação, Senhor.",
        "Bloqueio ativado. Ninguém entra sem autorização.",
        "Protocolo de segurança ativado.",
    ],
    "unlock_screen": [
        "Estação desbloqueada, Senhor.",
        "Acesso restaurado. Bem-vindo de volta.",
        "Protocolo de segurança desativado.",
    ],
    "shutdown": [
        "Encerrando todos os sistemas. Até breve, Senhor.",
        "Desligamento iniciado. Foi um prazer servi-lo.",
        "Protocolo de desligamento executado.",
    ],
    "shutdown_confirm": [
        "Tem certeza que deseja desligar, Senhor?",
        "Confirma o desligamento completo, Senhor?",
        "Devo realmente encerrar todos os sistemas, Senhor?",
    ],
    "shutdown_cancelled": [
        "Desligamento cancelado, Senhor.",
        "Entendido, mantendo os sistemas ativos.",
        "Operação abortada. Seguimos online, Senhor.",
    ],
    "restart": [
        "Reinicialização em andamento, Senhor.",
        "Reiniciando todos os sistemas. Volto em instantes.",
        "Reboot iniciado.",
    ],
    "suspend": [
        "Entrando em modo de hibernação, Senhor.",
        "Suspendendo operações. Bons sonhos.",
        "Modo de espera ativado.",
    ],
    "brightness_up": [
        "Luminosidade ampliada, Senhor.",
        "Brilho da tela elevado.",
        "Aumentando claridade.",
    ],
    "brightness_down": [
        "Luminosidade reduzida, Senhor.",
        "Brilho da tela atenuado.",
        "Reduzindo claridade.",
    ],
    "empty_trash": [
        "Lixeira esvaziada, Senhor.",
        "Resíduos digitais eliminados.",
        "Protocolo de limpeza da lixeira executado.",
    ],
    "timer": [
        "Cronômetro definido para {duration}, Senhor.",
        "Timer ativado. Avisarei em {duration}.",
        "Contagem regressiva iniciada: {duration}.",
    ],
    "smart_home_on": [
        "Ativando {device}, Senhor.",
        "{device} ligado.",
        "Comando enviado. {device} online.",
    ],
    "smart_home_off": [
        "Desativando {device}, Senhor.",
        "{device} desligado.",
        "Comando enviado. {device} offline.",
    ],
    "smart_home_error": [
        "Falha ao controlar {device}, Senhor.",
        "Não consegui acionar {device}. Verifique a conexão.",
    ],
    "logout": [
        "Encerrando sessão, Senhor.",
        "Logout iniciado. Até a próxima.",
        "Sessão encerrada.",
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
        self._pending_shutdown = False

    def execute(self, command, original_text=""):
        if not command:
            return "Nenhum comando recebido."

        # Handle pending shutdown confirmation
        if self._pending_shutdown:
            self._pending_shutdown = False
            text = original_text.lower().strip()
            if any(w in text for w in (
                "sim", "confirmo", "pode", "positivo",
                "afirmativo", "claro", "manda", "yes",
            )):
                return self._execute_shutdown()
            return _pick("shutdown_cancelled")

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
        self._ensure_unlocked()

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
        return _pick("start_work_done")

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

    WEATHER_LOCATION = "Conceição da Aparecida"

    WEATHER_LOADING = [
        "Consultando satélites meteorológicos.",
        "Acessando dados climáticos, Senhor.",
        "Verificando as condições atmosféricas.",
        "Coletando informações meteorológicas.",
    ]

    WEEKDAY_MAP = {
        "segunda": 0, "terça": 1, "terca": 1,
        "quarta": 2, "quinta": 3, "sexta": 4,
        "sábado": 5, "sabado": 5, "domingo": 6,
    }

    def _resolve_day_index(self, day_str):
        if not day_str:
            return 0
        day = day_str.strip().lower()
        if day in ("", "hoje"):
            return 0
        if day in ("amanhã", "amanha"):
            return 1
        if day in ("depois de amanhã", "depois de amanha"):
            return 2
        for name, wd in self.WEEKDAY_MAP.items():
            if name in day:
                today_wd = datetime.datetime.now().weekday()
                diff = (wd - today_wd) % 7
                return diff if diff != 0 else 7
        return 0

    def _fetch_weather(self, location="", day_index=0):
        from urllib.parse import quote
        loc = location or self.WEATHER_LOCATION
        url = f"https://wttr.in/{quote(loc)}?format=j1&lang=pt"
        r = requests.get(url, timeout=10, headers={"Accept": "application/json"})
        r.raise_for_status()
        data = r.json()

        cur = data["current_condition"][0]
        desc_cur = cur.get("lang_pt", [{}])[0].get("value") or cur["weatherDesc"][0]["value"]

        parts = [f"Local: {loc}."]

        if day_index == 0:
            parts.append(
                f"Agora: {cur['temp_C']} graus, sensação {cur['FeelsLikeC']} graus, "
                f"{desc_cur}, umidade {cur['humidity']}%, "
                f"vento {cur['windspeedKmph']} km/h."
            )

        weather_days = data.get("weather", [])
        if day_index < len(weather_days):
            day = weather_days[day_index]
            mid = day["hourly"][len(day["hourly"]) // 2]
            desc_fc = mid.get("lang_pt", [{}])[0].get("value") if mid.get("lang_pt") else mid["weatherDesc"][0]["value"]
            parts.append(
                f"Previsão ({day['date']}): "
                f"máxima {day['maxtempC']} graus, mínima {day['mintempC']} graus, "
                f"{desc_fc}, chuva {mid['chanceofrain']}%. "
                f"Nascer do sol: {day['astronomy'][0]['sunrise']}, "
                f"pôr do sol: {day['astronomy'][0]['sunset']}."
            )
        elif day_index > 0:
            parts.append(f"Previsão indisponível para {day_index} dias à frente (máximo 3 dias).")

        return " ".join(parts)

    def _do_weather(self, target, args):
        try:
            t = self._speak_async(random.choice(self.WEATHER_LOADING))
            location = target.strip() if target else ""
            day_index = self._resolve_day_index(args)
            weather_data = self._fetch_weather(location, day_index)
            if t:
                t.join()

            question = self._original_text
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": (
                        f"Dados meteorológicos: {weather_data}\n\n"
                        f"Pergunta do usuário: \"{question}\"\n\n"
                        "Responda em português do Brasil de forma direta e concisa, "
                        "no tom do J.A.R.V.I.S. Foque no que foi perguntado. "
                        "Trate o usuário por Senhor. Máximo 3 frases curtas."
                    ),
                    "stream": False,
                    "keep_alive": -1,
                    "options": {"temperature": 0.3, "num_predict": 80},
                },
                timeout=15,
            )
            import re
            text = r.json()["response"].strip()
            text = re.sub(r"[*#_~`>|]", "", text)
            return text
        except Exception as e:
            print(f"  Erro ao consultar clima: {e}")
            return "Não consegui acessar os dados meteorológicos, Senhor."

    NEWS_LOADING = [
        "Rastreando as últimas notícias, Senhor.",
        "Acessando os canais de informação.",
        "Consultando as fontes de notícias.",
        "Varrendo os noticiários, Senhor.",
    ]

    AGENCIA_BRASIL_RSS = "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml"
    GOOGLE_NEWS_SEARCH = "https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    def _fetch_news(self, query=""):
        from urllib.parse import quote
        if query:
            rss = self.GOOGLE_NEWS_SEARCH.format(query=quote(query))
        else:
            rss = self.AGENCIA_BRASIL_RSS
        url = f"https://api.rss2json.com/v1/api.json?rss_url={quote(rss, safe='')}"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])[:6]
        headlines = []
        for i, item in enumerate(items, 1):
            title = item.get("title", "")
            source = item.get("author", "") or ""
            headlines.append(f"{i}. {title}" + (f" ({source})" if source else ""))
        return "\n".join(headlines)

    def _do_news(self, target, args):
        try:
            t = self._speak_async(random.choice(self.NEWS_LOADING))
            query = target.strip() if target else ""
            headlines = self._fetch_news(query)
            if t:
                t.join()

            question = self._original_text
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": (
                        f"Manchetes de notícias:\n{headlines}\n\n"
                        f"Pergunta do usuário: \"{question}\"\n\n"
                        "Você é o Orion, IA no estilo J.A.R.V.I.S. Resuma as notícias "
                        "em português do Brasil de forma inteligente e concisa. "
                        "Destaque o que é mais relevante para a pergunta do usuário. "
                        "Trate-o por Senhor. Máximo 4 frases curtas e diretas."
                    ),
                    "stream": False,
                    "keep_alive": -1,
                    "options": {"temperature": 0.3, "num_predict": 150},
                },
                timeout=15,
            )
            import re
            text = r.json()["response"].strip()
            text = re.sub(r"[*#_~`>|]", "", text)
            return text
        except Exception as e:
            print(f"  Erro ao consultar notícias: {e}")
            return "Não consegui acessar os canais de notícias, Senhor."

    def _is_screen_locked(self):
        try:
            result = subprocess.run(
                ["busctl", "get-property", "org.freedesktop.login1",
                 "/org/freedesktop/login1/session/auto",
                 "org.freedesktop.login1.Session", "LockedHint"],
                capture_output=True, text=True, timeout=3,
            )
            return "true" in result.stdout
        except Exception:
            return False

    def _ensure_unlocked(self):
        if self._is_screen_locked():
            subprocess.run(["loginctl", "unlock-session"], capture_output=True)
            time.sleep(1)
        self._inhibit_suspend()

    def _inhibit_suspend(self):
        """Desativa suspensão automática e escurecimento de tela."""
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.session", "idle-delay", "0"],
            capture_output=True,
        )
        subprocess.run(
            ["gsettings", "set", "org.gnome.settings-daemon.plugins.power",
             "sleep-inactive-ac-timeout", "0"],
            capture_output=True,
        )
        subprocess.run(["xset", "s", "off"], capture_output=True)
        subprocess.run(["xset", "-dpms"], capture_output=True)

    def _do_unlock_screen(self, target, args):
        subprocess.run(["loginctl", "unlock-session"], capture_output=True)
        self._inhibit_suspend()
        return _pick("unlock_screen")

    def _do_lock_screen(self, target, args):
        subprocess.Popen(
            ["loginctl", "lock-session"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return _pick("lock_screen")

    def _do_shutdown(self, target, args):
        self._pending_shutdown = True
        return _pick("shutdown_confirm")

    def _execute_shutdown(self):
        reply = _pick("shutdown")
        if self._tts:
            self._tts.speak(reply)
        time.sleep(1)
        subprocess.Popen(["systemctl", "poweroff"])
        return None

    def _do_restart(self, target, args):
        reply = _pick("restart")
        if self._tts:
            self._tts.speak(reply)
        time.sleep(1)
        subprocess.Popen(["systemctl", "reboot"])
        return None

    def _do_suspend(self, target, args):
        reply = _pick("suspend")
        if self._tts:
            self._tts.speak(reply)
        time.sleep(1)
        subprocess.Popen(["systemctl", "suspend"])
        return None

    def _do_brightness_up(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["brightnessctl", "set", f"+{pct}%"],
            capture_output=True,
        )
        return _pick("brightness_up")

    def _do_brightness_down(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["brightnessctl", "set", f"{pct}%-"],
            capture_output=True,
        )
        return _pick("brightness_down")

    def _do_battery(self, target, args):
        try:
            result = subprocess.run(
                ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.split("\n"):
                if "percentage" in line:
                    pct = line.split(":")[-1].strip()
                    return f"Bateria em {pct}, Senhor."
            return "Informação de bateria indisponível, Senhor."
        except Exception:
            return "Não consegui acessar os dados da bateria, Senhor."

    def _do_system_info(self, target, args):
        try:
            uptime = subprocess.run(
                ["uptime", "-p"], capture_output=True, text=True
            ).stdout.strip()
            mem = subprocess.run(
                ["free", "-h", "--si"], capture_output=True, text=True
            )
            mem_lines = mem.stdout.strip().split("\n")
            mem_data = mem_lines[1].split() if len(mem_lines) > 1 else []
            mem_used = mem_data[2] if len(mem_data) > 2 else "?"
            mem_total = mem_data[1] if len(mem_data) > 1 else "?"
            disk = subprocess.run(
                ["df", "-h", "--output=used,size,pcent", "/"],
                capture_output=True, text=True,
            )
            disk_lines = disk.stdout.strip().split("\n")
            disk_data = disk_lines[1].split() if len(disk_lines) > 1 else []
            disk_pct = disk_data[2] if len(disk_data) > 2 else "?"
            return (
                f"Sistema ativo {uptime.replace('up ', '')}. "
                f"Memória: {mem_used} de {mem_total}. "
                f"Disco raiz: {disk_pct} em uso."
            )
        except Exception:
            return "Falha ao coletar dados do sistema, Senhor."

    def _do_empty_trash(self, target, args):
        subprocess.run(
            ["gio", "trash", "--empty"],
            capture_output=True,
        )
        return _pick("empty_trash")

    def _do_timer(self, target, args):
        import re
        raw = f"{target} {args} {self._original_text}"
        match = re.search(r"(\d+)", raw)
        if not match:
            return "Não identifiquei a duração do timer, Senhor."
        value = int(match.group(1))
        if any(w in raw.lower() for w in ("hora", "hour")):
            seconds = value * 3600
            label = f"{value} hora{'s' if value > 1 else ''}"
        elif any(w in raw.lower() for w in ("segundo", "second", "seg")):
            seconds = value
            label = f"{value} segundo{'s' if value > 1 else ''}"
        else:
            seconds = value * 60
            label = f"{value} minuto{'s' if value > 1 else ''}"

        def _alarm():
            time.sleep(seconds)
            if self._tts:
                self._tts.speak(f"Senhor, o timer de {label} expirou.")
            subprocess.run(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
                capture_output=True,
            )

        threading.Thread(target=_alarm, daemon=True).start()
        return _pick("timer", duration=label)

    def _do_logout(self, target, args):
        reply = _pick("logout")
        if self._tts:
            self._tts.speak(reply)
        time.sleep(1)
        subprocess.Popen(
            ["loginctl", "terminate-user", os.environ.get("USER", "")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return None

    def _do_smart_home(self, target, args):
        device = target.strip().lower()
        state = args.strip().lower() if args else "on"
        device_info = SMART_HOME_DEVICES.get(device)
        if not device_info:
            return f"Dispositivo '{target}' não cadastrado, Senhor."
        event = device_info.get(state)
        if not event:
            return f"Ação '{args}' inválida para {target}, Senhor."
        try:
            r = requests.get(IFTTT_URL.format(event=event), timeout=10)
            r.raise_for_status()
            label = target.capitalize()
            return _pick(f"smart_home_{state}", device=label)
        except Exception:
            return _pick("smart_home_error", device=target.capitalize())

    def _do_chat(self, target, args):
        return None
