"""Inspect a source sound: trims, loudness, and spectral profile.

Prints the active region, a 20 ms loudness profile, and the spectral centroid so
a trim window can be chosen without listening.
"""

import sys
import wave

import numpy as np


def load(path: str) -> tuple[np.ndarray, int]:
    """Read a 16-bit mono PCM WAV."""
    with wave.open(path, 'rb') as handle:
        rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
    data = np.frombuffer(frames, dtype='<i2').astype(np.float64) / 32768.0
    return data, rate


def describe(path: str) -> None:
    """Report active region, loudness and spectrum."""
    signal, rate = load(path)
    duration = len(signal) / rate
    peak = float(np.max(np.abs(signal)))
    rms = float(np.sqrt(np.mean(signal ** 2)))

    window = int(0.02 * rate)
    frames = len(signal) // window
    envelope = np.array([np.sqrt(np.mean(signal[i * window:(i + 1) * window] ** 2)) for i in range(frames)])
    loud = envelope / (np.max(envelope) + 1e-12)
    active = np.where(loud > 0.02)[0]
    start = active[0] * window / rate if len(active) else 0.0
    end = (active[-1] + 1) * window / rate if len(active) else duration

    spectrum = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(len(signal), 1 / rate)
    power = spectrum ** 2
    total = np.sum(power) + 1e-12
    centroid = float(np.sum(freqs * power) / total)
    high = float(np.sum(power[freqs > 5000]) / total)
    low = float(np.sum(power[freqs < 200]) / total)

    print(f'== {path}')
    print(f'   duration {duration:.2f}s  peak {peak:.2f}  rms {rms:.3f}')
    print(f'   active {start:.2f}s -> {end:.2f}s  ({end - start:.2f}s)')
    print(f'   centroid {centroid:.0f} Hz  >5 kHz {high * 100:.0f}%  <200 Hz {low * 100:.0f}%')
    print('   20 ms profile:')
    line = []
    for index, value in enumerate(loud):
        if index % 25 == 0:
            if line:
                print('     ' + ' '.join(line))
            line = []
        line.append(f'{value:0.2f}')


for argument in sys.argv[1:]:
    describe(argument)
