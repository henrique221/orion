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
