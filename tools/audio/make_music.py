#!/usr/bin/env python3
"""Original looping area themes, synthesized from scratch (electric piano, plucked guitar,
musette reed, music box, upright-ish bass, brushes). Rendered circularly so they loop cleanly.

    python3 tools/audio/make_music.py [name ...]

harbor_day      Dermaga by day: a lilting 6/8 harbour waltz with a musette reed.
street_stroll   Jalan Kota by day: an easy swing stroll on electric piano.
grandma_house   Rumah Nenek Sari: a slow 3/4 music-box lullaby with nylon guitar.
gallery_light   Galeri Komunitas: airy, soft piano over a warm pad.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from dsp import SR, TAU, band, conv, filt, noise, norm, rng, room_ir, write_ogg  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "audio", "music")


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------------ instruments (mono note renderers)
def epiano(f, dur, vel, r):
    n = int((dur + 1.2) * SR)
    t = np.arange(n) / SR
    idx = 1.6 * vel * np.exp(-t * 3.0)
    mod = np.sin(TAU * f * t) * idx
    car = np.sin(TAU * f * t + mod)
    tine = np.sin(TAU * f * 7.1 * t) * np.exp(-t * 18) * 0.08 * vel
    rel = np.clip((dur + 0.25 - t) / 0.25, 0, 1)
    return (car + tine) * np.exp(-t * 0.9) * rel * vel


def pluck(f, dur, vel, r, bright=0.5, decay=0.996):
    """Karplus-Strong string, vectorised one period at a time."""
    n = int((dur + 1.5) * SR)
    p = max(2, int(round(SR / f)))
    y = np.zeros(n + p + 1)
    burst = r.uniform(-1, 1, p)
    burst = filt(burst, lambda fr: band(fr, None, 1500 + 6000 * bright)) if p > 16 else burst
    y[1:p + 1] = burst
    k = p + 1
    while k < len(y):
        e = min(len(y), k + p)
        y[k:e] = decay * 0.5 * (y[k - p:e - p] + y[k - p - 1:e - p - 1])
        k = e
    y = y[1:n + 1]
    t = np.arange(n) / SR
    rel = np.clip((dur + 0.3 - t) / 0.3, 0, 1)
    return y * rel * vel


def reed(f, dur, vel, r):
    """Musette-style reed: two slightly detuned saws, soft filter, tremolo."""
    n = int((dur + 0.3) * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for det in (-0.25, 0.0, 0.3):
        ff = f * 2 ** (det / 12 / 4)
        for k in range(1, 12):
            x += np.sin(TAU * ff * k * t) / k ** 1.25
    x = filt(x, lambda fr: band(fr, 150, 2600) * (1 + 0.8 * np.exp(-((fr - 1200) / 500) ** 2)))
    env = np.minimum(1, t / 0.05) * np.clip((dur + 0.15 - t) / 0.15, 0, 1)
    return x * env * (1 + 0.12 * np.sin(TAU * 5.5 * t)) * vel * 0.25


def musicbox(f, dur, vel, r):
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    x = np.sin(TAU * f * t) * np.exp(-t * 1.6) + 0.35 * np.sin(TAU * f * 3.0 * t) * np.exp(-t * 4) + 0.15 * np.sin(TAU * f * 5.4 * t) * np.exp(-t * 9)
    x[:60] += r.uniform(-1, 1, 60) * 0.2
    return x * vel


def bass(f, dur, vel, r):
    n = int((dur + 0.2) * SR)
    t = np.arange(n) / SR
    x = np.sin(TAU * f * t) + 0.3 * np.sin(TAU * 2 * f * t) * np.exp(-t * 4) + 0.1 * np.sin(TAU * 3 * f * t) * np.exp(-t * 8)
    return x * np.minimum(1, t / 0.008) * np.exp(-t * 1.2) * np.clip((dur + 0.08 - t) / 0.08, 0, 1) * vel


def pad(f, dur, vel, r):
    n = int((dur + 1.5) * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(TAU * f * 2 ** (d / 1200) * t * k) / k ** 1.5 for d in (-7, 0, 7) for k in (1, 2, 3))
    env = np.minimum(1, t / 0.8) * np.clip((dur + 1.2 - t) / 1.2, 0, 1)
    return x * env * vel * 0.12


def soft_piano(f, dur, vel, r):
    n = int((dur + 2.0) * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, a in ((1, 1), (2, 0.45), (3, 0.2), (4, 0.12), (5, 0.06)):
        x += a * np.sin(TAU * f * k * 1.0004 ** (k * k) * t) * np.exp(-t * (0.9 + 0.7 * k))
    x[:40] += r.uniform(-1, 1, 40) * 0.05
    rel = np.clip((dur + 0.4 - t) / 0.4, 0, 1)
    return x * rel * vel * np.minimum(1, t / 0.004)


def drum(kind, r):
    if kind == "kick":
        n = int(0.35 * SR)
        t = np.arange(n) / SR
        f = 48 + 60 * np.exp(-t * 30)
        return np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t * 9)
    if kind == "brush":
        n = int(0.22 * SR)
        t = np.arange(n) / SR
        return noise(n, r, 2500, 11000) * np.exp(-t * 18) * 0.35
    if kind == "swish":
        n = int(0.4 * SR)
        t = np.arange(n) / SR
        return noise(n, r, 1500, 9000) * np.sin(np.pi * t / 0.4) ** 2 * 0.2
    if kind == "rim":
        n = int(0.06 * SR)
        t = np.arange(n) / SR
        return (noise(n, r, 1500, 6000) * 0.5 + np.sin(TAU * 1700 * t)) * np.exp(-t * 80) * 0.4
    if kind == "shaker":
        n = int(0.09 * SR)
        t = np.arange(n) / SR
        return noise(n, r, 5000, 12000) * np.sin(np.pi * t / 0.09) * 0.25
    raise ValueError(kind)


class Song:
    def __init__(self, seconds, seed):
        self.n = int(seconds * SR)
        self.r = rng(seed)
        self.buses = {}

    def add(self, bus, x, t, pan=0.0, gain=1.0):
        b = self.buses.setdefault(bus, np.zeros((self.n, 2)))
        a = (pan + 1) * np.pi / 4
        idx = (np.arange(len(x)) + int(t * SR)) % self.n
        np.add.at(b, idx, np.stack([x * gain * np.cos(a), x * gain * np.sin(a)], axis=1))

    def note(self, bus, inst, m, t, dur, vel=0.8, pan=0.0, **kw):
        self.add(bus, inst(hz(m), dur, vel * self.r.uniform(0.9, 1.0), self.r, **kw), t + self.r.uniform(0, 0.008), pan)

    def mix(self, levels, verb=1.8, wet=0.22):
        out = np.zeros((self.n, 2))
        send = np.zeros((self.n, 2))
        for bus, (g, s) in levels.items():
            if bus in self.buses:
                out += self.buses[bus] * g
                send += self.buses[bus] * g * s
        ir = room_ir(verb, self.r, 6000, 120)
        for c in range(2):
            out[:, c] += wet * conv(send[:, c], np.roll(ir, c * 41))
        out = np.stack([filt(out[:, c], lambda f: band(f, 35, 14000)) for c in range(2)], axis=1)
        return norm(out, -1.0, -19)


def chord_tones(root, quality):
    iv = {"maj": [0, 4, 7], "min": [0, 3, 7], "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "7": [0, 4, 7, 10], "add9": [0, 4, 7, 14]}[quality]
    return [root + i for i in iv]


def melody_line(r, chords, scale, beats_per_bar, rhythm, lo, hi, start):
    """Chord-tone-on-strong-beat walk: returns [(beat, dur, midi)]."""
    out = []
    cur = start
    for bar, (root, q) in enumerate(chords):
        ct = chord_tones(root, q)
        pattern = rhythm[bar % len(rhythm)]
        for (b, d) in pattern:
            strong = abs(b - round(b)) < 1e-6 and int(b) % 2 == 0
            if strong:
                cands = [m for m in range(lo, hi + 1) if (m - ct[0]) % 12 in [(c - ct[0]) % 12 for c in ct]]
            else:
                cands = [m for m in range(lo, hi + 1) if m % 12 in scale]
            cands.sort(key=lambda m: abs(m - cur) + r.uniform(0, 2.5))
            cur = cands[0] if abs(cands[0] - cur) > 0 or r.random() < 0.3 else cands[min(1, len(cands) - 1)]
            out.append((bar * beats_per_bar + b, d, cur))
    return out


# ------------------------------------------------------------------ songs
def harbor_day():
    eighth = 0.2
    bar = 6 * eighth
    prog = [(55, "maj"), (52, "min"), (48, "maj"), (50, "maj"), (55, "maj"), (52, "min"), (57, "min"), (50, "7")] * 2 + \
           [(48, "maj"), (50, "maj"), (55, "maj"), (52, "min"), (48, "maj"), (50, "7"), (55, "maj"), (55, "maj")] * 2
    s = Song(len(prog) * bar, 11)
    r = s.r
    G = [7, 9, 11, 0, 2, 4, 6]
    rhythm = [[(0, 1.5), (1.5, 0.5), (2, 1)], [(0, 1), (1, 1), (2, 1)], [(0, 2), (2, 1)], [(0, 0.5), (0.5, 0.5), (1, 1), (2, 1)]]
    # melody in dotted-quarter "beats" (2 per bar) -> express as 3 eighths per beat: use beat=1.5 eighths unit
    mel = melody_line(r, prog, G, 3, rhythm, 67, 83, 74)
    for i, (b, d, m) in enumerate(mel):
        sec = 16 * bar <= b * 2 * eighth < 24 * bar
        if sec and r.random() < 0.25:
            continue
        s.note("lead", reed, m, b * 2 * eighth, d * 2 * eighth * 0.95, 0.7, 0.15)
    for i, (root, q) in enumerate(prog):
        t0 = i * bar
        ct = chord_tones(root, q)
        arp = [ct[0], ct[1] + 12, ct[2], ct[1] + 12, ct[2] + 12, ct[1] + 12]
        for k, m in enumerate(arp):
            s.note("gtr", pluck, m, t0 + k * eighth, 0.5, 0.55 if k else 0.7, -0.35, bright=0.4)
        s.note("bass", bass, root - 12, t0, 0.55, 0.9)
        s.note("bass", bass, ct[2] - 12, t0 + 3 * eighth, 0.5, 0.7)
        for k in range(6):
            s.add("drum", drum("shaker", r), t0 + k * eighth, 0.4, 0.8 if k in (0, 3) else 0.45)
        if i % 2 == 1:
            s.add("drum", drum("swish", r), t0 + 4.5 * eighth, -0.2, 0.6)
    return s.mix({"lead": (0.9, 0.35), "gtr": (0.8, 0.3), "bass": (0.75, 0.05), "drum": (0.45, 0.2)}, 1.6, 0.25)


def street_stroll():
    beat = 60 / 96
    bar = 4 * beat
    sw = 0.62    # swing ratio
    prog = [(53, "maj7"), (50, "m7"), (55, "m7"), (48, "7")] * 2 + [(58, "maj7"), (57, "m7"), (50, "m7"), (55, "7"), (55, "m7"), (48, "7"), (53, "maj7"), (48, "7")] + [(53, "maj7"), (50, "m7"), (55, "m7"), (48, "7")] * 2
    s = Song(len(prog) * bar, 23)
    r = s.r
    F = [5, 7, 9, 10, 0, 2, 4]

    def swung(b):
        whole = int(b)
        frac = b - whole
        return (whole + (sw if abs(frac - 0.5) < 1e-6 else frac)) * beat

    rhythm = [[(0, 1), (1.5, 0.5), (2, 1.5)], [(0.5, 0.5), (1, 0.5), (1.5, 1), (3, 1)], [(0, 2), (2.5, 0.5), (3, 1)], [(0, 0.5), (0.5, 0.5), (1, 0.5), (1.5, 0.5), (2, 2)]]
    mel = melody_line(r, prog, F, 4, rhythm, 65, 81, 72)
    for b, d, m in mel:
        bar_i = int(b // 4)
        if bar_i % 8 == 7 and b % 4 >= 2:
            continue      # breathe at the end of each phrase
        s.note("lead", pluck, m, swung(b), d * beat, 0.65, 0.25, bright=0.55, decay=0.997)
    for i, (root, q) in enumerate(prog):
        t0 = i * bar
        ct = chord_tones(root, q)
        voicing = [ct[1], ct[2], ct[3] if len(ct) > 3 else ct[0] + 12]
        for (b, d) in ((0, 1.4), (1.5, 0.4), (2.5, 1.2)) if i % 2 == 0 else ((0.5, 1.0), (2, 1.0), (3.5, 0.4)):
            for m in voicing:
                s.note("keys", epiano, m, t0 + swung(b), d * beat, 0.32, -0.2)
        walk = [root - 12, ct[1] - 12, ct[2] - 12, (prog[(i + 1) % len(prog)][0] - 12) + (1 if r.random() < 0.5 else -1)]
        for k, m in enumerate(walk):
            s.note("bass", bass, m, t0 + k * beat, beat * 0.9, 0.85 if k == 0 else 0.7)
        for k in range(4):
            s.add("drum", drum("brush", r), t0 + k * beat, 0.3, 0.7)
            s.add("drum", drum("brush", r), t0 + (k + sw) * beat, 0.35, 0.4)
            if k in (1, 3):
                s.add("drum", drum("rim", r), t0 + k * beat, -0.1, 0.45)
            if k == 0:
                s.add("drum", drum("kick", r), t0, 0.0, 0.5)
    return s.mix({"lead": (0.85, 0.3), "keys": (0.8, 0.25), "bass": (0.8, 0.05), "drum": (0.5, 0.15)}, 1.4, 0.2)


def grandma_house():
    beat = 60 / 78
    bar = 3 * beat
    prog = [(50, "maj"), (47, "min"), (43, "maj"), (45, "maj"), (50, "maj"), (54, "min"), (43, "maj"), (45, "7")] * 2 + \
           [(43, "maj"), (45, "maj"), (47, "min"), (54, "min"), (43, "maj"), (45, "maj"), (50, "maj"), (50, "maj")]
    s = Song(len(prog) * bar, 37)
    r = s.r
    D = [2, 4, 6, 7, 9, 11, 1]
    rhythm = [[(0, 2), (2, 1)], [(0, 1), (1, 1), (2, 1)], [(0, 3)], [(0, 1.5), (1.5, 0.5), (2, 1)]]
    mel = melody_line(r, prog, D, 3, rhythm, 74, 90, 81)
    for b, d, m in mel:
        s.note("box", musicbox, m, b * beat, d * beat, 0.55, 0.2)
    for i, (root, q) in enumerate(prog):
        t0 = i * bar
        ct = chord_tones(root, q)
        for k, m in enumerate([ct[0], ct[2], ct[1] + 12]):
            s.note("gtr", pluck, m + 12 if k else m, t0 + k * beat, beat * 1.2, 0.5, -0.3, bright=0.25)
        s.note("pad", pad, ct[0] + 12, t0, bar, 0.5)
        s.note("pad", pad, ct[1] + 12, t0, bar, 0.4)
    return s.mix({"box": (0.8, 0.45), "gtr": (0.75, 0.3), "pad": (0.5, 0.4)}, 2.2, 0.3)


def gallery_light():
    beat = 60 / 70
    bar = 4 * beat
    prog = [(48, "add9"), (52, "min"), (45, "min"), (53, "maj7"), (48, "add9"), (55, "maj"), (53, "maj7"), (55, "7")] * 3
    s = Song(len(prog) * bar, 41)
    r = s.r
    C_ = [0, 2, 4, 5, 7, 9, 11]
    rhythm = [[(0, 1.5), (1.5, 0.5), (2, 2)], [(0, 3), (3, 1)], [(0.5, 0.5), (1, 1), (2, 2)], [(0, 4)]]
    mel = melody_line(r, prog, C_, 4, rhythm, 72, 88, 79)
    for b, d, m in mel:
        if int(b // 4) < 8 and r.random() < 0.4:
            continue    # sparse first section
        s.note("pno", soft_piano, m, b * beat, d * beat, 0.5, 0.15)
    for i, (root, q) in enumerate(prog):
        t0 = i * bar
        ct = chord_tones(root, q)
        for k, m in enumerate([ct[0] - 12, ct[1], ct[2], ct[1] + 12]):
            s.note("pno", soft_piano, m, t0 + k * beat * 0.5, bar * 0.9, 0.32, -0.2)
        s.note("pad", pad, ct[0], t0, bar, 0.55)
        s.note("pad", pad, ct[2], t0, bar, 0.4)
    return s.mix({"pno": (0.85, 0.45), "pad": (0.55, 0.5)}, 2.8, 0.35)


SONGS = {"harbor_day": harbor_day, "street_stroll": street_stroll, "grandma_house": grandma_house, "gallery_light": gallery_light}

if __name__ == "__main__":
    for name in (sys.argv[1:] or SONGS):
        x = SONGS[name]()
        p = os.path.join(OUT, name + ".ogg")
        write_ogg(p, x, 2)
        print(name, "%.1fs" % (len(x) / SR), os.path.getsize(p) // 1024, "KB")
