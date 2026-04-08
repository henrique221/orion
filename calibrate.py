"""Calibra o threshold de deteccao de palmas para o ambiente atual."""

import time

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
TEST_DURATION = 10
SILENCE_PHASE = 3


def main():
    print("=== Calibracao de Palmas - Orion ===\n")
    print(f"O teste dura {TEST_DURATION} segundos.")
    print(f"Primeiros {SILENCE_PHASE}s: fique em SILENCIO.")
    print(f"Depois: bata PALMAS varias vezes.\n")

    energies = []
    start_time = None

    def callback(indata, frames, time_info, status):
        energy = np.sqrt(np.mean(indata**2))
        elapsed = time.time() - start_time if start_time else 0
        energies.append((elapsed, energy))

    input("Pressione ENTER para comecar...")
    print()

    start_time = time.time()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        callback=callback,
    ):
        for i in range(TEST_DURATION, 0, -1):
            elapsed = time.time() - start_time
            if elapsed < SILENCE_PHASE:
                label = "SILENCIO"
            else:
                label = "BATA PALMAS"
            print(f"  {i:2d}s restantes  [{label}]", end="\r")
            time.sleep(1)

    print("\n\nAnalisando...\n")

    silence_energies = [e for t, e in energies if t <= SILENCE_PHASE]
    clap_energies = [e for t, e in energies if t > SILENCE_PHASE]

    if not silence_energies or not clap_energies:
        print("Dados insuficientes. Tente novamente.")
        return

    noise_floor = np.mean(silence_energies)
    noise_max = np.max(silence_energies)
    clap_peak = np.max(clap_energies)
    clap_p90 = np.percentile(
        [e for e in clap_energies if e > noise_max * 2], 10
    ) if any(e > noise_max * 2 for e in clap_energies) else clap_peak * 0.5

    suggested = (noise_max + clap_p90) / 2

    print(f"  Ruido medio (silencio):    {noise_floor:.4f}")
    print(f"  Ruido maximo (silencio):   {noise_max:.4f}")
    print(f"  Pico de palma:             {clap_peak:.4f}")
    print(f"  Percentil 10 das palmas:   {clap_p90:.4f}")
    print(f"\n  >>> Threshold sugerido:    {suggested:.4f}")
    print(f"\n  (Padrao atual: 0.25)")
    print(
        f"\n  Para usar, edite ENERGY_THRESHOLD em orion/clap_detector.py"
    )


if __name__ == "__main__":
    main()
