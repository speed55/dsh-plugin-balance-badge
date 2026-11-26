"""Turn the two source recordings into embedded plugin samples.

Each source is trimmed to its active region, limiter-protected so a clipped AAC
decode cannot stay clipped, downsampled with an anti-alias filter, and written as
a 22.05 kHz mono 16-bit WAV plus its base64 payload.

Run: python process_samples.py
Outputs: assets-src/coin-reward.wav|.b64 and assets-src/coin-drop.wav|.b64
"""

import base64
import os
import wave

import numpy as np

SR_OUT = 22050

# name, source file, trim start (s), trim end (s), extra high-frequency roll-off
#
# Both sources are the author's own recordings, so no third-party terms apply:
#   coin-reward <- cash-register-cha-ching.mp3  (2.43 s, active 0.02-1.28 s)
#   coin-drop   <- 原创金币掉落_短版.mp3        (1.65 s, active 0.00-1.46 s)
SOURCES = [
    ('coin-reward', 'src-reward.wav', 0.00, 1.30, 0.00),
    ('coin-drop', 'src-drop.wav', 0.00, 1.40, 0.20),
]


def load(path: str) -> tuple[np.ndarray, int]:
    """Read a 16-bit mono PCM WAV."""
    with wave.open(path, 'rb') as handle:
        rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
    return np.frombuffer(frames, dtype='<i2').astype(np.float64) / 32768.0, rate


def spectral_shape(signal: np.ndarray, rate: int, weight) -> np.ndarray:
    """Apply a smooth frequency weight without ringing."""
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), 1 / rate)
    return np.fft.irfft(spectrum * weight(freqs), len(signal))


def process(name: str, source: str, start: float, end: float, hiss: float) -> None:
    """Trim, shape, limit, resample and encode one source."""
    here = os.path.dirname(os.path.abspath(__file__))
    signal, rate = load(os.path.join(here, source))
    clip_ratio = float(np.mean(np.abs(signal) > 0.999))

    begin = int(start * rate)
    finish = min(len(signal), int(end * rate))
    signal = signal[begin:finish].copy()

    # Rumble out, and optionally tame a hissy top end before it is filtered away.
    def weight(f: np.ndarray) -> np.ndarray:
        highpass = f ** 2 / (f ** 2 + 70 ** 2)
        tame = 1 - hiss * (f ** 2 / (f ** 2 + 9000 ** 2))
        return highpass * tame

    signal = spectral_shape(signal, rate, weight)

    # Soft-knee limiter: only the last few dB are touched, so the transient
    # survives instead of being flattened.
    peak = np.max(np.abs(signal)) + 1e-9
    signal /= peak
    knee = 0.72
    magnitude = np.abs(signal)
    over = magnitude > knee
    if np.any(over):
        signal[over] = np.sign(signal[over]) * (knee + (1 - knee) * np.tanh((magnitude[over] - knee) / (1 - knee)))
    signal *= 0.96

    # Anti-aliased decimation to the shipped rate.
    ratio = rate // SR_OUT
    signal = spectral_shape(signal, rate, lambda f: (f < SR_OUT / 2 - 500).astype(float))[::ratio]

    # Short fades so the clip cannot click.
    fade_in = max(1, int(0.002 * SR_OUT))
    signal[:fade_in] *= np.linspace(0, 1, fade_in)
    fade_out = max(1, int(0.03 * SR_OUT))
    signal[-fade_out:] *= np.linspace(1, 0, fade_out)

    spectrum = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(len(signal), 1 / SR_OUT)
    power = spectrum ** 2
    total = np.sum(power) + 1e-12
    centroid = float(np.sum(freqs * power) / total)
    high = float(np.sum(power[freqs > 5000]) / total)

    pcm = (np.clip(signal, -1, 1) * 32767).astype('<i2')
    wav_path = os.path.join(here, name + '.wav')
    with wave.open(wav_path, 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR_OUT)
        handle.writeframes(pcm.tobytes())
    with open(wav_path, 'rb') as handle:
        payload = base64.b64encode(handle.read()).decode('ascii')
    with open(os.path.join(here, name + '.b64'), 'w', encoding='ascii') as handle:
        handle.write(payload)

    print(f'{name}: {len(signal) / SR_OUT:.2f}s  {len(pcm) * 2} bytes  b64 {len(payload)} chars')
    print(f'  centroid {centroid:6.0f} Hz   >5 kHz {high * 100:4.1f}%   source clipped samples {clip_ratio * 100:4.2f}%')


for entry in SOURCES:
    process(*entry)
