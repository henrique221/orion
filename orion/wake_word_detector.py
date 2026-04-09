import collections
import threading
import time

import numpy as np
import sounddevice as sd

from orion.audio_utils import clean_audio


class WakeWordDetector:
    SAMPLE_RATE = 16000
    BLOCK_SIZE = 800  # 50ms
    BUFFER_SECONDS = 3.0
    MIN_SPEECH_SEC = 0.12
    SILENCE_AFTER_SEC = 0.35
    COOLDOWN_SEC = 3.0
    CALIBRATION_WINDOW = 80
    # Pre-buffer: keeps audio BEFORE speech starts (captures word onset)
    PRE_BUFFER_BLOCKS = 6  # 300ms

    def __init__(self, on_activate, whisper_model):
        self.on_activate = on_activate
        self.model = whisper_model
        self._stream = None
        self._last_activate = 0.0
        self._threshold = 0.01
        self._speech_start = None
        self._silence_start = None
        self._buffer = []
        self._pre_buffer = collections.deque(maxlen=self.PRE_BUFFER_BLOCKS)
        self._checking = False
        self._noise_history = []
        self._noise_profile = self._calibrate_noise()

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

    def _update_noise_floor(self, energy):
        """Mantém uma janela deslizante do ruído ambiente."""
        self._noise_history.append(energy)
        if len(self._noise_history) > self.CALIBRATION_WINDOW:
            self._noise_history.pop(0)
        noise_floor = np.percentile(self._noise_history, 50)
        self._threshold = max(noise_floor * 1.5, 0.004)

    def _audio_callback(self, indata, frames, time_info, status):
        energy = np.sqrt(np.mean(indata**2))
        now = time.time()

        if self._speech_start is None:
            self._update_noise_floor(energy)
            self._pre_buffer.append(indata.copy())

        if energy > self._threshold:
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

    def _check(self, audio):
        try:
            audio = clean_audio(audio, self.SAMPLE_RATE, noise_profile=self._noise_profile, prop_decrease=0.5)
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

            if any(w in text for w in (
                "orion", "órion", "orian", "orião",
                "oriom", "oreon", "ório",
                "oriam", "aurion", "oryon",
                "oriel", "órien", "orient",
                "oh ryan", "o ryan",
            )):
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
        self._noise_history = []
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
