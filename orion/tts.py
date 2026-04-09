import os
import shutil
import subprocess
import time

import numpy as np
import sounddevice as sd


class TTS:
    KOKORO_MODEL = os.path.expanduser(
        "~/.local/share/kokoro/kokoro-v1.0.fp16.onnx"
    )
    KOKORO_VOICES = os.path.expanduser(
        "~/.local/share/kokoro/voices-v1.0.bin"
    )
    KOKORO_VOICE = "pm_alex"
    KOKORO_PITCH_SHIFT = 0.88
    KOKORO_SPEED = 1.35
    KOKORO_RATE = 24000

    PIPER_BIN = os.path.expanduser("~/.local/bin/piper")
    PIPER_LIB = os.path.expanduser("~/.local/bin")
    PIPER_MODEL = os.path.expanduser(
        "~/.local/share/piper/pt_BR-faber-medium.onnx"
    )

    def __init__(self, face=None):
        self._kokoro = None
        self._g2p = None
        self._use_piper = False
        self.interrupted = False
        self.allow_interrupt = True
        self._face = face

        if os.path.isfile(self.KOKORO_MODEL) and os.path.isfile(
            self.KOKORO_VOICES
        ):
            try:
                from kokoro_onnx import Kokoro
                from misaki.espeak import EspeakG2P

                print("  Carregando Kokoro TTS...")
                self._kokoro = Kokoro(self.KOKORO_MODEL, self.KOKORO_VOICES)
                self._g2p = EspeakG2P(language="pt-br")
                print("  TTS: Kokoro pronto.")
            except Exception as e:
                print(f"  Kokoro indisponível ({e}), tentando Piper...")

        if self._kokoro is None:
            self._use_piper = os.path.isfile(
                self.PIPER_BIN
            ) and os.path.isfile(self.PIPER_MODEL)
            self._piper_env = os.environ.copy()
            ld = self._piper_env.get("LD_LIBRARY_PATH", "")
            self._piper_env["LD_LIBRARY_PATH"] = (
                f"{self.PIPER_LIB}:{ld}" if ld else self.PIPER_LIB
            )
            if self._use_piper:
                print("  TTS: Piper pronto (fallback).")
            elif shutil.which("espeak-ng"):
                print("  TTS: espeak-ng (fallback).")
            else:
                print("  AVISO: Nenhum TTS disponível.")

    def speak(self, text):
        if not text:
            return
        if self._kokoro:
            self._speak_kokoro(text)
        elif self._use_piper:
            self._speak_piper(text)
        else:
            self._speak_espeak(text)

    INTERRUPT_THRESHOLD = 0.15
    INTERRUPT_SAMPLE_RATE = 16000
    INTERRUPT_CHUNK = 1600  # 100ms
    INTERRUPT_CONSECUTIVE = 3  # chunks consecutivos acima do threshold

    def _speak_kokoro(self, text):
        try:
            from scipy.signal import resample

            phonemes, _ = self._g2p(text)
            samples, sr = self._kokoro.create(
                phonemes, voice=self.KOKORO_VOICE, speed=self.KOKORO_SPEED,
                is_phonemes=True,
            )
            new_len = int(len(samples) / self.KOKORO_PITCH_SHIFT)
            samples = resample(samples, new_len).astype(np.float32)
            self.interrupted = False
            if self._face:
                from orion.face import State
                self._face.set_state(State.SPEAKING)
            sd.play(samples, sr)
            if self.allow_interrupt:
                self._monitor_for_interrupt(len(samples) / sr)
            else:
                sd.wait()
            if self._face:
                from orion.face import State
                self._face.set_state(State.IDLE)
        except Exception as e:
            print(f"  Erro Kokoro: {e}, usando fallback.")
            if self._use_piper:
                self._speak_piper(text)
            else:
                self._speak_espeak(text)

    def _monitor_for_interrupt(self, duration):
        """Monitora o microfone durante a fala. Se detectar voz, para."""
        start = time.time()
        grace_period = 0.5
        consecutive = 0
        try:
            with sd.InputStream(
                samplerate=self.INTERRUPT_SAMPLE_RATE,
                channels=1,
                blocksize=self.INTERRUPT_CHUNK,
            ) as mic:
                while time.time() - start < duration:
                    data, _ = mic.read(self.INTERRUPT_CHUNK)
                    if time.time() - start < grace_period:
                        continue
                    energy = np.sqrt(np.mean(data**2))
                    if energy > self.INTERRUPT_THRESHOLD:
                        consecutive += 1
                        if consecutive >= self.INTERRUPT_CONSECUTIVE:
                            sd.stop()
                            self.interrupted = True
                            print("  [Fala interrompida]")
                            return
                    else:
                        consecutive = 0
        except Exception:
            sd.wait()

    def _speak_piper(self, text):
        try:
            piper = subprocess.Popen(
                [
                    self.PIPER_BIN,
                    "--model",
                    self.PIPER_MODEL,
                    "--output-raw",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=self._piper_env,
            )
            aplay = subprocess.Popen(
                [
                    "aplay",
                    "-r",
                    "22050",
                    "-f",
                    "S16_LE",
                    "-t",
                    "raw",
                    "-",
                ],
                stdin=piper.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            piper.stdin.write(text.encode("utf-8"))
            piper.stdin.close()
            aplay.wait()
            piper.wait()
        except Exception as e:
            print(f"  Erro Piper: {e}, usando fallback.")
            self._speak_espeak(text)

    def _speak_espeak(self, text):
        try:
            subprocess.run(
                ["espeak-ng", "-v", "pt+f3", "-s", "150", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            print(f"  [TTS indisponível] {text}")
