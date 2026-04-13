import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from orion.audio_utils import clean_audio
from orion.vad import VoiceActivityDetector


class SpeechRecognizer:
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 512  # 32ms — Silero VAD native window
    CHUNK_DURATION = 512 / 16000  # 0.032s
    SILENCE_TIMEOUT = 1.5
    MAX_DURATION = 15.0
    INITIAL_SILENCE_TIMEOUT = 8.0
    MIN_SPEECH_DURATION = 0.3
    GRACE_PERIOD = 0.5
    # Silero VAD threshold — slightly higher than wake word to avoid
    # capturing noise during active recording
    VAD_THRESHOLD = 0.4

    def __init__(self):
        print("  Carregando modelo Whisper (large-v3) na GPU...")
        self.model = WhisperModel(
            "large-v3", device="cuda", compute_type="int8_float16"
        )
        print("  Whisper pronto (CUDA).")
        print("  Carregando Silero VAD (recognizer)...")
        self._vad = VoiceActivityDetector(threshold=self.VAD_THRESHOLD)
        print("  Silero VAD pronto.")
        self._noise_profile = self._calibrate_noise()

    def _calibrate_noise(self):
        """Mede o ruído ambiente por 1s e captura perfil para redutor."""
        print("  Calibrando ruído ambiente...", end=" ")
        chunk_size = self.CHUNK_SIZE
        noise_chunks = []
        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, blocksize=chunk_size
        ) as stream:
            for _ in range(int(1.0 / self.CHUNK_DURATION)):
                data, _ = stream.read(chunk_size)
                noise_chunks.append(data.copy())
        noise_profile = np.concatenate(noise_chunks, axis=0).flatten().astype(np.float32)
        print(f"perfil capturado ({len(noise_profile)} amostras)")
        return noise_profile

    def record_and_transcribe(self):
        chunk_size = self.CHUNK_SIZE
        chunks = []
        silence_start = None
        has_speech = False
        start_time = time.time()
        speech_frames = 0
        self._vad.reset()

        print("  Ouvindo...")

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, blocksize=chunk_size
        ) as stream:
            while True:
                data, _ = stream.read(chunk_size)
                elapsed = time.time() - start_time

                # Skip grace period to avoid TTS audio bleed
                if elapsed < self.GRACE_PERIOD:
                    continue

                chunks.append(data.copy())

                is_speech = self._vad.is_speech(
                    data.flatten().astype(np.float32)
                )

                if is_speech:
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
        audio = clean_audio(audio, self.SAMPLE_RATE, noise_profile=self._noise_profile)

        t0 = time.time()
        segments, _ = self.model.transcribe(
            audio,
            language="pt",
            beam_size=3,
            temperature=0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_speech_duration_ms=250),
            without_timestamps=True,
            initial_prompt=(
                "Orion, que horas são? Abre o Chrome. Fecha tudo. "
                "Desliga o computador. Liga a luz da varanda. "
                "Pesquisa sobre. Aumenta o volume. Faz uma demonstração."
            ),
        )
        parts = []
        for seg in segments:
            if seg.no_speech_prob < 0.6:
                parts.append(seg.text)
        text = " ".join(parts).strip()
        text = self._fix_transcription(text)
        print(f"  Transcrição: {time.time() - t0:.2f}s")
        return text

    TRANSCRIPTION_FIXES = {
        "oração": "horas são",
        "que oração": "que horas são",
        "orações": "horas são",
    }

    def _fix_transcription(self, text):
        lower = text.lower()
        for wrong, right in self.TRANSCRIPTION_FIXES.items():
            if wrong in lower:
                import re
                text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
        return text
