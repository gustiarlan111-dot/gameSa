"""Tiny numpy DSP kit for the game's original synthesized sounds (no samples, no external assets).

Everything that loops is built circularly: noise is shaped in the frequency domain (so it is
periodic over the buffer), every LFO/tone runs a whole number of cycles over the loop, and events
wrap around the end. The result loops with no seam and no crossfade.
"""
import os
import subprocess
import wave

import numpy as np

SR = 32000
TAU = 2 * np.pi


def rng(seed):
    return np.random.default_rng(seed)


def freqs(n):
    return np.fft.rfftfreq(n, 1 / SR)


def band(f, lo=None, hi=None, k=2.0):
    """Smooth band-pass magnitude response (k = steepness)."""
    g = np.ones_like(f)
    if lo:
        g /= 1 + (lo / np.maximum(f, 1e-3)) ** (2 * k)
    if hi:
        g /= 1 + (f / hi) ** (2 * k)
    return g


def peak(f, fc, q):
    """Resonant peak (approximate band-pass bell) for formants/resonances."""
    return 1 / (1 + ((f - fc) / (fc / q)) ** 2)


def noise(n, r, lo=None, hi=None, tilt=0.0, k=2.0):
    """Periodic noise with a band shape; tilt -1 = pink, -2 = brown (per octave power slope)."""
    f = freqs(n)
    mag = band(f, lo, hi, k) * np.where(f > 0, (np.maximum(f, 20) / 1000.0) ** (tilt / 2), 0)
    spec = mag * r.rayleigh(1, len(f)) * np.exp(1j * r.uniform(0, TAU, len(f)))
    x = np.fft.irfft(spec, n)
    return x / (np.std(x) + 1e-12)


def filt(x, shape):
    """Circular FFT filter; shape(f) -> gain array."""
    n = len(x)
    return np.fft.irfft(np.fft.rfft(x) * shape(freqs(n)), n)


def conv(x, ir):
    n = len(x)
    return np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(ir, n), n)


def room_ir(seconds, r, hi=6000, lo=80):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = noise(n, r, lo, hi) * np.exp(-6.9 * t / seconds)
    ir[0] = 0
    return ir / np.sqrt(np.sum(ir ** 2))


def lfo(n, cycles, phase=0.0):
    return np.sin(TAU * cycles * np.arange(n) / n + phase)


def gusts(n, r, slow=(1, 7), amount=0.7):
    """0..1 periodic swell built from a few whole-cycle sines."""
    g = np.zeros(n)
    for c in range(slow[0], slow[1] + 1):
        g += r.uniform(0.3, 1.0) / c ** 0.6 * lfo(n, c, r.uniform(0, TAU))
    g = (g - g.min()) / (g.max() - g.min() + 1e-12)
    return (1 - amount) + amount * g


def qfreq(hz, n):
    """Snap a frequency so it completes whole cycles over n samples (seamless tones)."""
    step = SR / n
    return max(step, round(hz / step) * step)


def env_ad(n, a, d, shape=4.0):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-5), np.exp(-shape * (t - a) / max(d, 1e-5)))
    return e * np.minimum(1, (n - np.arange(n)) / (0.006 * SR))     # always land on zero (no click)


def env_hann(n):
    return np.sin(np.pi * np.arange(n) / max(n - 1, 1)) ** 2


def tone(freq_curve, amps=(1.0,), inharm=None):
    """Additive tone following a per-sample frequency curve."""
    ph = TAU * np.cumsum(freq_curve) / SR
    out = np.zeros_like(freq_curve)
    ratios = inharm if inharm is not None else [i + 1 for i in range(len(amps))]
    for a, k in zip(amps, ratios):
        out += a * np.sin(ph * k)
    return out


def pan_st(x, pan):
    """Equal-power pan, pan in [-1, 1] -> (n, 2)."""
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def place(buf, ev, pos, gain=1.0, pan=0.0, wrap=True):
    """Add a mono event into a stereo (n,2) buffer at sample pos (wrapping around)."""
    n = len(buf)
    st = pan_st(ev * gain, pan)
    idx = (np.arange(len(ev)) + int(pos))
    if wrap:
        idx %= n
        np.add.at(buf, idx, st)
    else:
        ok = idx < n
        buf[idx[ok]] += st[ok]


def stereo(x, width=0.0, r=None):
    """Mono -> stereo with optional decorrelation (a tiny circular delay on one side)."""
    if width <= 0:
        return np.stack([x, x], axis=1)
    d = int(0.011 * SR * width)
    return np.stack([x, np.roll(x, d)], axis=1)


def norm(x, peak_db=-1.0, rms_db=None):
    x = x - np.mean(x, axis=0)
    if rms_db is not None:
        x = x * (10 ** (rms_db / 20) / (np.sqrt(np.mean(x ** 2)) + 1e-12))
    lim = 10 ** (peak_db / 20)
    if rms_db is None:
        return x * (lim / (np.max(np.abs(x)) + 1e-12))
    # keep the loudness target; tame rare peaks with a soft clip instead of turning it all down
    return lim * np.tanh(x / lim)


def write_ogg(path, x, quality=1, sr=SR):
    """Write float audio (n,) or (n,2) as Ogg Vorbis via ffmpeg."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = x[:, None]
    tmp = path + ".tmp.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-c:a", "libvorbis", "-q:a", str(quality), path], check=True)
    os.remove(tmp)


def write_wav(path, x, sr=SR):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = x[:, None]
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype("<i2").tobytes())
