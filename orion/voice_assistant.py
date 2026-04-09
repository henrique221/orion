import datetime
import random
import re
import sys
import threading

from orion.clap_detector import ClapDetector
from orion.command_executor import CommandExecutor
from orion.command_interpreter import CommandInterpreter
from orion.face import FaceAnimator, State
from orion.speech_recognizer import SpeechRecognizer
from orion.tts import TTS
from orion.wake_word_detector import WakeWordDetector

WAKE_WORD_PATTERN = re.compile(
    r"^(?:orion|órion|orian|orião|oriom|oreon|ório|oriam|aurion|oryon)"
    r"[,.!?\s]*",
    re.IGNORECASE,
)

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
        self.face = FaceAnimator()
        self.tts = TTS(face=self.face)
        self.recognizer = SpeechRecognizer()
        self.interpreter = CommandInterpreter()
        self.executor = CommandExecutor(
            tts=self.tts,
            pause_listening=self._stop_listeners,
            resume_listening=self._start_listeners,
        )
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
        print("\nAguardando palmas ou \"Orion\"...\n")

    def _on_activate(self, wake_text=None):
        if not self._lock.acquire(blocking=False):
            return
        try:
            print("\n>> Ativado!")
            sys.stdout.write("\a")
            sys.stdout.flush()
            self._stop_listeners()
            self.face.set_state(State.LISTENING)

            # Extract phrase after wake word (e.g. "orion, tá aí?" → "tá aí?")
            initial_text = None
            if wake_text:
                remaining = WAKE_WORD_PATTERN.sub("", wake_text).strip()
                if remaining:
                    initial_text = remaining

            if initial_text:
                self._conversation_loop(initial_text=initial_text)
            else:
                self.tts.speak(random.choice(LISTENING_PHRASES))
                self._conversation_loop()
        finally:
            if not self.executor._demo_running:
                self._beep()
            self.face.set_state(State.IDLE)
            if self._running and not self.executor._demo_running:
                self._start_listeners()
            self._lock.release()

    def _beep(self):
        """Toca um bip curto para indicar fim da conversa."""
        try:
            import subprocess
            subprocess.Popen(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/message.oga"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            sys.stdout.write("\a")
            sys.stdout.flush()

    STOP_WORDS = ("para", "pare", "parar", "chega", "dispensado")

    def _conversation_loop(self, initial_text=None):
        """Mantém a conversa ativa até o usuário ficar em silêncio."""
        first = True
        while True:
            if first and initial_text:
                text = initial_text
                first = False
                print(f"  Voce disse: {text}")
            else:
                first = False
                self.face.set_state(State.LISTENING)
                text = self.recognizer.record_and_transcribe()
                if not text:
                    print("  Sem resposta, encerrando conversa.")
                    return
                print(f"  Voce disse: {text}")

            if text.strip().lower().rstrip(".!,") in self.STOP_WORDS:
                print("  Conversa encerrada pelo usuário.")
                self.tts.speak(random.choice([
                    "Entendido, Senhor.",
                    "À disposição, Senhor.",
                    "Estarei aqui se precisar.",
                ]))
                return

            self.face.set_state(State.PROCESSING)
            commands = self.interpreter.interpret(text)
            if not commands:
                self.tts.speak(random.choice([
                    "Houve uma falha no processamento, Senhor.",
                    "Meus sistemas não conseguiram interpretar. Pode repetir?",
                    "Interferência nos meus circuitos. Tente novamente.",
                ]))
                return

            interrupted = False
            for command in commands:
                print(
                    f"  Acao: {command.get('action')} -> "
                    f"{command.get('target', '')}"
                )

                result = self.executor.execute(command, original_text=text)
                if result == "__END_CONVERSATION__":
                    return
                response = result or command.get("reply", "")
                if response:
                    print(f"  Resposta: {response}")
                    self.tts.speak(response)
                    if self.tts.interrupted:
                        print("  Interrompido pelo usuário.")
                        interrupted = True
                        break
            if interrupted:
                continue

            print("  Aguardando próximo comando...")

    GREETINGS = {
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
    }

    def start(self):
        self.face.setup()
        hour = datetime.datetime.now().hour
        if hour < 12:
            period = "morning"
        elif hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        greeting = random.choice(self.GREETINGS[period])
        print(f"\n  {greeting}")
        self.tts.speak(greeting)
        self._start_listeners()

    def stop(self):
        self._running = False
        self._stop_listeners()
        self.face.cleanup()

    @property
    def running(self):
        return self._running
