import time
import threading

import numpy as np
import sounddevice as sd


class ClapDetector:
    SAMPLE_RATE = 44100
    BLOCK_SIZE = 1024
    ENERGY_THRESHOLD = 0.25
    MIN_GAP_SEC = 0.15
    MAX_GAP_SEC = 1.5
    COOLDOWN_SEC = 2.0

    def __init__(self, on_activate, threshold=None):
        self.on_activate = on_activate
        if threshold is not None:
            self.ENERGY_THRESHOLD = threshold
        self._last_clap_time = 0.0
        self._last_activate_time = 0.0
        self._stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        energy = np.sqrt(np.mean(indata**2))
        now = time.time()

        if energy > self.ENERGY_THRESHOLD:
            gap = now - self._last_clap_time

            if (
                self._last_clap_time > 0
                and self.MIN_GAP_SEC <= gap <= self.MAX_GAP_SEC
            ):
                if now - self._last_activate_time > self.COOLDOWN_SEC:
                    self._last_activate_time = now
                    self._last_clap_time = 0.0
                    threading.Thread(
                        target=self.on_activate, daemon=True
                    ).start()
                    return

            self._last_clap_time = now

    def start(self):
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
