"""V8 sound effects, synthesised from filtered noise and tones (original, no third-party audio):
  step_stairs   heel on a stone step: short click + hollow low knock, a little brighter than step_stone
22050 Hz mono 16-bit like the other step sounds.
Usage: python3 tools/sfx_v8.py"""
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
    print(name, round(len(x) / SR, 3), 's')


def step_stairs(seed=8):
    rng = np.random.default_rng(seed)
    n = int(SR * 0.16)
    t = np.arange(n) / SR
    click = bandpass(rng.standard_normal(n), 2200, 6500) * env(n, 0.0008, 0.008)
    knock = np.sin(2 * np.pi * (180 - 60 * t / t[-1]) * t) * env(n, 0.002, 0.035)
    grit = bandpass(rng.standard_normal(n), 600, 2400) * env(n, 0.003, 0.025) * 0.5
    return click * 0.9 + knock * 1.1 + grit


if __name__ == '__main__':
    save('step_stairs', step_stairs(), 0.55)
