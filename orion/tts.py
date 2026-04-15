import os
import shutil
import subprocess
import time

import numpy as np
import sounddevice as sd

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TTS:
    VOICE_REF = os.path.join(_PROJECT_ROOT, "assets", "voice_ref.wav")
    XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
    XTTS_RATE = 24000

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

    def __init__(self, strings, face=None):
        self._strings = strings
        tts_cfg = strings["tts"]
        self._xtts_lang = tts_cfg["xtts"]
        self._kokoro_lang = tts_cfg["kokoro_lang"]
        self._espeak_voice = tts_cfg["espeak"]
        self._piper_model = tts_cfg["piper_model"]

        self._xtts = None
        self._kokoro = None
        self._g2p = None
        self._use_piper = False
        self.interrupted = False
        self.allow_interrupt = True
        self._face = face

        # 1. Tentar XTTS v2 (GPU — Ollama roda em CPU)
        self._xtts_model = None
        self._xtts_gpt_latent = None
        self._xtts_speaker_emb = None
        self._has_cuda = False
        if os.path.isfile(self.VOICE_REF):
            try:
                import torch
                self._has_cuda = torch.cuda.is_available()
                from TTS.api import TTS as CoquiTTS

                print(self._strings["terminal"]["loading_xtts"])
                device = "cuda" if self._has_cuda else "cpu"
                self._xtts = CoquiTTS(self.XTTS_MODEL).to(device)
                self._xtts_model = self._xtts.synthesizer.tts_model
                # Cache do embedding da voz (evita reprocessar a cada fala)
                print(self._strings["terminal"]["caching_voice"])
                self._xtts_gpt_latent, self._xtts_speaker_emb = \
                    self._xtts_model.get_conditioning_latents(audio_path=self.VOICE_REF)
                if self._has_cuda:
                    vram = torch.cuda.memory_allocated() / 1024 ** 2
                    print(self._strings["terminal"]["xtts_ready_gpu"].format(vram=vram))
                else:
                    print(self._strings["terminal"]["xtts_ready_cpu"])
            except Exception as e:
                print(self._strings["terminal"]["xtts_unavailable"].format(error=e))

        # 2. Fallback: Kokoro (CPU)
        if self._xtts is None and os.path.isfile(self.KOKORO_MODEL) and os.path.isfile(
            self.KOKORO_VOICES
        ):
            try:
                from kokoro_onnx import Kokoro
                from misaki.espeak import EspeakG2P

                print(self._strings["terminal"]["loading_kokoro"])
                self._kokoro = Kokoro(self.KOKORO_MODEL, self.KOKORO_VOICES)
                self._g2p = EspeakG2P(language=self._kokoro_lang)
                print(self._strings["terminal"]["kokoro_ready"])
            except Exception as e:
                print(self._strings["terminal"]["kokoro_unavailable"].format(error=e))

        # 3. Fallback: Piper / espeak-ng
        if self._xtts is None and self._kokoro is None:
            self._use_piper = os.path.isfile(self.PIPER_BIN) and os.path.isfile(self._piper_model)
            self._piper_env = os.environ.copy()
            ld = self._piper_env.get("LD_LIBRARY_PATH", "")
            self._piper_env["LD_LIBRARY_PATH"] = (
                f"{self.PIPER_LIB}:{ld}" if ld else self.PIPER_LIB
            )
            if self._use_piper:
                print(self._strings["terminal"]["piper_ready"])
            elif shutil.which("espeak-ng"):
                print(self._strings["terminal"]["espeak_ready"])
            else:
                print(self._strings["terminal"]["no_tts"])

    def free_vram(self):
        """Move XTTS para CPU temporariamente para liberar VRAM."""
        if self._xtts_model and self._has_cuda:
            import torch
            self._xtts_model.cpu()
            self._xtts_gpt_latent = self._xtts_gpt_latent.cpu()
            self._xtts_speaker_emb = self._xtts_speaker_emb.cpu()
            torch.cuda.empty_cache()
            print(self._strings["terminal"]["xtts_to_cpu"])

    def reclaim_vram(self):
        """Move XTTS de volta para GPU."""
        if self._xtts_model and self._has_cuda:
            self._xtts_model.cuda()
            self._xtts_gpt_latent = self._xtts_gpt_latent.cuda()
            self._xtts_speaker_emb = self._xtts_speaker_emb.cuda()
            print(self._strings["terminal"]["xtts_to_gpu"])

    def speak(self, text):
        if not text:
            return
        if self._xtts:
            self._speak_xtts(text)
        elif self._kokoro:
            self._speak_kokoro(text)
        elif self._use_piper:
            self._speak_piper(text)
        else:
            self._speak_espeak(text)

    @staticmethod
    def _split_text(text, max_len=200):
        """Divide texto em pedaços respeitando vírgulas e espaços."""
        if len(text) <= max_len:
            return [text]
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            cut = text.rfind(',', 0, max_len)
            if cut == -1:
                cut = text.rfind(' ', 0, max_len)
            if cut == -1:
                cut = max_len
            chunks.append(text[:cut].strip())
            text = text[cut:].lstrip(', ')
        return [c for c in chunks if c]

    @staticmethod
    def _clean_text_for_xtts(text):
        """Remove pontuação que o XTTS lê literalmente."""
        import re
        # Expande símbolos comuns
        text = text.replace("°C", " graus")
        text = text.replace("°", " graus")
        text = text.replace("%", " por cento")
        # Remove pontos finais e reticências (causa "ponto")
        text = re.sub(r'\.{2,}', ',', text)
        text = re.sub(r'\.\s*$', '', text)
        text = re.sub(r'\.\s+', ', ', text)
        # Remove outros que podem ser lidos
        text = re.sub(r'[;:!]', ',', text)
        return text.strip()

    def _speak_xtts(self, text):
        try:
            import torch
            clean = self._clean_text_for_xtts(text)
            chunks = self._split_text(clean, max_len=200)

            all_samples = []
            for chunk in chunks:
                with torch.no_grad():
                    out = self._xtts_model.inference(
                        text=chunk,
                        language=self._xtts_lang,
                        gpt_cond_latent=self._xtts_gpt_latent,
                        speaker_embedding=self._xtts_speaker_emb,
                        temperature=0.3,
                        speed=1.1,
                        repetition_penalty=10.0,
                        enable_text_splitting=False,
                    )
                wav = out["wav"]
                if hasattr(wav, 'cpu'):
                    all_samples.append(wav.squeeze().cpu().numpy())
                else:
                    all_samples.append(np.asarray(wav).squeeze())

            samples = np.concatenate(all_samples) if len(all_samples) > 1 else all_samples[0]
            self.interrupted = False
            if self._face:
                from orion.face import State
                self._face.set_state(State.SPEAKING)
            sd.play(samples, self.XTTS_RATE)
            if self.allow_interrupt:
                self._monitor_for_interrupt(len(samples) / self.XTTS_RATE)
            else:
                sd.wait()
            if self._face:
                from orion.face import State
                self._face.set_state(State.IDLE)
        except Exception as e:
            print(self._strings["terminal"]["xtts_error"].format(error=e))
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
            print(self._strings["terminal"]["kokoro_error"].format(error=e))
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
                            print(self._strings["terminal"]["speech_interrupted"])
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
                    self._piper_model,
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
            print(self._strings["terminal"]["piper_error"].format(error=e))
            self._speak_espeak(text)

    def _speak_espeak(self, text):
        try:
            subprocess.run(
                ["espeak-ng", "-v", self._espeak_voice, "-s", "150", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            print(self._strings["terminal"]["tts_unavailable"])
