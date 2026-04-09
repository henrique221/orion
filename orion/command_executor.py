import base64
import datetime
import math
import os
import random
import shutil
import subprocess
import threading
import time

import requests

from orion.commands import (
    APP_MAP,
    IFTTT_URL,
    MONITOR_ALIASES,
    MONITORS,
    SAFE_COMMAND_PREFIXES,
    SMART_HOME_DEVICES,
    VISION_MODEL,
    pick,
)

class CommandExecutor:
    def __init__(self, tts=None):
        self._tts = tts
        self._pending_shutdown = False
        self._demo_running = False

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
            return pick("shutdown", "cancelled")

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
            return pick("open_app", "success", target=target.capitalize())
        except FileNotFoundError:
            return f"Aplicativo {target} não localizado nos meus registros, Senhor."

    def _do_close_app(self, target, args):
        app = APP_MAP.get(target.lower(), target)
        try:
            subprocess.run(["wmctrl", "-c", target], capture_output=True)
            return pick("close_app", "success", target=target.capitalize())
        except FileNotFoundError:
            try:
                subprocess.run(["pkill", "-f", app], capture_output=True)
                return pick("close_app", "success", target=target.capitalize())
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
        return pick("open_url", "success", target=target)

    def _do_search_web(self, target, args):
        query = target.replace(" ", "+")
        url = f"https://www.google.com/search?q={query}"
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return pick("search_web", "success", target=target)

    def _do_volume_up(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{pct}%"],
            capture_output=True,
        )
        return pick("volume_up")

    def _do_volume_down(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{pct}%"],
            capture_output=True,
        )
        return pick("volume_down")

    def _do_mute(self, target, args):
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
            capture_output=True,
        )
        return pick("mute")

    def _do_screenshot(self, target, args):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/screenshot_{ts}.png")
        result = subprocess.run(
            ["gnome-screenshot", "-f", path], capture_output=True
        )
        if result.returncode == 0:
            return pick("screenshot")
        result = subprocess.run(["scrot", path], capture_output=True)
        if result.returncode == 0:
            return pick("screenshot")
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
        t = self._speak_async(pick("start_work", "loading"))

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
        return pick("start_work", "done")

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
            return pick("start_work", "done")

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
        return pick("close_all")

    def _do_switch_workspace(self, target, args):
        import re
        # Extrai o primeiro número de target, args ou texto original
        match = re.search(r"\d+", f"{target} {args} {self._original_text}")
        if not match:
            return "Número da área de trabalho inválido."
        num = int(match.group()) - 1
        subprocess.run(["wmctrl", "-s", str(num)], capture_output=True)
        return pick("switch_workspace", "success", num=num + 1)

    WEATHER_LOCATION = "Conceição da Aparecida"


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
            t = self._speak_async(pick("weather", "loading"))
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
            t = self._speak_async(pick("news", "loading"))
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
        return pick("unlock_screen")

    def _do_lock_screen(self, target, args):
        subprocess.Popen(
            ["loginctl", "lock-session"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return pick("lock_screen")

    def _do_shutdown(self, target, args):
        self._pending_shutdown = True
        return pick("shutdown", "confirm")

    def _execute_shutdown(self):
        reply = pick("shutdown")
        if self._tts:
            self._tts.speak(reply)
        time.sleep(1)
        subprocess.Popen(["systemctl", "poweroff"])
        return None

    def _do_restart(self, target, args):
        reply = pick("restart")
        if self._tts:
            self._tts.speak(reply)
        time.sleep(1)
        subprocess.Popen(["systemctl", "reboot"])
        return None

    def _do_suspend(self, target, args):
        reply = pick("suspend")
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
        return pick("brightness_up")

    def _do_brightness_down(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["brightnessctl", "set", f"{pct}%-"],
            capture_output=True,
        )
        return pick("brightness_down")

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
        return pick("empty_trash")

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
        return pick("timer", "success", duration=label)

    def _do_logout(self, target, args):
        reply = pick("logout")
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
            return pick("smart_home", state, device=label)
        except Exception:
            return pick("smart_home", "error", device=target.capitalize())

    # ── Analyze screen ──────────────────────────────────────────

    OLLAMA_URL = "http://localhost:11434"
    LLM_MODEL = "llama3.2"

    MOUSE_REGION_SIZE = (800, 600)  # Area around cursor to capture

    def _get_mouse_position(self):
        """Returns (x, y) of the mouse cursor."""
        result = subprocess.run(
            ["xdotool", "getmouselocation"],
            capture_output=True, text=True,
        )
        # Output: x:1234 y:567 screen:0 window:12345
        parts = dict(p.split(":") for p in result.stdout.strip().split() if ":" in p)
        return int(parts["x"]), int(parts["y"])

    def _do_analyze_screen(self, target, args):
        # Resolve monitor or mouse
        name = target.strip().lower() if target else ""
        is_mouse = name in ("mouse", "cursor", "aqui")
        if not is_mouse:
            name = MONITOR_ALIASES.get(name, name)
            if name and name not in MONITORS:
                return f"Monitor '{target}' não encontrado, Senhor."

        try:
            # Stage 1: Capture
            self._speak_sync(pick("analyze_screen", "capturing"))

            img_path = "/tmp/orion_screen_analyze.png"
            full_path = "/tmp/orion_screen_full.png"

            # Always capture full screen first
            subprocess.run(
                ["scrot", full_path, "--overwrite"], capture_output=True
            )
            if not os.path.isfile(full_path):
                subprocess.run(
                    ["gnome-screenshot", "-f", full_path],
                    capture_output=True,
                )

            if not os.path.isfile(full_path):
                return "Falha na captura de tela, Senhor."

            if is_mouse:
                # Crop region around mouse cursor
                mx, my = self._get_mouse_position()
                rw, rh = self.MOUSE_REGION_SIZE
                cx = max(0, mx - rw // 2)
                cy = max(0, my - rh // 2)
                print(f"  Mouse em ({mx}, {my}), recortando {rw}x{rh}+{cx}+{cy}")
                subprocess.run(
                    ["convert", full_path,
                     "-crop", f"{rw}x{rh}+{cx}+{cy}", "+repage", img_path],
                    capture_output=True,
                )
                os.remove(full_path)
            elif name:
                x, y, w, h = MONITORS[name]
                subprocess.run(
                    ["convert", full_path,
                     "-crop", f"{w}x{h}+{x}+{y}", "+repage", img_path],
                    capture_output=True,
                )
                os.remove(full_path)
            else:
                os.rename(full_path, img_path)

            if not os.path.isfile(img_path):
                return "Falha na captura de tela, Senhor."

            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()

            # Stage 2: Swap models
            self._speak_sync(pick("analyze_screen", "swapping"))
            print("  Descarregando LLM para liberar VRAM...")
            requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={"model": self.LLM_MODEL, "keep_alive": 0},
                timeout=10,
            )
            time.sleep(2)

            # Stage 3: Analyze — vision model extracts all text/content
            self._speak_sync(pick("analyze_screen", "analyzing"))
            print(f"  Carregando modelo de visão ({VISION_MODEL})...")
            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": VISION_MODEL,
                    "prompt": (
                        "Read and extract ALL visible text on this screen. "
                        "Also describe any images, UI elements, windows, and applications visible. "
                        "Be thorough — capture every piece of text you can read."
                    ),
                    "images": [img_b64],
                    "stream": False,
                    "options": {"num_predict": 500},
                },
                timeout=120,
            )
            r.raise_for_status()
            analysis = r.json()["response"].strip()
            print(f"  Análise bruta: {analysis}")

            # Stage 4: Restore LLM
            self._speak_sync(pick("analyze_screen", "restoring"))
            print("  Restaurando LLM...")
            requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={"model": VISION_MODEL, "keep_alive": 0},
                timeout=10,
            )
            time.sleep(1)
            requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": "ok",
                    "keep_alive": -1,
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=30,
            )
            print("  LLM restaurado.")

            os.remove(img_path)

            # Stage 5: LLM answers the user's question using the extracted content
            import re
            question = self._original_text
            task = args.strip().lower() if args else ""

            task_instructions = {
                "traduzir": "Traduza o texto extraído da tela para português do Brasil.",
                "resumir": "Resuma o conteúdo da tela de forma concisa.",
                "ler": "Leia e reproduza o texto visível na tela.",
                "explicar": "Explique o conteúdo da tela de forma clara e didática.",
            }
            task_hint = task_instructions.get(task, "Responda à pergunta do usuário sobre o conteúdo da tela.")

            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": (
                        f"Conteúdo extraído da tela:\n{analysis}\n\n"
                        f"Pergunta do usuário: \"{question}\"\n\n"
                        f"Tarefa: {task_hint}\n\n"
                        "Responda em português do Brasil de forma concisa, "
                        "no tom do J.A.R.V.I.S. Trate-o por Senhor. "
                        "Máximo 5 frases. Foque no que foi pedido."
                    ),
                    "stream": False,
                    "keep_alive": -1,
                    "options": {"temperature": 0.3, "num_predict": 200},
                },
                timeout=20,
            )
            text = r.json()["response"].strip()
            text = re.sub(r"[*#_~`>|]", "", text)
            return text

        except Exception as e:
            print(f"  Erro na análise de tela: {e}")
            self._restore_llm()
            return "Falha na análise visual, Senhor."

    def _get_selected_text(self):
        """Tries multiple methods to get selected text."""
        methods = [
            # 1. xclip primary selection (highlighted text)
            ["xclip", "-selection", "primary", "-o"],
            # 2. xsel primary selection
            ["xsel", "-o"],
            # 3. xclip clipboard
            ["xclip", "-selection", "clipboard", "-o"],
            # 4. xsel clipboard
            ["xsel", "--clipboard", "-o"],
        ]
        for cmd in methods:
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=3,
                )
                text = result.stdout.strip()
                if text:
                    return text
            except (FileNotFoundError, Exception):
                continue

        # 5. Last resort: simulate Ctrl+C and read clipboard
        try:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", "ctrl+c"],
                capture_output=True, timeout=3,
            )
            time.sleep(0.3)
            for cmd in methods:
                try:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=3,
                    )
                    text = result.stdout.strip()
                    if text:
                        return text
                except (FileNotFoundError, Exception):
                    continue
        except Exception:
            pass

        return ""

    def _do_analyze_selection(self, target, args):
        self._speak_sync(pick("analyze_selection", "loading"))

        selected = self._get_selected_text()

        if not selected:
            return pick("analyze_selection", "empty")

        print(f"  Texto selecionado ({len(selected)} chars): {selected[:100]}...")

        import re
        question = self._original_text
        task = args.strip().lower() if args else ""

        task_instructions = {
            "traduzir": "Traduza o texto para português do Brasil. Se já estiver em português, traduza para inglês.",
            "resumir": "Resuma o texto de forma concisa.",
            "ler": "Leia e reproduza o texto.",
            "explicar": "Explique o conteúdo do texto de forma clara e didática.",
            "corrigir": "Corrija erros de gramática e ortografia no texto. Mostre o texto corrigido.",
        }
        task_hint = task_instructions.get(task, "Responda à pergunta do usuário sobre o texto.")

        try:
            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": (
                        f"Texto selecionado pelo usuário:\n\"{selected}\"\n\n"
                        f"Pedido do usuário: \"{question}\"\n\n"
                        f"Tarefa: {task_hint}\n\n"
                        "Responda em português do Brasil de forma concisa, "
                        "no tom do J.A.R.V.I.S. Trate-o por Senhor. "
                        "Foque no que foi pedido."
                    ),
                    "stream": False,
                    "keep_alive": -1,
                    "options": {"temperature": 0.3, "num_predict": 300},
                },
                timeout=20,
            )
            text = r.json()["response"].strip()
            text = re.sub(r"[*#_~`>|]", "", text)
            return text
        except Exception as e:
            print(f"  Erro na análise de seleção: {e}")
            return "Falha ao processar o texto selecionado, Senhor."

    def _speak_sync(self, text):
        """Fala e espera terminar antes de continuar."""
        if self._tts and text:
            self._tts.speak(text)

    def _restore_llm(self):
        try:
            requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": "ok",
                    "keep_alive": -1,
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=30,
            )
        except Exception:
            pass

    # ── Demo hacker ──────────────────────────────────────────────

    DEMO_DURATION = 30

    DEMO_BASH_EFFECTS = [
        # Fake access log
        r"""bash -c 'while true; do printf "\033[33m%s \033[36m[%s] \033[0m%s %s/%s \033[32m%s\033[0m\n" \
            "$(date +%H:%M:%S)" \
            "$(shuf -n1 -e INFO WARN DEBUG TRACE)" \
            "$(shuf -n1 -e GET POST PUT DELETE PATCH)" \
            "$(shuf -n1 -e /api /auth /data /sys /core)" \
            "$(shuf -n1 -e login sync status config deploy scan)" \
            "$(shuf -n1 -e 200 201 301 403 404 500)"; sleep 0.04; done'""",
        # Fake port scan
        r"""bash -c 'while true; do printf "\033[31m[SCAN]\033[0m %s:%d \033[33m%-8s\033[0m %s\n" \
            "$(printf "%d.%d.%d.%d" $((RANDOM%255)) $((RANDOM%255)) $((RANDOM%255)) $((RANDOM%255)))" \
            "$((RANDOM%65535))" \
            "$(shuf -n1 -e OPEN CLOSED FILTERED)" \
            "$(shuf -n1 -e ssh http ftp smtp dns rdp vnc telnet)"; sleep 0.06; done'""",
        # Hex stream
        r"""bash -c 'while true; do printf "\033[32m%04x: " $((RANDOM%65535)); \
            for i in $(seq 1 16); do printf "%02x " $((RANDOM%256)); done; \
            printf "\033[0m\n"; sleep 0.03; done'""",
        # Fake compilation
        r"""bash -c 'while true; do printf "\033[36m[%s]\033[0m Compiling %s v%d.%d.%d (%s)\n" \
            "$(date +%H:%M:%S)" \
            "$(shuf -n1 -e orion_core neural_net crypto_engine quantum_sim payload_gen)" \
            "$((RANDOM%5))" "$((RANDOM%20))" "$((RANDOM%99))" \
            "$(shuf -n1 -e src/lib.rs src/main.rs core/engine.c net/proto.go)"; sleep 0.08; done'""",
    ]

    def _get_demo_effects(self):
        effects = []
        if shutil.which("cmatrix"):
            effects.append("cmatrix -b -u 2 -C green")
            effects.append("cmatrix -b -u 1 -C red")
        if shutil.which("genact"):
            effects.append("genact -m cargo")
            effects.append("genact -m botnet")
            effects.append("genact -m cryptomining")
        if shutil.which("hollywood"):
            effects.append("hollywood")
        effects.extend(self.DEMO_BASH_EFFECTS)
        random.shuffle(effects)
        return effects[:6]

    def _find_window_by_title(self, title):
        for _ in range(20):
            time.sleep(0.15)
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True
            )
            for line in result.stdout.strip().split("\n"):
                if title in line:
                    return line.split()[0]
        return None

    def _do_demo(self, target, args):
        reply = pick("demo")
        t = self._speak_async(reply)
        self._demo_running = True
        threading.Thread(target=self._run_demo, daemon=True).start()
        if t:
            t.join()
        return None

    def _do_close_demo(self, target, args):
        self._demo_running = False
        # Find and close all demo windows
        result = subprocess.run(
            ["wmctrl", "-l"], capture_output=True, text=True
        )
        closed = 0
        for line in result.stdout.strip().split("\n"):
            if "ORION-DEMO-" in line:
                wid = line.split()[0]
                subprocess.run(["wmctrl", "-i", "-c", wid], capture_output=True)
                closed += 1
                time.sleep(0.2)
        if closed:
            return pick("close_demo")
        return "Nenhuma demonstração ativa, Senhor."

    def _run_demo(self):
        if not shutil.which("xdotool"):
            return

        effects = self._get_demo_effects()
        n = len(effects)
        wids = []
        procs = []

        # Center of the ultrawide (primary monitor)
        cx, cy = 1280, 450
        win_w, win_h = 520, 360

        # Phase 1: Spawn terminals in cascade
        for i, effect in enumerate(effects):
            title = f"ORION-DEMO-{i}"
            proc = subprocess.Popen(
                [
                    "gnome-terminal",
                    f"--title={title}",
                    "--hide-menubar",
                    "--",
                    "bash", "-c", f"{effect}; sleep 999",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            procs.append(proc)
            wid = self._find_window_by_title(title)
            if wid:
                wids.append(wid)
                # Remove maximize, set size, start stacked at center
                subprocess.run(
                    ["xdotool", "windowsize", wid, str(win_w), str(win_h)],
                    capture_output=True,
                )
                subprocess.run(
                    ["xdotool", "windowmove", wid,
                     str(cx - win_w // 2 + i * 30),
                     str(cy - win_h // 2 + i * 20)],
                    capture_output=True,
                )

        if not wids:
            return

        n = len(wids)
        start = time.time()

        # Phase 2 + 3: Animate
        while time.time() - start < self.DEMO_DURATION and self._demo_running:
            t = time.time() - start

            for i, wid in enumerate(wids):
                phase = i * (2 * math.pi / n)

                if t < 3:
                    # Spread out from center
                    progress = t / 3
                    ease = progress * (2 - progress)  # ease-out
                    radius_x = 600 * ease
                    radius_y = 280 * ease
                    angle = phase
                    x = int(cx + radius_x * math.cos(angle) - win_w // 2)
                    y = int(cy + radius_y * math.sin(angle) - win_h // 2)
                elif t > self.DEMO_DURATION - 3:
                    # Collapse back to center
                    remaining = (self.DEMO_DURATION - t) / 3
                    ease = remaining * (2 - remaining)
                    radius_x = 600 * ease
                    radius_y = 280 * ease
                    speed = 1.2
                    angle = phase + t * speed
                    x = int(cx + radius_x * math.cos(angle) - win_w // 2)
                    y = int(cy + radius_y * math.sin(angle) - win_h // 2)
                else:
                    # Orbital juggling with breathing radius
                    speed = 1.2
                    angle = phase + t * speed
                    rx = 600 + 150 * math.sin(t * 0.4)
                    ry = 280 + 80 * math.cos(t * 0.3)
                    x = int(cx + rx * math.cos(angle) - win_w // 2)
                    y = int(cy + ry * math.sin(angle) - win_h // 2)

                x = max(0, min(x, 4200))
                y = max(0, min(y, 1800))

                subprocess.run(
                    ["xdotool", "windowmove", wid, str(x), str(y)],
                    capture_output=True,
                )

            time.sleep(0.03)

        # Phase 4: Distribute terminals evenly on screen
        spacing = (2560 - win_w) // max(n - 1, 1)
        for i, wid in enumerate(wids):
            x = i * spacing
            y = (cy - win_h // 2) + (50 if i % 2 else 0)
            subprocess.run(
                ["xdotool", "windowmove", wid, str(x), str(y)],
                capture_output=True,
            )

    def _do_chat(self, target, args):
        return None
