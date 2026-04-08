import signal
import sys
import time

from orion.voice_assistant import VoiceAssistant

BANNER = r"""
   ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
  ██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
  ██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
  ██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
  ╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
   ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝

  Assistente de Voz Local - 100%% Offline
"""


def main():
    print(BANNER)

    assistant = VoiceAssistant()

    def shutdown(sig, frame):
        print("\n\nEncerrando Orion...")
        assistant.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        assistant.start()

        while assistant.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        assistant.stop()

    print("Orion encerrado.\n")


if __name__ == "__main__":
    main()
