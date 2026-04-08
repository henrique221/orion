import os
import shutil
import subprocess


class TTS:
    PIPER_BIN = os.path.expanduser("~/.local/bin/piper")
    PIPER_LIB = os.path.expanduser("~/.local/bin")
    PIPER_MODEL = os.path.expanduser(
        "~/.local/share/piper/pt_BR-faber-medium.onnx"
    )

    def __init__(self):
        self._use_piper = os.path.isfile(self.PIPER_BIN) and os.path.isfile(
            self.PIPER_MODEL
        )
        self._piper_env = os.environ.copy()
        ld = self._piper_env.get("LD_LIBRARY_PATH", "")
        self._piper_env["LD_LIBRARY_PATH"] = (
            f"{self.PIPER_LIB}:{ld}" if ld else self.PIPER_LIB
        )
        if self._use_piper:
            print("  TTS: Piper pronto.")
        elif shutil.which("espeak-ng"):
            print("  TTS: Usando espeak-ng (fallback).")
        else:
            print("  AVISO: Nenhum TTS disponível.")

    def speak(self, text):
        if not text:
            return
        if self._use_piper:
            self._speak_piper(text)
        else:
            self._speak_espeak(text)

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
            print(f"  [TTS indisponivel] {text}")
