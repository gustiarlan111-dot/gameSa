"""Synthesized one-shot voices: birds, insects, animals, water, objects, city. All original synthesis."""
import numpy as np

from dsp import SR, TAU, band, env_ad, env_hann, filt, noise, peak, tone


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def _n(sec):
    return int(sec * SR)


# ------------------------------------------------------------------ birds
def chirp(r, f0, f1, dur, harm=(1, 0.25, 0.08), curve=1.0):
    n = _n(dur)
    x = np.linspace(0, 1, n) ** curve
    f = f0 + (f1 - f0) * x
    return tone(f, harm) * env_hann(n)


def sparrow(r):
    """Busy little tweets: 3-7 short down-chirps."""
    out = []
    base = r.uniform(3200, 4800)
    for _ in range(r.integers(3, 8)):
        f0 = base * r.uniform(0.9, 1.15)
        out.append(chirp(r, f0, f0 * r.uniform(0.6, 0.8), r.uniform(0.04, 0.08)))
        out.append(np.zeros(_n(r.uniform(0.04, 0.11))))
    return np.concatenate(out)


def warbler(r):
    """Fast alternating trill that rises a little."""
    out = []
    a, b = r.uniform(2600, 3400), r.uniform(3600, 4600)
    k = r.integers(10, 22)
    for i in range(k):
        f = (a if i % 2 else b) * (1 + 0.15 * i / k)
        out.append(chirp(r, f, f * 0.85, 0.035, (1, 0.15)))
        out.append(np.zeros(_n(0.022)))
    x = np.concatenate(out)
    return x * np.linspace(0.6, 1, len(x))


def whistler(r):
    """Clear melodic whistle of 2-4 gliding notes (oriole/bulbul-like, not a real species copy)."""
    out = []
    notes = r.choice([1500, 1800, 2000, 2250, 2400, 2700, 3000], size=r.integers(2, 5))
    for i, f in enumerate(notes):
        g = f * r.uniform(0.85, 1.2)
        out.append(chirp(r, f, g, r.uniform(0.12, 0.26), (1, 0.05), curve=0.6))
        out.append(np.zeros(_n(r.uniform(0.02, 0.08))))
    return np.concatenate(out)


def cuckoo(r):
    """Soft two-note forest call, falling third, repeated 2-3 times."""
    out = []
    f = r.uniform(620, 760)
    for _ in range(r.integers(2, 4)):
        for ff, d in ((f, 0.22), (f * 0.84, 0.32)):
            n = _n(d)
            out.append(tone(np.full(n, ff), (1, 0.12, 0.04)) * env_ad(n, 0.03, d, 3))
            out.append(np.zeros(_n(0.1)))
        out.append(np.zeros(_n(0.45)))
    return np.concatenate(out)


def dove(r):
    """Low cooing (pigeon/turtle-dove), breathy."""
    out = []
    f = r.uniform(380, 480)
    for d, g in ((0.18, 1.0), (0.42, 1.1), (0.28, 0.95)):
        n = _n(d)
        t = np.arange(n) / SR
        fc = f * g * (1 + 0.03 * np.sin(TAU * 9 * t))
        v = tone(fc, (1, 0.35, 0.1)) * env_hann(n)
        out.append(v)
        out.append(np.zeros(_n(0.06)))
    x = np.concatenate(out)
    return filt(x, lambda fr: band(fr, None, 1400)) * 1.4


def owl(r):
    """Hoo ... hoo-hoo-hoooo."""
    f = r.uniform(330, 400)
    out = []
    for d, gap in ((0.42, 0.55), (0.18, 0.12), (0.18, 0.12), (0.7, 0.0)):
        n = _n(d)
        t = np.arange(n) / SR
        v = tone(f * (1 - 0.06 * t / d), (1, 0.18)) * env_ad(n, 0.06, d, 2.5)
        br = noise(n, r, f * 0.8, f * 3) * 0.08 * env_hann(n)
        out += [v + br, np.zeros(_n(gap))]
    return np.concatenate(out)


def woodpecker(r):
    hits = r.integers(10, 20)
    rate = r.uniform(14, 20)
    out = np.zeros(_n(hits / rate + 0.2))
    fc = r.uniform(900, 1500)
    for i in range(hits):
        n = _n(0.03)
        click = noise(n, r, fc * 0.6, fc * 2.5) * np.exp(-np.arange(n) / (SR * 0.006))
        p = int(i / rate * SR)
        out[p:p + n] += click * (1 - 0.5 * i / hits)
    return out


def gull(r):
    """Harbour gull cry: nasal 'kyaa' rising then falling, 1-3 times."""
    out = []
    for _ in range(r.integers(1, 4)):
        d = r.uniform(0.35, 0.6)
        n = _n(d)
        x = np.linspace(0, 1, n)
        f = r.uniform(700, 900) * (1 + 0.7 * np.sin(np.pi * x ** 0.7)) * (1 + 0.02 * np.sin(TAU * 30 * x * d))
        v = tone(f, (1, 0.8, 0.6, 0.45, 0.3, 0.2))
        v = filt(v, lambda fr: peak(fr, 1900, 2.5) + 0.5 * peak(fr, 3200, 3))
        out += [v * env_ad(n, 0.04, d, 2.0), np.zeros(_n(r.uniform(0.08, 0.2)))]
    return np.concatenate(out)


# ------------------------------------------------------------------ insects / amphibians
def cricket_chirp(r, fc, pulses=3, prate=28):
    n = _n(pulses / prate)
    t = np.arange(n) / SR
    am = np.maximum(0, np.sin(np.pi * prate * t)) ** 2
    return np.sin(TAU * fc * t) * am


def frog(r):
    """Croak: a 0.3-0.6 s pulse train through a throat resonance."""
    d = r.uniform(0.25, 0.55)
    n = _n(d)
    t = np.arange(n) / SR
    rate = r.uniform(16, 28)
    f0 = r.uniform(140, 260)
    src = tone(np.full(n, f0), [1 / (k + 1) for k in range(10)])
    am = np.maximum(0, np.sin(np.pi * rate * t)) ** 3
    v = filt(src * am, lambda fr: peak(fr, r.uniform(500, 900), 3) + 0.4 * peak(fr, 1600, 4))
    return v * env_hann(n)


def tokek(r):
    """Gecko call, Indonesian evenings: a throaty rattle, then 4-7 'to-keh' pairs that slow down."""
    out = [np.zeros(_n(0.1))]
    rr = _n(0.5)
    out.append(filt(noise(rr, r, 200, 1200) * np.maximum(0, np.sin(TAU * 18 * np.arange(rr) / SR)) ** 2 * env_hann(rr), lambda f: peak(f, 500, 2)) * 0.4)
    out.append(np.zeros(_n(0.35)))
    reps = r.integers(4, 8)
    for i in range(reps):
        for syl, d, f0, fm in (("to", 0.09, 300, 900), ("keh", 0.2, 230, 700)):
            n = _n(d)
            t = np.arange(n) / SR
            src = tone(np.full(n, f0) * (1 - 0.15 * t / d), [1 / (k + 1) ** 0.8 for k in range(12)])
            if syl == "keh":
                src += noise(n, r, 600, 3000) * 0.25
            v = filt(src, lambda fr: peak(fr, fm, 2.5) + 0.3 * peak(fr, fm * 2.2, 3))
            out += [v * env_ad(n, 0.01, d, 3), np.zeros(_n(0.06))]
        out.append(np.zeros(_n(0.55 + 0.12 * i)))
    x = np.concatenate(out)
    return x / (np.max(np.abs(x)) + 1e-9)


# ------------------------------------------------------------------ water
def bubble(r, f0, dur=None, rise=None):
    dur = dur or r.uniform(0.008, 0.05)
    n = _n(dur * 3)
    t = np.arange(n) / SR
    rise = rise if rise is not None else r.uniform(0.5, 3.0)
    f = f0 * (1 + rise * t / dur * 0.15)
    return np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / dur)


def drip(r, f0=None):
    f0 = f0 or r.uniform(900, 2200)
    x = bubble(r, f0, r.uniform(0.02, 0.05), r.uniform(2, 5))
    tick = np.zeros(len(x))
    tick[:80] = noise(80, r, 2000, 9000) * np.linspace(1, 0, 80) * 0.3
    return x + tick


def splash(r, dur=0.6):
    n = _n(dur)
    t = np.arange(n) / SR
    x = noise(n, r, 400, 7000, tilt=-0.5) * np.exp(-t / (dur * 0.25)) * 0.6
    for _ in range(25):
        b = bubble(r, r.uniform(500, 2500))
        p = r.integers(0, max(1, n - len(b)))
        x[p:p + len(b)] += b * r.uniform(0.1, 0.4) * np.exp(-p / (SR * dur * 0.4))
    return x


# ------------------------------------------------------------------ bells, wood, objects
def bell(r, f0, partials=((1, 1), (2.0, 0.5), (2.76, 0.6), (5.4, 0.25), (8.93, 0.1)), decay=2.0, strike=0.004):
    n = _n(decay * 1.5)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, a in partials:
        x += a * np.sin(TAU * f0 * k * t + r.uniform(0, TAU)) * np.exp(-t * (1 + k * 0.6) / decay)
    hit = _n(strike)
    x[:hit] += noise(hit, r, 1000, 10000) * 0.3
    return x * np.minimum(1, t / 0.002)


def wind_chime(r, scale=(1046.5, 1174.7, 1318.5, 1568.0, 1760.0, 2093.0)):
    out = np.zeros(_n(4.5))
    hits = r.integers(3, 8)
    p = 0
    for _ in range(hits):
        b = bell(r, r.choice(scale), ((1, 1), (2.76, 0.35), (5.4, 0.12)), decay=1.6) * r.uniform(0.3, 1)
        end = min(len(out), p + len(b))
        out[p:end] += b[:end - p]
        p += _n(r.uniform(0.07, 0.4))
        if p >= len(out):
            break
    return out


def crystal(r):
    f = r.choice([1567.98, 1760.0, 2093.0, 2349.3, 2637.0, 3136.0])
    return bell(r, f, ((1, 1), (2.32, 0.4), (4.25, 0.2), (6.63, 0.08)), decay=2.6)


def buoy_bell(r):
    return bell(r, r.uniform(290, 330), ((1, 1), (2.0, 0.6), (2.4, 0.4), (3.0, 0.3), (4.2, 0.2)), decay=3.5) * 0.8


def creak(r):
    """Wood/rope stick-slip creak (pier, moored boat)."""
    d = r.uniform(0.5, 1.1)
    n = _n(d)
    x = np.zeros(n)
    t = 0.0
    rate0, rate1 = r.uniform(120, 260), r.uniform(200, 420)
    while t < d:
        rate = rate0 + (rate1 - rate0) * t / d
        p = int(t * SR)
        x[p] += r.uniform(0.5, 1)
        t += 1 / rate * r.uniform(0.85, 1.15)
    x = filt(x, lambda f: peak(f, r.uniform(280, 420), 4) + 0.7 * peak(f, r.uniform(800, 1200), 5) + 0.3 * peak(f, 2300, 4))
    return x * env_hann(n)


def ship_horn(r):
    d = 2.6
    n = _n(d)
    t = np.arange(n) / SR
    f = r.uniform(98, 118)
    v = tone(np.full(n, f), [1 / (k + 1) ** 0.7 for k in range(14)])
    v *= np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 0.6)
    return filt(v, lambda fr: band(fr, 60, 900))


def car_horn(r):
    d = r.uniform(0.18, 0.4)
    n = _n(d)
    v = tone(np.full(n, 415.0), (1, 0.5, 0.33, 0.25)) + tone(np.full(n, 520.0), (1, 0.5, 0.33, 0.25))
    v = filt(v, lambda f: band(f, 200, 2500)) * env_ad(n, 0.01, d, 1.5)
    return v


def bike_bell(r):
    out = np.zeros(_n(1.4))
    for i in range(2):
        b = bell(r, 2350, ((1, 1), (1.47, 0.5), (2.1, 0.3)), decay=0.8)[:_n(1.2)]
        p = _n(0.16 * i)
        out[p:p + len(b)] += b[:len(out) - p]
    return out


def bus_hiss(r):
    d = 1.1
    n = _n(d)
    t = np.arange(n) / SR
    return noise(n, r, 1800, 9000) * np.minimum(1, t / 0.02) * np.exp(-t / 0.35)


def crossing_beep(r):
    out = []
    for _ in range(8):
        n = _n(0.07)
        t = np.arange(n) / SR
        out += [np.sign(np.sin(TAU * 2400 * t)) * 0.35 * env_hann(n), np.zeros(_n(0.18))]
    return filt(np.concatenate(out), lambda f: band(f, 500, 6000))


def train(r):
    """Distant commuter train: rumble with wheel clacks and a two-tone horn."""
    d = 9.0
    n = _n(d)
    t = np.arange(n) / SR
    envl = np.sin(np.pi * t / d) ** 1.5
    rum = noise(n, r, 30, 300, tilt=-1) * 0.6
    clk = np.zeros(n)
    tt = 0.3
    while tt < d - 0.2:
        for o in (0, 0.11):
            p = int((tt + o) * SR)
            k = _n(0.03)
            clk[p:p + k] += noise(k, r, 200, 1800) * np.exp(-np.arange(k) / (SR * 0.006))
        tt += 0.62
    x = (rum + clk * 0.7) * envl
    hp = _n(1.8)
    h0 = int(2.2 * SR)
    th = np.arange(hp) / SR
    horn = tone(np.full(hp, 330.0), (1, .5, .3)) + tone(np.full(hp, 415.3), (1, .5, .3))
    x[h0:h0 + hp] += horn * np.minimum(1, th / 0.1) * np.minimum(1, (1.8 - th) / 0.3) * 0.18
    return filt(x, lambda f: band(f, None, 1800))


def cup_clink(r):
    out = np.zeros(_n(0.7))
    for i in range(r.integers(1, 3)):
        f = r.uniform(2600, 3800)
        b = bell(r, f, ((1, 1), (1.63, 0.6), (2.7, 0.3)), decay=0.18)[:_n(0.4)]
        p = _n(0.09 * i)
        out[p:p + len(b)] += b * r.uniform(0.6, 1)
    return out


def espresso(r):
    d = 2.8
    n = _n(d)
    t = np.arange(n) / SR
    x = noise(n, r, 1500, 9000) * np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 0.4) * 0.5
    g = np.zeros(n)
    for _ in range(140):
        b = bubble(r, r.uniform(300, 900), 0.02)
        p = r.integers(0, n - len(b))
        g[p:p + len(b)] += b * 0.15
    return x + g


def arcade_bleep(r):
    notes = r.choice([523.3, 659.3, 784.0, 1046.5, 1318.5, 1568.0], size=r.integers(3, 7))
    out = []
    for f in notes:
        n = _n(0.06)
        t = np.arange(n) / SR
        out.append(np.sign(np.sin(TAU * f * t)) * 0.3 * env_ad(n, 0.002, 0.06, 2))
    return filt(np.concatenate(out), lambda fr: band(fr, 200, 5000))


def thunder(r):
    d = r.uniform(5, 7)
    n = _n(d)
    t = np.arange(n) / SR
    e = np.zeros(n)
    for _ in range(r.integers(3, 6)):
        c = r.uniform(0.2, d * 0.6)
        e += r.uniform(0.4, 1) * np.exp(-np.abs(t - c) / r.uniform(0.3, 1.0))
    e *= np.minimum(1, t / 0.05)
    x = noise(n, r, 20, 600, tilt=-2) * e
    return x / (np.max(np.abs(x)) + 1e-9)


def fish_splash(r):
    return splash(r, 0.5) * 0.8


def twinkle(r):
    out = np.zeros(_n(2.5))
    p = 0
    for f in r.choice([2093.0, 2349.3, 2637.0, 3136.0, 3520.0, 4186.0], size=r.integers(3, 6)):
        b = bell(r, f, ((1, 1), (2.0, 0.3), (3.0, 0.1)), decay=0.9)[:_n(1.5)] * r.uniform(0.3, 0.8)
        end = min(len(out), p + len(b))
        out[p:end] += b[:end - p]
        p += _n(r.uniform(0.05, 0.2))
    return out


def whisper(r):
    """Soft breathy swell (fading memories) - no words, just air shaped like a voice."""
    d = r.uniform(1.4, 2.4)
    n = _n(d)
    t = np.arange(n) / SR
    x = noise(n, r, 300, 6000)
    syl = np.maximum(0, np.sin(TAU * r.uniform(3, 5) * t)) ** 1.5
    x = filt(x, lambda f: peak(f, r.uniform(600, 900), 3) + peak(f, r.uniform(1400, 2200), 4) + 0.5 * peak(f, 3000, 4))
    return x * syl * env_hann(n) * 0.8


def clock_chime(r):
    """Old wall clock striking (rumah nenek): 3 soft gong strikes."""
    out = np.zeros(_n(6.5))
    for i in range(3):
        b = bell(r, 196.0, ((1, 1), (2.0, 0.5), (3.0, 0.35), (4.2, 0.2), (5.4, 0.1)), decay=2.0)[:_n(4.5)]
        p = _n(1.1 * i)
        out[p:p + len(b)] += b[:len(out) - p]
    return out


def kettle(r):
    d = 3.5
    n = _n(d)
    t = np.arange(n) / SR
    f = 1800 + 500 * t / d
    w = np.sin(TAU * np.cumsum(f) / SR) * np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 0.3)
    return w * 0.25 + noise(n, r, 2000, 8000) * 0.1 * np.minimum(1, t / 0.5)


def dog_far(r):
    out = []
    for _ in range(r.integers(1, 4)):
        d = 0.16
        n = _n(d)
        t = np.arange(n) / SR
        f = r.uniform(420, 520) * (1 - 0.3 * t / d)
        v = tone(f, [1 / (k + 1) ** 0.6 for k in range(10)]) + noise(n, r, 500, 3000) * 0.3
        v = filt(v, lambda fr: peak(fr, 900, 2) + 0.5 * peak(fr, 1800, 3))
        out += [v * env_ad(n, 0.01, d, 3), np.zeros(_n(r.uniform(0.15, 0.35)))]
    return filt(np.concatenate(out), lambda f: band(f, None, 2200))
