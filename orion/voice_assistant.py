import datetime
import random
import sys
import threading

from orion.clap_detector import ClapDetector
from orion.command_executor import CommandExecutor
from orion.command_interpreter import CommandInterpreter
from orion.speech_recognizer import SpeechRecognizer
from orion.tts import TTS
from orion.wake_word_detector import WakeWordDetector

LISTENING_PHRASES = [
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
]


class VoiceAssistant:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = True

        print("\nInicializando Orion...\n")
        self.tts = TTS()
        self.recognizer = SpeechRecognizer()
        self.interpreter = CommandInterpreter()
        self.executor = CommandExecutor(tts=self.tts)
        self.detector = ClapDetector(on_activate=self._on_activate)
        self.wake_word = WakeWordDetector(
            on_activate=self._on_activate,
            whisper_model=self.recognizer.model,
        )

    def _stop_listeners(self):
        self.detector.stop()
        self.wake_word.stop()

    def _start_listeners(self):
        self.detector.start()
        self.wake_word.start()
        print("\nAguardando palmas ou \"hey Orion\"...\n")

    def _on_activate(self):
        if not self._lock.acquire(blocking=False):
            return
        try:
            print("\n>> Ativado!")
            sys.stdout.write("\a")
            sys.stdout.flush()
            self._stop_listeners()
            self.tts.speak(random.choice(LISTENING_PHRASES))
            self._conversation_loop()
        finally:
            if self._running:
                self._start_listeners()
            self._lock.release()

    def _conversation_loop(self):
        """Mantém a conversa ativa até o usuário ficar em silêncio."""
        while True:
            text = self.recognizer.record_and_transcribe()
            if not text:
                print("  Sem resposta, encerrando conversa.")
                self.interpreter.clear_history()
                return
            print(f"  Voce disse: {text}")

            command = self.interpreter.interpret(text)
            if not command:
                self.tts.speak(random.choice([
                    "Houve uma falha no processamento, Senhor.",
                    "Meus sistemas não conseguiram interpretar. Pode repetir?",
                    "Interferência nos meus circuitos. Tente novamente.",
                ]))
                return

            print(
                f"  Acao: {command.get('action')} -> "
                f"{command.get('target', '')}"
            )

            result = self.executor.execute(command, original_text=text)
            response = result or command.get("reply", "")
            if response:
                print(f"  Resposta: {response}")
                self.tts.speak(response)

            print("  Aguardando próximo comando...")

    def start(self):
        hour = datetime.datetime.now().hour
        if hour < 12:
            period = "Bom dia"
        elif hour < 18:
            period = "Boa tarde"
        else:
            period = "Boa noite"
        greeting = f"{period}, senhor Borges. Todos os sistemas operacionais. Aguardando instruções."
        print(f"\n  {greeting}")
        self.tts.speak(greeting)
        self._start_listeners()

    def stop(self):
        self._running = False
        self._stop_listeners()

    @property
    def running(self):
        return self._running
