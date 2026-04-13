import numpy as np
import torch


class VoiceActivityDetector:
    """Silero VAD wrapper for real-time speech detection.

    Uses a neural network trained specifically on speech vs noise,
    far more accurate than simple RMS energy thresholds.
    """

    SAMPLE_RATE = 16000
    WINDOW_SIZE = 512  # 32ms at 16kHz — Silero's native window

    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self._model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
        self._model.eval()

    def reset(self):
        """Reset internal RNN states (call between utterances)."""
        self._model.reset_states()

    def __call__(self, audio_chunk):
        """Return speech probability for a chunk of audio.

        Args:
            audio_chunk: numpy array or torch tensor, ideally 512 samples at 16kHz.

        Returns:
            float: speech probability [0, 1].
        """
        if isinstance(audio_chunk, np.ndarray):
            audio_chunk = torch.from_numpy(audio_chunk).float()
        if audio_chunk.dim() > 1:
            audio_chunk = audio_chunk.squeeze()
        if len(audio_chunk) < self.WINDOW_SIZE:
            audio_chunk = torch.nn.functional.pad(
                audio_chunk, (0, self.WINDOW_SIZE - len(audio_chunk))
            )
        elif len(audio_chunk) > self.WINDOW_SIZE:
            audio_chunk = audio_chunk[: self.WINDOW_SIZE]
        return self._model(audio_chunk, self.SAMPLE_RATE).item()

    def is_speech(self, audio_chunk):
        """Check if audio chunk contains speech."""
        return self(audio_chunk) >= self.threshold
