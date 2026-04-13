import noisereduce as nr
import numpy as np
from scipy.signal import butter, sosfilt


# Human voice frequency range
VOICE_LOW_HZ = 100
VOICE_HIGH_HZ = 3400
FILTER_ORDER = 5


def bandpass_filter(audio, sr, low=VOICE_LOW_HZ, high=VOICE_HIGH_HZ):
    """Filters audio to keep only human voice frequencies (100-3400 Hz).

    Removes low-frequency rumble (fans, AC, traffic) and
    high-frequency noise (electronics, hiss).
    """
    nyq = sr / 2
    sos = butter(FILTER_ORDER, [low / nyq, high / nyq], btype="band", output="sos")
    return sosfilt(sos, audio).astype(np.float32)


def clean_audio(audio, sr, noise_profile=None, prop_decrease=0.8):
    """Full audio cleanup pipeline: band-pass filter + noise reduction."""
    # Step 1: Band-pass filter to isolate voice frequencies
    audio = bandpass_filter(audio, sr)

    # Step 2: Spectral noise reduction
    if noise_profile is not None:
        noise_profile = bandpass_filter(noise_profile, sr)
        audio = nr.reduce_noise(
            y=audio,
            y_noise=noise_profile,
            sr=sr,
            prop_decrease=prop_decrease,
            stationary=True,
        )
    else:
        audio = nr.reduce_noise(
            y=audio,
            sr=sr,
            prop_decrease=prop_decrease,
            stationary=False,
        )

    return audio
