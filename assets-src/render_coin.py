"""Render a "treasure chest bursts open" coin cascade.

Structure follows how a real cascade behaves: an extremely dense burst at t=0
(coins bursting out of the lid), a thinning Poisson stream of coin-on-coin and
coin-on-chest contacts, then isolated bounce chains that grow sparser and die
out. Three timbres are layered — bright high "ping" partials, mid "clink"
bodies, and a few heavy "clank" hits for weight.

Run: python render_coin.py
Outputs: assets-src/coin.wav (32 kHz mono 16-bit) and assets-src/coin.b64
"""

import base64
import os
import wave

import numpy as np

SR = 44100
SR_OUT = 22050
DURATION = 1.2
SEED = 20261126

# Squared Bessel zeros of a free circular plate: strongly inharmonic mode set.
BESSEL_ZEROS = [2.405, 3.832, 5.136, 5.520, 6.380, 7.016, 8.417, 8.654, 9.761,
                11.065, 11.620, 13.015, 13.324, 14.796, 16.223, 17.960]
RATIOS = [(z / BESSEL_ZEROS[0]) ** 2 for z in BESSEL_ZEROS]


def spectral_shape(x: np.ndarray, weight) -> np.ndarray:
    """Apply a smooth frequency weight without ringing."""
    spectrum = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(spectrum * weight(freqs), len(x))


def modal_ring(f0: float, amplitude: float, tau: float, length: int,
               rng: np.random.Generator, slope: float = 0.85) -> np.ndarray:
    """Inharmonic modal bank of one metal contact."""
    t = np.arange(length) / SR
    out = np.zeros(length)
    for index, ratio in enumerate(RATIOS):
        frequency = f0 * ratio
        if frequency > SR * 0.45:
            break
        mode_tau = tau / (1 + (ratio - 1) * slope)
        mode_gain = amplitude / (1 + index * 0.55)
        phase = rng.uniform(0, 2 * np.pi)
        out += mode_gain * np.exp(-t / mode_tau) * np.sin(2 * np.pi * frequency * t + phase)
    return out


def contact(f0: float, amplitude: float, tau: float, click: float,
            duration: float, rng: np.random.Generator, slope: float = 0.85) -> np.ndarray:
    """One coin contact: modal ring plus a broadband strike transient."""
    n = max(8, int(duration * SR))
    out = modal_ring(f0, amplitude, tau, n, rng, slope)

    click_len = max(8, int(0.0018 * SR))
    noise = rng.standard_normal(click_len) * np.exp(-np.linspace(0, 7.5, click_len))
    noise = spectral_shape(noise, lambda f: (f ** 2) / (f ** 2 + 2200 ** 2))
    out[:click_len] += noise / (np.max(np.abs(noise)) + 1e-9) * amplitude * click
    return out


def add_at(target: np.ndarray, source: np.ndarray, when: float) -> None:
    """Mix one event into the timeline at a time in seconds."""
    start = int(when * SR)
    if start >= len(target):
        return
    end = min(len(target), start + len(source))
    target[start:end] += source[:end - start]


def render() -> np.ndarray:
    """Build the cascade from bursts, a thinning stream and bounce chains."""
    rng = np.random.default_rng(SEED)
    total = np.zeros(int(DURATION * SR))
    events = 0

    def coin(when: float, kind: str, gain: float) -> None:
        """Place one contact of the requested timbre."""
        nonlocal events
        if kind == 'ping':
            f0 = rng.uniform(3200, 8200)
            tau = rng.uniform(0.006, 0.02)
            length = 0.055
            slope = 1.35
            click = rng.uniform(0.5, 0.9)
        elif kind == 'clink':
            f0 = rng.uniform(1250, 3200)
            tau = rng.uniform(0.014, 0.045)
            length = 0.12
            slope = 0.95
            click = rng.uniform(0.35, 0.7)
        else:  # clank: a coin slamming the chest wall
            f0 = rng.uniform(240, 620)
            tau = rng.uniform(0.035, 0.085)
            length = 0.26
            slope = 0.55
            click = rng.uniform(0.8, 1.2)
        amplitude = gain * rng.uniform(0.35, 1.0)
        add_at(total, contact(f0, amplitude, tau, click, length, rng, slope), when)
        events += 1

    # 1. The burst: the lid blows open and coins explode outward. Dense beyond
    #    what the ear can resolve, so it reads as one bright impact with weight.
    for _ in range(54):
        when = rng.uniform(0, 0.075) ** 0.7
        coin(when, 'ping' if rng.random() < 0.64 else 'clink', 0.5)
    coin(0.002, 'clank', 1.5)
    coin(0.012, 'clank', 1.1)
    for when in (0.006, 0.021, 0.037):
        coin(when, 'clink', 1.2)
    # A few heavy hits later on give the cascade its weight without muddying it.
    for when in (0.19, 0.35, 0.53):
        coin(when, 'clank', 0.75)

    # 2. The cascade: a Poisson stream whose rate decays, so the texture thins
    #    from a wall of sound into separate contacts.
    time = 0.06
    while time < 0.78:
        rate = 660 * np.exp(-(time - 0.06) / 0.19) + 30
        time += float(rng.exponential(1.0 / rate))
        if time >= 0.78:
            break
        roll = rng.random()
        kind = 'ping' if roll < 0.6 else ('clink' if roll < 0.95 else 'clank')
        coin(time, kind, 0.55 * np.exp(-time / 0.75) + 0.12)

    # 3. Bounce chains: coins that landed once keep hopping with shorter rings.
    time = 0.16
    while time < 0.92:
        time += float(rng.uniform(0.03, 0.11))
        when = time
        bounces = int(rng.integers(2, 5))
        gap = rng.uniform(0.05, 0.12)
        for step in range(bounces):
            if when > 1.02:
                break
            coin(when, 'clink' if rng.random() < 0.72 else 'ping', 0.5 * (0.62 ** step))
            when += gap
            gap *= 0.72
        time = when

    # 4. The last few coins settle: isolated, quieter, wider apart, and the very
    #    last one dies into silence before the file ends.
    for when in (0.97, 1.03, 1.08, 1.125, 1.165):
        coin(when, 'clink', 0.3 * (1.0 - (when - 0.95) * 2.2))

    # 5. A short low thump under the burst gives the chest its weight; a very
    #    quiet high bed glues the contacts together instead of leaving them as
    #    separate grains.
    t = np.arange(int(0.22 * SR)) / SR
    thump = (np.sin(2 * np.pi * 92 * t) + 0.5 * np.sin(2 * np.pi * 148 * t)) * np.exp(-t / 0.055)
    add_at(total, thump * 0.62, 0.004)

    bed = rng.standard_normal(int(DURATION * SR))
    bed = spectral_shape(bed, lambda f: ((f > 2500) & (f < 11000)).astype(float))
    envelope = np.exp(-np.arange(len(bed)) / (0.18 * SR)) * 0.5 + 0.03
    total += bed * envelope * 0.014

    # 6. Shape: remove mud, ease the ear's most sensitive octave, add air.
    def weight(f: np.ndarray) -> np.ndarray:
        highpass = f ** 4 / (f ** 4 + 120 ** 4)
        mud = 1 - 0.26 * np.exp(-0.5 * ((np.log2(np.maximum(f, 1) / 2600)) / 0.45) ** 2)
        air = 1 + 0.55 * (f ** 4 / (f ** 4 + 6500 ** 4))
        hiss = 1 / (1 + (f / 13500) ** 6)
        return highpass * mud * air * hiss

    total = spectral_shape(total, weight)

    # 7. Normalise first, then a soft-knee limiter that only acts on the last
    #    few dB: the burst keeps its transient instead of being flattened by a
    #    wide tanh, which is what makes this sound punchy instead of squashed.
    total = total / (np.max(np.abs(total)) + 1e-9)
    knee = 0.78
    magnitude = np.abs(total)
    over = magnitude > knee
    if np.any(over):
        total[over] = np.sign(total[over]) * (knee + (1 - knee) * np.tanh((magnitude[over] - knee) / (1 - knee)))
    total *= 0.94

    fade_in = int(0.0008 * SR)
    total[:fade_in] *= np.linspace(0, 1, fade_in)
    fade_out = int(0.02 * SR)
    total[-fade_out:] *= np.linspace(1, 0, fade_out)
    peak = np.max(np.abs(total)) + 1e-9
    print(f'events: {events}')
    return total / peak * 0.9


def downsample(signal: np.ndarray) -> np.ndarray:
    """Anti-aliased decimation to the shipped rate."""
    return spectral_shape(signal, lambda f: (f < SR_OUT / 2 - 600).astype(float))[::SR // SR_OUT]


def report(signal: np.ndarray) -> None:
    """Print objective descriptors of the rendered cascade."""
    spectrum = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(len(signal), 1 / SR_OUT)
    power = spectrum ** 2
    total = np.sum(power) + 1e-12
    centroid = float(np.sum(freqs * power) / total)
    above_2k = float(np.sum(power[freqs > 2000]) / total)
    above_5k = float(np.sum(power[freqs > 5000]) / total)
    below_200 = float(np.sum(power[freqs < 200]) / total)

    energy = np.cumsum((signal ** 2)[::-1])[::-1]
    energy_db = 10 * np.log10(energy / (energy[0] + 1e-12) + 1e-12)
    below = np.where(energy_db < -40)[0]
    t40 = float(below[0] / SR_OUT) if len(below) else float(len(signal) / SR_OUT)

    window = int(0.01 * SR_OUT)
    frames = len(signal) // window
    rms = np.array([np.sqrt(np.mean(signal[i * window:(i + 1) * window] ** 2)) for i in range(frames)])
    peak_level = np.max(rms) + 1e-9

    print(f'duration {len(signal) / SR_OUT:.2f}s  peak {np.max(np.abs(signal)):.3f}  rms {np.sqrt(np.mean(signal ** 2)):.3f}')
    print(f'spectral centroid {centroid:6.0f} Hz   >2 kHz {above_2k * 100:4.1f}%   >5 kHz {above_5k * 100:4.1f}%   <200 Hz {below_200 * 100:4.1f}%')
    print(f'energy decay to -40 dB {t40 * 1000:4.0f} ms')
    print('10 ms loudness profile: ' + ' '.join(f'{value / peak_level:0.2f}' for value in rms[:120]))


def main() -> None:
    """Render, report, and write the WAV plus its base64 payload."""
    here = os.path.dirname(os.path.abspath(__file__))
    signal = downsample(render())
    report(signal)

    pcm = np.clip(signal, -1, 1)
    pcm = (pcm * 32767).astype('<i2')
    wav_path = os.path.join(here, 'coin.wav')
    with wave.open(wav_path, 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR_OUT)
        handle.writeframes(pcm.tobytes())

    with open(wav_path, 'rb') as handle:
        payload = base64.b64encode(handle.read()).decode('ascii')
    with open(os.path.join(here, 'coin.b64'), 'w', encoding='ascii') as handle:
        handle.write(payload)
    print(f'wrote coin.wav ({len(pcm) * 2} bytes) and coin.b64 ({len(payload)} chars)')


if __name__ == '__main__':
    main()
