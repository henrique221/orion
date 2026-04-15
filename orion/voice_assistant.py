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
    r"^[oó]r[iye](?:ão|[oa][nm]?)[,.!?\s]*",
    re.IGNORECASE,
)


class VoiceAssistant:
    def __init__(self, strings, language):
        self._lock = threading.Lock()
        self._running = True
        self._strings = strings

        print(f"\n{strings['terminal']['initializing']}\n")
        self.face = FaceAnimator()
        self.tts = TTS(strings, face=self.face)
        self.recognizer = SpeechRecognizer(strings)
        self.interpreter = CommandInterpreter(strings)
        self.executor = CommandExecutor(
            strings,
            tts=self.tts,
            pause_listening=self._stop_listeners,
            resume_listening=self._start_listeners,
        )
        self.detector = ClapDetector(on_activate=self._on_activate)
        self.wake_word = WakeWordDetector(
            on_activate=self._on_activate,
            whisper_model=self.recognizer.model,
            strings=strings,
        )

    def _stop_listeners(self):
        self.detector.stop()
        self.wake_word.stop()

    def _start_listeners(self):
        self.detector.start()
        self.wake_word.start()
        print(f"\n{self._strings['terminal']['waiting_activation']}\n")

    def _on_activate(self, wake_text=None):
        if not self._lock.acquire(blocking=False):
            return
        try:
            print(f"\n{self._strings['terminal']['activated']}")
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
                self.tts.speak(random.choice(self._strings["listening_phrases"]))
                self._conversation_loop()
        finally:
            if not self.executor._demo_running:
                self._beep()
            self.face.set_state(State.IDLE)
            if self._running and not self.executor._demo_running:
                self._start_listeners()
            self._lock.release()

    def _beep(self):
        """Play a short beep to indicate end of conversation."""
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

    def _conversation_loop(self, initial_text=None):
        """Keep the conversation active until the user goes silent."""
        first = True
        while True:
            if first and initial_text:
                text = initial_text
                first = False
                print(f"  {self._strings['terminal']['you_said']} {text}")
            else:
                first = False
                self.face.set_state(State.LISTENING)
                text = self.recognizer.record_and_transcribe()
                if not text:
                    print(f"  {self._strings['terminal']['no_response']}")
                    return
                print(f"  {self._strings['terminal']['you_said']} {text}")

            if text.strip().lower().rstrip(".!,") in self._strings["stop_words"]:
                print(f"  {self._strings['terminal']['conversation_ended']}")
                self.tts.speak(random.choice(self._strings["stop_responses"]))
                return

            self.face.set_state(State.PROCESSING)
            commands = self.interpreter.interpret(text)
            if not commands:
                self.tts.speak(random.choice(self._strings["error_responses"]))
                return

            interrupted = False
            execution_results = []
            for command in commands:
                print(
                    f"  {self._strings['terminal']['action_label']} "
                    f"{command.get('action')} -> {command.get('target', '')}"
                )

                result = self.executor.execute(command, original_text=text)
                if result == "__END_CONVERSATION__":
                    self.interpreter.record_execution_results(execution_results)
                    return
                response = result or command.get("reply", "")
                execution_results.append(response)
                if response:
                    print(f"  {self._strings['terminal']['response_label']} {response}")
                    self.tts.speak(response)
                    if self.tts.interrupted:
                        print(f"  {self._strings['terminal']['interrupted']}")
                        interrupted = True
                        break
            self.interpreter.record_execution_results(execution_results)
            if interrupted:
                continue

            print(f"  {self._strings['terminal']['waiting_next']}")

    def start(self):
        self.face.setup()
        hour = datetime.datetime.now().hour
        if hour < 12:
            period = "morning"
        elif hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        greeting = random.choice(self._strings["greetings"][period])
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
