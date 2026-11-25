"""Synthesises the surface and foliage sounds (original, generated from filtered noise):
step_gravel, rustle_grass, rustle_bush. 22050 Hz mono 16-bit like the other step sounds.
Usage: python3 tools/sfx_foliage.py"""
import wave
from pathlib import Path
import numpy as np

SR = 22050
OUT = Path(__file__).resolve().parents[1] / 'assets/audio/sfx'


def bandpass(x, lo, hi):
    f = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    f[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(f, len(x))


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t / decay)


def save(name, x, peak=0.6):
    x = x / (np.abs(x).max() + 1e-9) * peak
    x[-200:] *= np.linspace(1, 0, 200)
    with wave.open(str(OUT / (name + '.wav')), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())
    print(name, len(x) / SR, 's')


rng = np.random.default_rng(7)
# gravel: a cluster of tiny bright crunches
n = int(0.3 * SR)
g = np.zeros(n)
for _ in range(38):
    s = int(rng.uniform(0, 0.12) * SR + rng.exponential(0.02) * SR)
    m = int(0.025 * SR)
    if s + m < n:
        g[s:s + m] += bandpass(rng.normal(0, 1, m), 1800, 7000) * env(m, 0.001, 0.006) * rng.uniform(0.3, 1)
g += bandpass(rng.normal(0, 1, n), 300, 1500) * env(n, 0.004, 0.05) * 0.5
save('step_gravel', g, 0.55)
# grass rustle: soft swishy high noise with a slow swell
for k, dur in ((1, 0.42), (2, 0.36)):
    n = int(dur * SR)
    x = bandpass(rng.normal(0, 1, n), 2500, 9000)
    am = 0.6 + 0.4 * np.sin(np.arange(n) / SR * 2 * np.pi * rng.uniform(18, 26)) * rng.uniform(0.5, 1)
    save('rustle_grass' + ('' if k == 1 else '_b'), x * am * env(n, 0.06, 0.12), 0.38)
# bush rustle: leaves + twigs, lower and fuller
for k, dur in ((1, 0.55), (2, 0.5)):
    n = int(dur * SR)
    x = bandpass(rng.normal(0, 1, n), 900, 6000) * env(n, 0.03, 0.16)
    for _ in range(6):
        s = int(rng.uniform(0.02, dur * 0.7) * SR); m = int(0.012 * SR)
        x[s:s + m] += bandpass(rng.normal(0, 1, m), 2000, 8000) * env(m, 0.0005, 0.003) * 2.5
    save('rustle_bush' + ('' if k == 1 else '_b'), x, 0.45)
