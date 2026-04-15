import base64
import datetime
import math
import os
import random
import select
import shutil
import subprocess
import sys
import termios
import threading
import time
import tty

import requests

from orion.commands import (
    IFTTT_URL,
    MONITORS,
    SAFE_COMMAND_PREFIXES,
    SMART_HOME_DEVICES,
    VISION_MODEL,
)

class CommandExecutor:
    def __init__(self, strings, tts=None, pause_listening=None, resume_listening=None):
        self._strings = strings
        self._tts = tts
        self._pause_listening = pause_listening
        self._resume_listening = resume_listening
        self._pending_shutdown = False
        self._demo_running = False
        self._byobu_wid = None

    def _pick(self, action, variant="success", **kwargs):
        from orion.commands import pick
        return pick(self._strings, action, variant, **kwargs)

    def execute(self, command, original_text=""):
        if not command:
            return self._strings["terminal"]["no_command"]

        # Handle pending shutdown confirmation
        if self._pending_shutdown:
            self._pending_shutdown = False
            text = original_text.lower().strip()
            if any(w in text for w in self._strings["executor"]["shutdown_confirm_words"]):
                return self._execute_shutdown()
            return self._pick("shutdown", "cancelled")

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
        app = self._strings["app_map"].get(target.lower(), target)
        try:
            subprocess.Popen(
                [app],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return self._pick("open_app", "success", target=target.capitalize())
        except FileNotFoundError:
            return self._strings["terminal"]["app_not_found"].format(target=target)

    def _do_close_app(self, target, args):
        app = self._strings["app_map"].get(target.lower(), target)
        try:
            subprocess.run(["wmctrl", "-c", target], capture_output=True)
            return self._pick("close_app", "success", target=target.capitalize())
        except FileNotFoundError:
            try:
                subprocess.run(["pkill", "-f", app], capture_output=True)
                return self._pick("close_app", "success", target=target.capitalize())
            except Exception:
                return self._strings["terminal"]["close_app_error"].format(target=target)

    def _do_open_url(self, target, args):
        url = target if target.startswith("http") else f"https://{target}"
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return self._pick("open_url", "success", target=target)

    def _do_search_web(self, target, args):
        t = self._speak_async(self._pick("search_web", "loading", target=target))

        # Open browser
        query = target.replace(" ", "+")
        url = f"https://www.google.com/search?q={query}"
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Fetch results in parallel
        snippets = self._fetch_search_results(target)
        if t:
            t.join()

        if not snippets:
            return self._strings["terminal"]["search_browser_fallback"]

        # Summarize with LLM
        question = self._original_text
        try:
            import re
            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": self._strings["executor"]["search_summary_prompt"].format(
                        query=target, snippets=snippets, question=question
                    ),
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0.3, "num_predict": 200},
                },
                timeout=20,
            )
            text = r.json()["response"].strip()
            text = re.sub(r"[*#_~`>|]", "", text)
            return text
        except Exception as e:
            print(f"  {self._strings['terminal']['search_error'].format(error=e)}")
            return self._strings["terminal"]["search_fallback"]

    DUCKDUCKGO_URL = "https://lite.duckduckgo.com/lite/"

    def _fetch_search_results(self, query):
        """Fetches search snippets from DuckDuckGo Lite."""
        import re
        try:
            r = requests.post(
                self.DUCKDUCKGO_URL,
                data={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            r.raise_for_status()
            html = r.text

            # Extract snippets from DuckDuckGo Lite HTML
            # Snippets are in <td class="result-snippet"> tags
            snippets = re.findall(
                r'<td\s+class="result-snippet">(.*?)</td>',
                html, re.DOTALL,
            )
            # Extract titles
            titles = re.findall(
                r'<a\s+rel="nofollow"\s+href="[^"]*"\s+class="result-link">(.*?)</a>',
                html, re.DOTALL,
            )

            results = []
            for i, (title, snippet) in enumerate(zip(titles, snippets), 1):
                # Clean HTML tags
                clean_title = re.sub(r"<[^>]+>", "", title).strip()
                clean_snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                if clean_title and clean_snippet:
                    results.append(f"{i}. {clean_title}: {clean_snippet}")
                if i >= 5:
                    break

            return "\n".join(results)
        except Exception as e:
            print(f"  {self._strings['terminal']['search_results_error'].format(error=e)}")
            return ""

    def _do_volume_up(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{pct}%"],
            capture_output=True,
        )
        return self._pick("volume_up")

    def _do_volume_down(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{pct}%"],
            capture_output=True,
        )
        return self._pick("volume_down")

    def _do_mute(self, target, args):
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
            capture_output=True,
        )
        return self._pick("mute")

    def _do_screenshot(self, target, args):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/screenshot_{ts}.png")
        result = subprocess.run(
            ["gnome-screenshot", "-f", path], capture_output=True
        )
        if result.returncode == 0:
            return self._pick("screenshot")
        result = subprocess.run(["scrot", path], capture_output=True)
        if result.returncode == 0:
            return self._pick("screenshot")
        return self._strings["terminal"]["screenshot_fail"]

    def _do_show_time(self, target, args):
        now = datetime.datetime.now()
        h, m = now.hour, now.minute
        if m == 0:
            return self._strings["terminal"]["time_exact"].format(h=h)
        return self._strings["terminal"]["time_normal"].format(h=h, m=m)

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
                return self._strings["terminal"]["windows_listing"].format(listing=listing)
            return self._strings["terminal"]["no_windows"]
        except FileNotFoundError:
            return self._strings["terminal"]["wmctrl_missing"]

    def _do_run_command(self, target, args):
        cmd = target.strip()
        if not any(cmd.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES):
            return self._strings["terminal"]["command_blocked"].format(cmd=cmd)
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout.strip()
            return output if output else self._strings["terminal"]["command_executed"]
        except subprocess.TimeoutExpired:
            return self._strings["terminal"]["command_timeout"]

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

        # Desabilitar interrupção durante abertura dos workspaces
        if self._tts:
            self._tts.allow_interrupt = False

        try:
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
            t = self._speak_async(self._pick("start_work", "loading"))

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
            return self._pick("start_work", "done")
        finally:
            if self._tts:
                self._tts.allow_interrupt = True

    def _motivational_quote(self):
        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": self._strings["executor"]["motivational_prompt"],
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0.9, "num_predict": 25},
                },
                timeout=15,
            )
            phrase = r.json()["response"].strip().strip('"')
            return phrase
        except Exception:
            return self._pick("start_work", "done")

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
        return self._pick("close_all")

    def _do_switch_workspace(self, target, args):
        import re
        # Extrai o primeiro número de target, args ou texto original
        match = re.search(r"\d+", f"{target} {args} {self._original_text}")
        if not match:
            return self._strings["terminal"]["workspace_invalid"]
        num = int(match.group()) - 1
        subprocess.run(["wmctrl", "-s", str(num)], capture_output=True)
        return self._pick("switch_workspace", "success", num=num + 1)

    WEATHER_LOCATION = "Conceição da Aparecida"

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
            parts.append(self._strings["terminal"]["weather_unavailable"].format(days=day_index))

        return " ".join(parts)

    def _do_weather(self, target, args):
        t = self._speak_async(self._pick("weather", "loading"))
        location = target.strip() if target else ""
        day_index = self._resolve_day_index(args)
        question = self._original_text

        # Try wttr.in first, fallback to DuckDuckGo
        try:
            weather_data = self._fetch_weather(location, day_index)
        except Exception as e:
            print(f"  {self._strings['terminal']['weather_error'].format(error=e)}")
            loc = location or self.WEATHER_LOCATION
            weather_data = self._fetch_search_results(
                self._strings["executor"]["weather_fallback_query"].format(location=loc)
            )

        if t:
            t.join()

        if not weather_data:
            return self._strings["terminal"]["weather_fail"]

        try:
            import re
            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": self._strings["executor"]["weather_summary_prompt"].format(
                        data=weather_data, question=question
                    ),
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0.3, "num_predict": 80},
                },
                timeout=15,
            )
            text = r.json()["response"].strip()
            text = re.sub(r"[*#_~`>|]", "", text)
            return text
        except Exception as e:
            print(f"  {self._strings['terminal']['weather_error'].format(error=e)}")
            return self._strings["terminal"]["weather_fail"]


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
        t = self._speak_async(self._pick("news", "loading"))
        query = target.strip() if target else ""
        question = self._original_text

        # Try RSS first, fallback to DuckDuckGo
        try:
            headlines = self._fetch_news(query)
        except Exception as e:
            print(f"  {self._strings['terminal']['news_error'].format(error=e)}")
            if query:
                search_query = self._strings["executor"]["news_fallback_query"].format(query=query)
            else:
                search_query = self._strings["executor"]["news_default_query"]
            headlines = self._fetch_search_results(search_query)

        if t:
            t.join()

        if not headlines:
            return self._strings["terminal"]["news_fail"]

        try:
            import re
            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": self._strings["executor"]["news_summary_prompt"].format(
                        headlines=headlines, question=question
                    ),
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0.3, "num_predict": 150},
                },
                timeout=15,
            )
            text = r.json()["response"].strip()
            text = re.sub(r"[*#_~`>|]", "", text)
            return text
        except Exception as e:
            print(f"  {self._strings['terminal']['news_error'].format(error=e)}")
            return self._strings["terminal"]["news_fail"]

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
        return self._pick("unlock_screen")

    def _do_lock_screen(self, target, args):
        subprocess.Popen(
            ["loginctl", "lock-session"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return self._pick("lock_screen")

    def _do_shutdown(self, target, args):
        self._pending_shutdown = True
        return self._pick("shutdown", "confirm")

    def _execute_shutdown(self):
        reply = self._pick("shutdown")
        if self._tts:
            self._tts.speak(reply)
        time.sleep(1)
        subprocess.Popen(["systemctl", "poweroff"])
        return None

    def _do_restart(self, target, args):
        reply = self._pick("restart")
        if self._tts:
            self._tts.speak(reply)
        time.sleep(1)
        subprocess.Popen(["systemctl", "reboot"])
        return None

    def _do_suspend(self, target, args):
        reply = self._pick("suspend")
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
        return self._pick("brightness_up")

    def _do_brightness_down(self, target, args):
        pct = args if args else "10"
        subprocess.run(
            ["brightnessctl", "set", f"{pct}%-"],
            capture_output=True,
        )
        return self._pick("brightness_down")

    def _do_battery(self, target, args):
        try:
            result = subprocess.run(
                ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.split("\n"):
                if "percentage" in line:
                    pct = line.split(":")[-1].strip()
                    return self._strings["terminal"]["battery_info"].format(pct=pct)
            return self._strings["terminal"]["battery_unavailable"]
        except Exception:
            return self._strings["terminal"]["battery_error"]

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
            return self._strings["terminal"]["system_info_template"].format(
                uptime=uptime.replace("up ", ""),
                mem_used=mem_used,
                mem_total=mem_total,
                disk_pct=disk_pct,
            )
        except Exception:
            return self._strings["terminal"]["system_info_error"]

    def _do_empty_trash(self, target, args):
        subprocess.run(
            ["gio", "trash", "--empty"],
            capture_output=True,
        )
        return self._pick("empty_trash")

    def _do_timer(self, target, args):
        import re
        raw = f"{target} {args} {self._original_text}"
        match = re.search(r"(\d+)", raw)
        if not match:
            return self._strings["terminal"]["timer_no_duration"]
        value = int(match.group(1))
        timer_words = self._strings["executor"]["timer_words"]
        if any(w in raw.lower() for w in timer_words["hours"]):
            seconds = value * 3600
            label = f"{value} hora{'s' if value > 1 else ''}"
        elif any(w in raw.lower() for w in timer_words["seconds"]):
            seconds = value
            label = f"{value} segundo{'s' if value > 1 else ''}"
        else:
            seconds = value * 60
            label = f"{value} minuto{'s' if value > 1 else ''}"

        def _alarm():
            time.sleep(seconds)
            if self._tts:
                self._tts.speak(self._strings["terminal"]["timer_expired"].format(duration=label))
            subprocess.run(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
                capture_output=True,
            )

        threading.Thread(target=_alarm, daemon=True).start()
        return self._pick("timer", "success", duration=label)

    def _do_logout(self, target, args):
        reply = self._pick("logout")
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
            return self._strings["terminal"]["device_not_found"].format(target=target)
        event = device_info.get(state)
        if not event:
            return self._strings["terminal"]["device_action_invalid"].format(args=args, target=target)
        try:
            r = requests.get(IFTTT_URL.format(event=event), timeout=10)
            r.raise_for_status()
            label = target.capitalize()
            return self._pick("smart_home", state, device=label)
        except Exception:
            return self._pick("smart_home", "error", device=target.capitalize())

    # ── Analyze screen ──────────────────────────────────────────

    OLLAMA_URL = "http://localhost:11434"
    LLM_MODEL = "qwen2.5:1.5b"

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
            name = self._strings["monitors"].get(name, name)
            if name and name not in MONITORS:
                return self._strings["terminal"]["monitor_not_found"].format(target=target)

        try:
            # Stage 1: Capture
            self._speak_sync(self._pick("analyze_screen", "capturing"))

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
                return self._strings["terminal"]["screen_capture_fail"]

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
                return self._strings["terminal"]["screen_capture_fail"]

            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()

            # Stage 2: Swap models — liberar VRAM para o modelo de visão
            self._speak_sync(self._pick("analyze_screen", "swapping"))
            print(f"  {self._strings['terminal']['vision_freeing_vram']}")
            requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={"model": self.LLM_MODEL, "keep_alive": 0},
                timeout=10,
            )
            if self._tts:
                self._tts.free_vram()
            time.sleep(1)

            # Stage 3: Analyze — vision model extracts all text/content
            self._speak_sync(self._pick("analyze_screen", "analyzing"))
            print(f"  {self._strings['terminal']['vision_loading'].format(model=VISION_MODEL)}")
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
            print(f"  {self._strings['terminal']['vision_raw'].format(analysis=analysis)}")

            # Stage 4: Restore models
            self._speak_sync(self._pick("analyze_screen", "restoring"))
            print(f"  {self._strings['terminal']['vision_restoring']}")
            requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={"model": VISION_MODEL, "keep_alive": 0},
                timeout=10,
            )
            time.sleep(1)
            if self._tts:
                self._tts.reclaim_vram()
            print(f"  {self._strings['terminal']['vision_restored']}")

            os.remove(img_path)

            # Stage 5: LLM answers the user's question using the extracted content
            import re
            question = self._original_text
            task = args.strip().lower() if args else ""

            task_instructions = self._strings["executor"]["screen_task_instructions"]
            task_hint = task_instructions.get(task, self._strings["executor"]["screen_task_default"])

            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": self._strings["executor"]["screen_analysis_prompt"].format(
                        analysis=analysis, question=question, task_hint=task_hint
                    ),
                    "stream": False,
                    "keep_alive": 0,
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
            return self._strings["terminal"]["screen_analysis_fail"]

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
        self._speak_sync(self._pick("analyze_selection", "loading"))

        selected = self._get_selected_text()

        if not selected:
            return self._pick("analyze_selection", "empty")

        print(f"  {self._strings['terminal']['selection_chars'].format(count=len(selected), preview=selected[:100])}")

        import re
        question = self._original_text
        task = args.strip().lower() if args else ""

        task_instructions = self._strings["executor"]["selection_task_instructions"]
        task_hint = task_instructions.get(task, self._strings["executor"]["selection_task_default"])

        try:
            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": self._strings["executor"]["selection_analysis_prompt"].format(
                        selected=selected, question=question, task_hint=task_hint
                    ),
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0.3, "num_predict": 300},
                },
                timeout=20,
            )
            text = r.json()["response"].strip()
            text = re.sub(r"[*#_~`>|]", "", text)
            return text
        except Exception as e:
            print(f"  Erro na análise de seleção: {e}")
            return self._strings["terminal"]["selection_analysis_fail"]

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
                    "keep_alive": 0,
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=30,
            )
        except Exception:
            pass

    # ── Demo hacker ──────────────────────────────────────────────

    DEMO_DURATION = 30
    DEMO_MUSIC_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "demo.mp3")

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
        self._demo_running = True
        self._demo_wids = []
        self._byobu_wid = None
        threading.Thread(target=self._run_demo, daemon=True).start()
        return "__END_CONVERSATION__"

    def _find_sink_input(self, app_name):
        """Find a sink input index by application name."""
        try:
            result = subprocess.run(
                ["pactl", "list", "sink-inputs"],
                capture_output=True, text=True, timeout=3,
            )
            current_idx = None
            for line in result.stdout.split("\n"):
                if "Sink Input #" in line:
                    current_idx = line.split("#")[1].strip()
                if current_idx and app_name in line.lower():
                    return current_idx
        except Exception:
            pass
        return None

    def _fade_out_demo_music(self):
        """Fade out music over ~3 seconds then kill."""
        proc = getattr(self, "_demo_music_proc", None)
        if not proc:
            return
        # Fade volume down via PipeWire sink input
        idx = self._find_sink_input("pw-play") or self._find_sink_input("pw-cat")
        if idx:
            for vol in range(100, -1, -5):  # 100% → 0% in 5% steps
                subprocess.run(
                    ["pactl", "set-sink-input-volume", idx, f"{vol}%"],
                    capture_output=True,
                )
                time.sleep(0.15)  # ~3s total
            # Restore to 100% BEFORE killing so stream-restore saves 100%
            subprocess.run(
                ["pactl", "set-sink-input-volume", idx, "100%"],
                capture_output=True,
            )
            time.sleep(0.1)
        # Kill the process group
        try:
            os.killpg(os.getpgid(proc.pid), 9)
        except (ProcessLookupError, OSError):
            pass
        self._demo_music_proc = None

    def _do_close_demo(self, target, args):
        self._demo_running = False
        time.sleep(0.5)
        self._fade_out_demo_music()
        self._close_demo_windows()
        self._restore_demo_volume()
        if self._resume_listening:
            self._resume_listening()
        return self._pick("close_demo")

    def _get_window_ids(self):
        """Returns set of current window IDs."""
        result = subprocess.run(
            ["wmctrl", "-l"], capture_output=True, text=True
        )
        return {line.split()[0] for line in result.stdout.strip().split("\n") if line.strip()}

    def _track_new_window(self, before_ids, timeout=5):
        """Waits for a new window to appear and tracks its ID."""
        for _ in range(int(timeout / 0.2)):
            time.sleep(0.2)
            after_ids = self._get_window_ids()
            new = after_ids - before_ids
            if new:
                wid = new.pop()
                self._demo_wids.append(wid)
                return wid
        return None

    def _watch_esc_key(self):
        """Monitors for ESC key press to interrupt demo."""
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while self._demo_running:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        ch = sys.stdin.read(1)
                        if ch == '\x1b':  # ESC
                            print("\n  [Demo interrompida por ESC]")
                            self._demo_running = False
                            return
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass

    def _close_demo_windows(self):
        # Close only windows we opened — try graceful, then force
        for wid in getattr(self, "_demo_wids", []):
            subprocess.run(["wmctrl", "-i", "-c", wid], capture_output=True)
            time.sleep(0.15)
        time.sleep(0.5)
        # Force-kill any that survived
        for wid in getattr(self, "_demo_wids", []):
            # Get PID from window ID and kill
            result = subprocess.run(
                ["xdotool", "getwindowpid", wid],
                capture_output=True, text=True,
            )
            pid = result.stdout.strip()
            if pid:
                try:
                    os.kill(int(pid), 9)
                except (ProcessLookupError, OSError, ValueError):
                    pass
        # Also kill any leftover byobu session
        subprocess.run(["byobu", "kill-server"], capture_output=True)
        self._demo_wids = []

    def _demo_speak(self, text):
        if self._demo_running and self._tts:
            self._tts.speak(text)

    def _demo_wait(self, seconds):
        for _ in range(int(seconds * 10)):
            if not self._demo_running:
                return False
            time.sleep(0.1)
        return self._demo_running

    def _demo_open_and_close(self, cmd, wait_time=3, kill_proc=False):
        """Opens something, waits, then closes only the window it opened."""
        before = self._get_window_ids()
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        wid = self._track_new_window(before, timeout=wait_time + 2)
        if not self._demo_wait(wait_time):
            return
        if wid:
            subprocess.run(["wmctrl", "-i", "-c", wid], capture_output=True)
            if wid in self._demo_wids:
                self._demo_wids.remove(wid)
        if kill_proc:
            try:
                os.killpg(os.getpgid(proc.pid), 9)
            except (ProcessLookupError, OSError):
                pass

    DEMO_VOLUME_MUSIC = 18       # pw-play volume (0-100) for background music
    DEMO_VOLUME_VOICE = "160%"  # TTS voice volume during demo


    def _save_and_set_demo_volume(self):
        """Saves current volume and sets demo volumes."""
        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True, timeout=3,
            )
            # Extract percentage, e.g. "Volume: front-left: 65536 / 100% / ..."
            import re
            match = re.search(r"(\d+)%", result.stdout)
            self._pre_demo_volume = match.group(0) if match else "100%"
        except Exception:
            self._pre_demo_volume = "100%"

        # Set main volume high for TTS voice
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", self.DEMO_VOLUME_VOICE],
            capture_output=True,
        )

    def _restore_demo_volume(self):
        """Restores volume to pre-demo level."""
        vol = getattr(self, "_pre_demo_volume", "100%")
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", vol],
            capture_output=True,
        )

    def _animate_terminals(self, wids, cx, cy, win_w, win_h):
        """Runs orbital animation until self._anim_running is False."""
        n = len(wids)
        start = time.time()
        while self._anim_running and self._demo_running:
            t = time.time() - start
            for i, wid in enumerate(wids):
                phase = i * (2 * math.pi / n)
                if t < 3:
                    progress = t / 3
                    ease = progress * (2 - progress)
                    rx, ry = 600 * ease, 280 * ease
                    angle = phase
                else:
                    angle = phase + t * 1.2
                    rx = 600 + 150 * math.sin(t * 0.4)
                    ry = 280 + 80 * math.cos(t * 0.3)
                x = max(0, min(int(cx + rx * math.cos(angle) - win_w // 2), 4200))
                y = max(0, min(int(cy + ry * math.sin(angle) - win_h // 2), 1800))
                subprocess.run(
                    ["xdotool", "windowmove", wid, str(x), str(y)],
                    capture_output=True,
                )
            time.sleep(0.03)

    def _run_demo(self):
        if not shutil.which("xdotool"):
            return

        # ── Play background music immediately ─────────────────
        # Convert MP3 → WAV once, then loop with paplay (ffplay SDL fails in subprocess)
        self._demo_music_proc = None
        self._demo_wav = "/tmp/orion_demo_music.wav"
        if os.path.isfile(self.DEMO_MUSIC_PATH):
            if not os.path.isfile(self._demo_wav):
                subprocess.run(
                    ["ffmpeg", "-y", "-i", self.DEMO_MUSIC_PATH,
                     "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
                     self._demo_wav],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            if os.path.isfile(self._demo_wav):
                # pw-play: PipeWire native, supports --volume, no stream-restore issues
                vol = self.DEMO_VOLUME_MUSIC / 100.0  # pw-play uses 0.0-1.0
                self._demo_music_proc = subprocess.Popen(
                    ["bash", "-c",
                     f'while true; do pw-play --volume={vol} "{self._demo_wav}"; done'],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )

        # Watch for ESC key to interrupt
        threading.Thread(target=self._watch_esc_key, daemon=True).start()

        try:
            self._run_demo_acts()
        finally:
            self._demo_running = False
            self._fade_out_demo_music()
            self._close_demo_windows()
            self._restore_demo_volume()
            if self._tts:
                self._tts.allow_interrupt = True
            if self._resume_listening:
                self._resume_listening()

    def _run_demo_acts(self):
        # Disable speech interruption during demo
        # (listeners already stopped by voice_assistant._on_activate)
        if self._tts:
            self._tts.allow_interrupt = False

        # Save volume and boost for demo
        self._save_and_set_demo_volume()

        # ── Spawn byobu (stays open the whole demo) ───────────
        if shutil.which("byobu"):
            subprocess.run(["byobu", "kill-server"], capture_output=True)
            # Create byobu session with split panes showing system activity
            setup = (
                "byobu new-session -d -s orion-demo \\; "
                "send-keys 'htop' Enter \\; "
                "split-window -h \\; "
                "send-keys 'watch -n1 -c sensors 2>/dev/null || watch -n1 free -h' Enter \\; "
                "split-window -v \\; "
                "send-keys 'dmesg -wH 2>/dev/null || journalctl -f' Enter \\; "
                "select-pane -t 0 \\; "
                "split-window -v \\; "
                "send-keys 'sudo iotop -o 2>/dev/null || iostat -x 1 2>/dev/null || vmstat 1' Enter \\; "
                "&& byobu attach -t orion-demo"
            )
            subprocess.Popen(
                ["gnome-terminal", "--title=ORION-BYOBU", "--hide-menubar",
                 "--geometry=200x50+0+0",
                 "--", "bash", "-c", f"{setup}; sleep 999"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            wid = self._find_window_by_title("ORION-BYOBU")
            if wid:
                self._byobu_wid = wid
                self._demo_wids.append(wid)
                # Force window to ultrawide monitor at x=0 and maximize
                subprocess.run(
                    ["wmctrl", "-i", "-r", wid, "-b", "remove,maximized_vert,maximized_horz"],
                    capture_output=True,
                )
                time.sleep(0.2)
                subprocess.run(
                    ["xdotool", "windowactivate", "--sync", wid],
                    capture_output=True,
                )
                subprocess.run(
                    ["xdotool", "windowmove", "--sync", wid, "0", "0"],
                    capture_output=True,
                )
                subprocess.run(
                    ["xdotool", "windowsize", "--sync", wid, "2560", "1048"],
                    capture_output=True,
                )
                time.sleep(0.5)
                subprocess.run(
                    ["wmctrl", "-i", "-r", wid, "-b", "add,maximized_vert,maximized_horz"],
                    capture_output=True,
                )

        # Spawn effect terminals
        before = self._get_window_ids()
        effects = self._get_demo_effects()
        term_wids = []
        cx, cy = 1280, 450
        win_w, win_h = 520, 360

        for i, effect in enumerate(effects):
            title = f"ORION-DEMO-{i}"
            subprocess.Popen(
                ["gnome-terminal", f"--title={title}", "--hide-menubar",
                 "--", "bash", "-c", f"{effect}; sleep 999"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        # Wait for terminals to appear and collect their window IDs
        expected = len(effects)
        for _ in range(30):  # up to 3s
            time.sleep(0.1)
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True
            )
            found = 0
            for line in result.stdout.strip().split("\n"):
                if "ORION-DEMO-" in line and "BYOBU" not in line:
                    wid = line.split()[0]
                    if wid not in before and wid not in term_wids:
                        found += 1
            if found >= expected:
                break

        result = subprocess.run(
            ["wmctrl", "-l"], capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            if "ORION-DEMO-" in line and "BYOBU" not in line:
                wid = line.split()[0]
                if wid not in before:
                    term_wids.append(wid)
                    self._demo_wids.append(wid)

        # Position terminals
        for i, wid in enumerate(term_wids):
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

        # ── Act 1: Terminals + narration in parallel ────────────
        if term_wids:
            self._anim_running = True
            anim = threading.Thread(
                target=self._animate_terminals,
                args=(term_wids, cx, cy, win_w, win_h),
                daemon=True,
            )
            anim.start()

            self._demo_speak(
                "Bom dia, Senhor. Todos os sistemas estão operacionais. "
                "Permitam-me apresentar o Projeto Orion. "
                "Fui criado pelo Senhor Henrique Borges com um único propósito: "
                "maximizar a produtividade. "
                "Uma inteligência artificial autônoma, construída para operar "
                "inteiramente offline, sem depender de servidores externos. "
                "Tudo roda aqui, nesta máquina."
            )
            if not self._demo_running:
                self._anim_running = False
                return

            self._demo_speak(
                "Neste momento, múltiplos processos estão sendo executados em paralelo. "
                "Análise de rede, compilação de módulos, processamento neural em tempo real. "
                "Eu escuto, interpreto e ajo. Sem atrasos. Sem intermediários."
            )
            if not self._demo_running:
                self._anim_running = False
                return

            self._demo_speak(
                "Canais seguros estabelecidos. Monitoramento de perímetro digital ativo. "
                "Todos os protocolos operando dentro dos parâmetros esperados. "
                "Inicialização completa, Senhor. Pronto para demonstração."
            )

            self._anim_running = False
            anim.join(timeout=2)
            for wid in term_wids:
                subprocess.run(["wmctrl", "-i", "-c", wid], capture_output=True)
                if wid in self._demo_wids:
                    self._demo_wids.remove(wid)
                time.sleep(0.15)

        if not self._demo_running:
            return

        # ── Act 2: Web search ───────────────────────────────────
        self._demo_speak(
            "Tenho acesso completo à internet. Posso pesquisar, ler e resumir "
            "qualquer informação em segundos. Observe."
        )
        if not self._demo_running:
            return
        self._demo_open_and_close(
            ["google-chrome", "--new-window",
             "https://www.google.com/search?q=inteligência+artificial+2026"],
            wait_time=2,
        )
        if not self._demo_running:
            return
        self._demo_speak(
            "Resultados obtidos e processados. "
            "Notícias, clima, qualquer pergunta, eu encontro a resposta."
        )
        if not self._demo_running:
            return

        # ── Act 3: Open apps ────────────────────────────────────
        self._demo_speak(
            "Também controlo todos os aplicativos do sistema. "
            "Basta um comando de voz. Vou abrir o Zoom como exemplo."
        )
        if not self._demo_running:
            return

        zoom_cmd = "zoom"
        if not shutil.which(zoom_cmd):
            zoom_cmd = "gnome-calculator"
        self._demo_open_and_close([zoom_cmd], wait_time=2, kill_proc=True)
        if not self._demo_running:
            return
        self._demo_speak(
            "Aberto e encerrado em segundos. Qualquer aplicativo, a qualquer momento."
        )
        if not self._demo_running:
            return

        # ── Act 4: Work environment ─────────────────────────────
        self._demo_speak(
            "Agora, algo mais sofisticado. Com uma única instrução, "
            "eu monto o ambiente de trabalho completo. Editor, projeto, tudo pronto."
        )
        if not self._demo_running:
            return

        before = self._get_window_ids()
        subprocess.Popen(
            ["cursor", "--new-window", os.path.expanduser("~/gitdocs/skyportal-website")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        cursor_wid = self._track_new_window(before, timeout=5)
        self._demo_speak(
            "Projeto Sky Portal carregado no Cursor. "
            "Ambiente de desenvolvimento configurado e operacional."
        )
        if not self._demo_running:
            return
        if cursor_wid:
            subprocess.run(["wmctrl", "-i", "-c", cursor_wid], capture_output=True)
            if cursor_wid in self._demo_wids:
                self._demo_wids.remove(cursor_wid)

        if not self._demo_running:
            return

        # ── Act 5: Vision & analysis ────────────────────────────
        self._demo_speak(
            "Meus recursos vão além de comandos simples. "
            "Eu enxergo o que está na tela. Posso analisar imagens, traduzir textos, "
            "resumir documentos e explicar qualquer conteúdo visível."
        )
        if not self._demo_running:
            return

        # ── Act 6: Smart home ───────────────────────────────────
        self._demo_speak(
            "E não me limito ao computador. "
            "Eu controlo dispositivos inteligentes da casa inteira. "
            "Luzes, climatização, piscina. Tudo responde à minha voz."
        )
        if not self._demo_running:
            return

        # ── Act 7: Finale ──────────────────────────────────────
        self._demo_speak(
            "Pesquisa inteligente, automação completa, visão computacional, "
            "controle residencial, e tudo isso sem conexão com nuvem. "
            "Eu sou o Orion. E estou sempre à disposição, Senhor."
        )

    def _do_chat(self, target, args):
        """Gera resposta conversacional usando o LLM."""
        try:
            prompt = (
                "Você é Orion, IA inspirada no J.A.R.V.I.S. do Tony Stark. "
                "Tom: formal britânico com humor seco e sutil. "
                "Trate o usuário por 'Senhor' ou 'senhor Borges'. "
                "Nunca use emojis. "
                f"O usuário disse: \"{self._original_text}\"\n"
                "Responda de forma natural, inteligente e concisa (máximo 30 palavras). "
                "Apenas o texto da resposta falada, sem aspas, sem JSON."
            )
            r = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0.7, "num_predict": 80},
                },
                timeout=15,
            )
            r.raise_for_status()
            response = r.json().get("response", "").strip().strip('"\'')
            if response and len(response) > 5:
                return response
        except Exception as e:
            print(f"  Erro no chat: {e}")
        return None
