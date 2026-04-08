import time

import noisereduce as nr
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class SpeechRecognizer:
    SAMPLE_RATE = 16000
    CHUNK_DURATION = 0.05
    SILENCE_TIMEOUT = 1.5
    MAX_DURATION = 15.0
    INITIAL_SILENCE_TIMEOUT = 8.0
    MIN_SPEECH_DURATION = 0.3
    GRACE_PERIOD = 0.5

    def __init__(self):
        print("  Carregando modelo Whisper (large-v3) na GPU...")
        self.model = WhisperModel(
            "large-v3", device="cuda", compute_type="int8_float16"
        )
        print("  Whisper pronto (CUDA).")
        self.silence_threshold = self._calibrate_noise()

    def _calibrate_noise(self):
        """Mede o ruído ambiente por 1s e define o threshold."""
        print("  Calibrando ruído ambiente...", end=" ")
        chunk_size = int(self.SAMPLE_RATE * self.CHUNK_DURATION)
        noise_chunks = []
        energies = []
        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, blocksize=chunk_size
        ) as stream:
            for _ in range(int(1.0 / self.CHUNK_DURATION)):
                data, _ = stream.read(chunk_size)
                noise_chunks.append(data.copy())
                energies.append(np.sqrt(np.mean(data**2)))
        self.noise_floor = np.mean(energies)
        self._noise_profile = np.concatenate(noise_chunks, axis=0).flatten().astype(np.float32)
        threshold = max(self.noise_floor * 5, 0.01)
        print(f"ruído={self.noise_floor:.4f}, threshold={threshold:.4f}")
        return threshold

    def record_and_transcribe(self):
        chunk_size = int(self.SAMPLE_RATE * self.CHUNK_DURATION)
        chunks = []
        silence_start = None
        has_speech = False
        start_time = time.time()

        print("  Ouvindo...")

        speech_frames = 0

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, blocksize=chunk_size
        ) as stream:
            while True:
                data, _ = stream.read(chunk_size)
                energy = np.sqrt(np.mean(data**2))
                elapsed = time.time() - start_time

                # Skip grace period to avoid TTS audio bleed
                if elapsed < self.GRACE_PERIOD:
                    continue

                chunks.append(data.copy())

                if energy >= self.silence_threshold:
                    has_speech = True
                    speech_frames += 1
                    silence_start = None
                else:
                    if silence_start is None:
                        silence_start = time.time()
                    elif has_speech and time.time() - silence_start >= self.SILENCE_TIMEOUT:
                        break

                # Bail if no real speech after initial timeout
                wait_time = elapsed - self.GRACE_PERIOD
                speech_duration = speech_frames * self.CHUNK_DURATION
                if not has_speech and wait_time >= self.INITIAL_SILENCE_TIMEOUT:
                    print("  Nenhuma fala detectada.")
                    return ""
                if has_speech and speech_duration < self.MIN_SPEECH_DURATION and wait_time >= self.INITIAL_SILENCE_TIMEOUT:
                    print("  Apenas ruído detectado.")
                    return ""

                if elapsed >= self.MAX_DURATION:
                    break

        rec_time = time.time() - start_time
        speech_duration = speech_frames * self.CHUNK_DURATION
        print(f"  Gravação: {rec_time:.1f}s (fala: {speech_duration:.1f}s)")

        if not has_speech or speech_duration < self.MIN_SPEECH_DURATION:
            return ""

        audio = np.concatenate(chunks, axis=0).flatten().astype(np.float32)
        audio = nr.reduce_noise(
            y=audio,
            y_noise=self._noise_profile,
            sr=self.SAMPLE_RATE,
            prop_decrease=0.8,
            stationary=True,
        )

        t0 = time.time()
        segments, _ = self.model.transcribe(
            audio,
            language="pt",
            beam_size=1,
            temperature=0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_speech_duration_ms=250),
            without_timestamps=True,
        )
        parts = []
        for seg in segments:
            if seg.no_speech_prob < 0.6:
                parts.append(seg.text)
        text = " ".join(parts).strip()
        print(f"  Transcrição: {time.time() - t0:.2f}s")
        return text
