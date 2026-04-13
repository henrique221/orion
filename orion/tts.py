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
    PIPER_MODEL = os.path.expanduser(
        "~/.local/share/piper/pt_BR-faber-medium.onnx"
    )

    def __init__(self, face=None):
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

                print("  Carregando XTTS v2...")
                device = "cuda" if self._has_cuda else "cpu"
                self._xtts = CoquiTTS(self.XTTS_MODEL).to(device)
                self._xtts_model = self._xtts.synthesizer.tts_model
                # Cache do embedding da voz (evita reprocessar a cada fala)
                print("  Cacheando embedding da voz...")
                self._xtts_gpt_latent, self._xtts_speaker_emb = \
                    self._xtts_model.get_conditioning_latents(audio_path=self.VOICE_REF)
                if self._has_cuda:
                    vram = torch.cuda.memory_allocated() / 1024 ** 2
                    print(f"  TTS: XTTS v2 pronto (GPU, {vram:.0f}MB VRAM).")
                else:
                    print("  TTS: XTTS v2 pronto (CPU).")
            except Exception as e:
                print(f"  XTTS v2 indisponível ({e}), tentando Kokoro...")

        # 2. Fallback: Kokoro (CPU)
        if self._xtts is None and os.path.isfile(self.KOKORO_MODEL) and os.path.isfile(
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

        # 3. Fallback: Piper / espeak-ng
        if self._xtts is None and self._kokoro is None:
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

    def free_vram(self):
        """Move XTTS para CPU temporariamente para liberar VRAM."""
        if self._xtts_model and self._has_cuda:
            import torch
            self._xtts_model.cpu()
            self._xtts_gpt_latent = self._xtts_gpt_latent.cpu()
            self._xtts_speaker_emb = self._xtts_speaker_emb.cpu()
            torch.cuda.empty_cache()
            print("  XTTS movido para CPU.")

    def reclaim_vram(self):
        """Move XTTS de volta para GPU."""
        if self._xtts_model and self._has_cuda:
            self._xtts_model.cuda()
            self._xtts_gpt_latent = self._xtts_gpt_latent.cuda()
            self._xtts_speaker_emb = self._xtts_speaker_emb.cuda()
            print("  XTTS movido para GPU.")

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
                        language="pt",
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
            print(f"  Erro XTTS: {e}, usando fallback.")
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
