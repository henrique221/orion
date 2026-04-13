import collections
import re
import threading
import time

import numpy as np
import sounddevice as sd

from orion.audio_utils import clean_audio
from orion.vad import VoiceActivityDetector

# Matches "Orion" and realistic Whisper transcription variants,
# using word boundaries to avoid partial matches like "laboratório".
# Covers: orion, órion, orian, orião, oriom, oreon, ório, oryon, oriam
_WAKE_RE = re.compile(r'\b[oó]r[iye](?:ão|[oa][nm]?)\b', re.IGNORECASE)


class WakeWordDetector:
    SAMPLE_RATE = 16000
    BLOCK_SIZE = 512  # 32ms — Silero VAD native window
    BUFFER_SECONDS = 3.0
    MIN_SPEECH_SEC = 0.12
    SILENCE_AFTER_SEC = 0.35
    COOLDOWN_SEC = 3.0
    # Pre-buffer: keeps audio BEFORE speech starts (captures word onset)
    PRE_BUFFER_BLOCKS = 10  # ~320ms at 512 samples
    # Silero VAD threshold — lower = more sensitive to quiet speech
    VAD_THRESHOLD = 0.35

    def __init__(self, on_activate, whisper_model):
        self.on_activate = on_activate
        self.model = whisper_model
        self._stream = None
        self._last_activate = 0.0
        self._speech_start = None
        self._silence_start = None
        self._buffer = []
        self._pre_buffer = collections.deque(maxlen=self.PRE_BUFFER_BLOCKS)
        self._checking = False
        self._noise_profile = self._calibrate_noise()
        print("  Carregando Silero VAD (wake word)...")
        self._vad = VoiceActivityDetector(threshold=self.VAD_THRESHOLD)
        print("  Silero VAD pronto.")

    def _calibrate_noise(self):
        """Captura 1s de ruído ambiente para o redutor de ruído."""
        chunk_size = self.BLOCK_SIZE
        noise_chunks = []
        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, blocksize=chunk_size
        ) as stream:
            for _ in range(int(1.0 / (chunk_size / self.SAMPLE_RATE))):
                data, _ = stream.read(chunk_size)
                noise_chunks.append(data.copy())
        return np.concatenate(noise_chunks, axis=0).flatten().astype(np.float32)

    def _audio_callback(self, indata, frames, time_info, status):
        chunk = indata.flatten().astype(np.float32)
        now = time.time()

        if self._speech_start is None:
            self._pre_buffer.append(indata.copy())

        is_speech = self._vad.is_speech(chunk)

        if is_speech:
            if self._speech_start is None:
                self._speech_start = now
                # Prepend pre-buffer to capture word onset
                self._buffer = list(self._pre_buffer)
            self._silence_start = None
            self._buffer.append(indata.copy())
            max_blocks = int(
                self.BUFFER_SECONDS * self.SAMPLE_RATE / self.BLOCK_SIZE
            )
            if len(self._buffer) > max_blocks:
                self._buffer = self._buffer[-max_blocks:]
        elif self._speech_start is not None:
            self._buffer.append(indata.copy())
            if self._silence_start is None:
                self._silence_start = now
            elif now - self._silence_start >= self.SILENCE_AFTER_SEC:
                duration = self._silence_start - self._speech_start
                if (
                    duration >= self.MIN_SPEECH_SEC
                    and not self._checking
                    and now - self._last_activate > self.COOLDOWN_SEC
                ):
                    audio = np.concatenate(self._buffer, axis=0)
                    self._checking = True
                    threading.Thread(
                        target=self._check,
                        args=(audio.flatten().astype(np.float32),),
                        daemon=True,
                    ).start()
                self._speech_start = None
                self._silence_start = None
                self._buffer = []
                self._vad.reset()

    def _check(self, audio):
        try:
            audio = clean_audio(audio, self.SAMPLE_RATE, noise_profile=self._noise_profile, prop_decrease=0.6)
            segments, _ = self.model.transcribe(
                audio,
                language="pt",
                beam_size=3,
                temperature=0,
                without_timestamps=True,
                vad_filter=False,
                initial_prompt="Orion",
            )
            text = " ".join(seg.text for seg in segments).strip().lower()

            if not text or len(text) > 50:
                return
            words = text.split()
            if len(words) > 3 and len(set(words)) <= len(words) // 2:
                return

            if _WAKE_RE.search(text):
                print(f"  [Wake word: \"{text}\"]")
                self._last_activate = time.time()
                self.on_activate(text)
        except Exception:
            pass
        finally:
            self._checking = False

    def start(self):
        self._speech_start = None
        self._silence_start = None
        self._buffer = []
        self._pre_buffer = collections.deque(maxlen=self.PRE_BUFFER_BLOCKS)
        self._checking = False
        self._vad.reset()
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.BLOCK_SIZE,
            channels=1,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
