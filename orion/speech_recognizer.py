import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class SpeechRecognizer:
    SAMPLE_RATE = 16000
    CHUNK_DURATION = 0.05
    SILENCE_TIMEOUT = 0.8
    MAX_DURATION = 10.0

    def __init__(self):
        print("  Carregando modelo Whisper (turbo) na GPU...")
        self.model = WhisperModel(
            "turbo", device="cuda", compute_type="float16"
        )
        print("  Whisper pronto (CUDA).")
        self.silence_threshold = self._calibrate_noise()

    def _calibrate_noise(self):
        """Mede o ruído ambiente por 1s e define o threshold."""
        print("  Calibrando ruído ambiente...", end=" ")
        chunk_size = int(self.SAMPLE_RATE * self.CHUNK_DURATION)
        energies = []
        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, blocksize=chunk_size
        ) as stream:
            for _ in range(int(1.0 / self.CHUNK_DURATION)):
                data, _ = stream.read(chunk_size)
                energies.append(np.sqrt(np.mean(data**2)))
        self.noise_floor = np.mean(energies)
        threshold = max(self.noise_floor * 3, 0.008)
        print(f"ruído={self.noise_floor:.4f}, threshold={threshold:.4f}")
        return threshold

    def record_and_transcribe(self):
        chunk_size = int(self.SAMPLE_RATE * self.CHUNK_DURATION)
        chunks = []
        silence_start = None
        has_speech = False
        start_time = time.time()

        print("  Ouvindo...")

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, blocksize=chunk_size
        ) as stream:
            while True:
                data, _ = stream.read(chunk_size)
                chunks.append(data.copy())
                energy = np.sqrt(np.mean(data**2))
                elapsed = time.time() - start_time

                if energy >= self.silence_threshold:
                    has_speech = True
                    silence_start = None
                else:
                    if silence_start is None:
                        silence_start = time.time()
                    elif has_speech and time.time() - silence_start >= self.SILENCE_TIMEOUT:
                        break

                if elapsed >= self.MAX_DURATION:
                    break

        rec_time = time.time() - start_time
        print(f"  Gravação: {rec_time:.1f}s")

        if not chunks:
            return ""

        audio = np.concatenate(chunks, axis=0).flatten().astype(np.float32)

        t0 = time.time()
        segments, _ = self.model.transcribe(
            audio,
            language="pt",
            beam_size=1,
            temperature=0,
            condition_on_previous_text=False,
            vad_filter=True,
            without_timestamps=True,
        )
        text = " ".join(seg.text for seg in segments).strip()
        print(f"  Transcrição: {time.time() - t0:.2f}s")
        return text
