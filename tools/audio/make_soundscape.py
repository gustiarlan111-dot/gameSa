#!/usr/bin/env python3
"""Builds the per-area soundscape: looping layers, positional emitter loops and random one-shot
"spot" sounds, all synthesized here from scratch (no recorded or third-party audio), plus
assets/audio/area_sound.json that says which area uses what.

    python3 tools/audio/make_soundscape.py            # everything (~3 min)
    python3 tools/audio/make_soundscape.py layers     # only loops
    python3 tools/audio/make_soundscape.py spots      # only one-shots
    python3 tools/audio/make_soundscape.py json       # only the profile table

Loops are 32 s, built circularly (see dsp.py) so they repeat without a seam. Stereo Ogg Vorbis
at 32 kHz, quality 0-1, to stay light on phones.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import voices as V  # noqa: E402
from dsp import (SR, TAU, band, conv, filt, gusts, lfo, noise, norm, peak, place, qfreq, rng,  # noqa: E402
                 room_ir, stereo, write_ogg)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AMB = os.path.join(ROOT, "assets", "audio", "amb")
SPOTS = os.path.join(ROOT, "assets", "audio", "spots")
LOOP = 32.0
N = int(LOOP * SR)


def st_noise(r, lo=None, hi=None, tilt=0.0, k=2.0):
    """Independent noise per channel (wide, natural)."""
    return np.stack([noise(N, r, lo, hi, tilt, k), noise(N, r, lo, hi, tilt, k)], axis=1)


def scatter(r, buf, maker, count, gain=(0.3, 1.0), pan=(-0.9, 0.9), far=None):
    for _ in range(count):
        ev = maker(r)
        g = r.uniform(*gain)
        if far is not None and r.random() < far:
            ev = filt(ev, lambda f: band(f, None, 2500)) * 0.5
        place(buf, ev, r.integers(0, N), g, r.uniform(*pan))


def verb(buf, r, sec=1.2, wet=0.25, hi=5000):
    ir = room_ir(sec, r, hi)
    out = buf.copy()
    for c in range(2):
        out[:, c] += wet * conv(buf[:, c], np.roll(ir, c * 37))
    return out


# ------------------------------------------------------------------ layer recipes
def wind_soft(r):
    g = gusts(N, r, (1, 6), 0.75)
    x = st_noise(r, 60, 700, -1.5) * g[:, None] * 0.8
    x += st_noise(r, 500, 2200, -1) * (g ** 2)[:, None] * 0.25
    return x


def wind_high(r):
    """Hilltop wind: stronger gusts and a faint whistle over the grass."""
    g = gusts(N, r, (1, 8), 0.85)
    x = st_noise(r, 50, 900, -1.5) * g[:, None]
    wh = np.stack([filt(noise(N, r), lambda f: peak(f, 1150, 18) + 0.6 * peak(f, 1700, 22)) for _ in range(2)], axis=1)
    x += wh * (g ** 3)[:, None] * 0.35
    x += st_noise(r, 2500, 9000) * (g ** 2.5)[:, None] * 0.18
    return x


def wind_trees(r):
    """Wind in a canopy: low roar plus leaf hiss that rises with each gust."""
    g = gusts(N, r, (1, 7), 0.8)
    x = st_noise(r, 40, 500, -2) * g[:, None] * 0.9
    leaf = st_noise(r, 1800, 9000) * (g ** 2.2)[:, None]
    flutter = 0.6 + 0.4 * np.abs(noise(N, r, 3, 14))
    x += leaf * flutter[:, None] * 0.45
    return x


def birds_park(r):
    x = np.zeros((N, 2))
    scatter(r, x, V.sparrow, 26, (0.2, 0.7), far=0.4)
    scatter(r, x, V.warbler, 9, (0.2, 0.6), far=0.5)
    scatter(r, x, V.whistler, 10, (0.15, 0.5), far=0.5)
    return verb(x, r, 0.8, 0.12)


def birds_forest(r):
    x = np.zeros((N, 2))
    scatter(r, x, V.whistler, 12, (0.15, 0.55), far=0.6)
    scatter(r, x, V.cuckoo, 3, (0.2, 0.4), far=0.7)
    scatter(r, x, V.warbler, 6, (0.1, 0.4), far=0.7)
    scatter(r, x, V.sparrow, 8, (0.1, 0.35), far=0.7)
    return verb(x, r, 2.2, 0.35, 4000)


def birds_town(r):
    x = np.zeros((N, 2))
    scatter(r, x, V.sparrow, 18, (0.15, 0.5), far=0.6)
    scatter(r, x, V.dove, 5, (0.2, 0.45), far=0.3)
    return verb(x, r, 0.6, 0.1)


def crickets(r):
    """Several crickets on their own fixed rhythm (rates divide the loop, so it stays seamless)."""
    x = np.zeros((N, 2))
    for _ in range(7):
        fc = r.uniform(3900, 5200)
        per = LOOP / r.integers(40, 80)       # chirp period that tiles the loop exactly
        ev = V.cricket_chirp(r, fc, r.integers(2, 5))
        g = r.uniform(0.12, 0.45)
        pan = r.uniform(-1, 1)
        ph = r.uniform(0, per)
        k = 0
        while k * per < LOOP:
            place(x, ev, (ph + k * per) * SR, g * r.uniform(0.85, 1.0), pan)
            k += 1
    # a soft field of distant insects
    x += st_noise(r, 3500, 6500, k=3) * (0.04 * (1 + 0.3 * lfo(N, 64)))[:, None]
    return x


def frogs(r):
    x = np.zeros((N, 2))
    for _ in range(4):
        per = LOOP / r.integers(10, 24)
        ev = V.frog(r)
        g, pan, ph = r.uniform(0.2, 0.6), r.uniform(-0.9, 0.9), r.uniform(0, per)
        k = 0
        while k * per < LOOP:
            if r.random() < 0.8:
                place(x, ev, (ph + k * per) * SR, g * r.uniform(0.7, 1), pan)
            k += 1
    return verb(x, r, 0.9, 0.2)


def cicadas(r):
    """Tonggeret: buzzing swells high in the trees on hot afternoons."""
    x = np.zeros((N, 2))
    for _ in range(3):
        d = r.uniform(6, 11)
        n = int(d * SR)
        t = np.arange(n) / SR
        sw = np.minimum(1, t / (d * 0.35)) ** 2 * np.minimum(1, (d - t) / (d * 0.25))
        buzz = noise(n, r, 4200, 7500, k=3) * (0.55 + 0.45 * np.sin(TAU * r.uniform(140, 190) * t))
        place(x, buzz * sw, r.integers(0, N), r.uniform(0.15, 0.3), r.uniform(-0.8, 0.8))
    return x


def _voice(r, n):
    """One far-off talker: buzz through drifting vowel formants, chopped into syllables."""
    t = np.arange(n) / SR
    f0 = r.uniform(110, 240) * (1 + 0.06 * noise(n, r, 0.5, 3))
    src = np.zeros(n)
    ph = TAU * np.cumsum(f0) / SR
    for k in range(1, 18):
        src += np.sin(ph * k) / k
    vowels = [(r.uniform(300, 800), r.uniform(900, 2200)) for _ in range(3)]
    vs = [filt(src, lambda f, a=a, b=b: peak(f, a, 4) + 0.7 * peak(f, b, 6)) for a, b in vowels]
    sel = np.abs(noise(n, r, 2, 6))
    mix = vs[0] * np.clip(1 - sel, 0, 1) + vs[1] * np.clip(sel, 0, 1) + vs[2] * 0.3
    syl = np.maximum(0, noise(n, r, 2.5, 7)) ** 1.2
    talk = (np.sin(TAU * r.integers(1, 5) * t / LOOP + r.uniform(0, TAU)) > -0.2)    # pauses
    return mix * syl * talk


def murmur(r, voices=14, hi=2400, room=1.4, wet=0.5):
    x = np.zeros((N, 2))
    for _ in range(voices):
        v = _voice(r, N)
        x += np.stack([v, v], axis=1) * np.array([1 + r.uniform(-0.6, 0.6), 1 + r.uniform(-0.6, 0.6)]) * r.uniform(0.3, 1.0)
    x = np.stack([filt(x[:, c], lambda f: band(f, 150, hi)) for c in range(2)], axis=1)
    return verb(x, r, room, wet, hi)


def city_crowd(r):
    """Plaza: far crowd, footsteps on stone, a soft city hum underneath."""
    x = murmur(r, 16, 2000, 1.8, 0.6)
    x /= np.sqrt(np.mean(x ** 2)) + 1e-9
    x += st_noise(r, 40, 300, -2) * 0.25
    steps = np.zeros((N, 2))
    for _ in range(140):
        k = 400
        e = noise(k, r, 800, 5000) * np.exp(-np.arange(k) / (SR * 0.004))
        place(steps, e, r.integers(0, N), r.uniform(0.02, 0.08), r.uniform(-1, 1))
    return x + steps


def traffic(r, cars=11, near=0.6):
    """Cars passing at different distances, left to right and back."""
    x = np.zeros((N, 2))
    x += st_noise(r, 30, 400, -2) * 0.4
    for _ in range(cars):
        d = r.uniform(3.0, 6.5)
        n = int(d * SR)
        t = np.arange(n) / SR
        e = np.exp(-((t - d / 2) / (d / 5)) ** 2)
        tire = noise(n, r, 150, 2500, -1) * e
        f0 = r.uniform(32, 55) * (1 + 0.06 * np.tanh((d / 2 - t) * 2))     # doppler
        eng = V.tone(f0, (1, 0.6, 0.4, 0.3, 0.2)) * e * 0.5
        g = r.uniform(0.25, 1.0) * near
        v = tire + eng
        if g < 0.3:
            v = filt(v, lambda f: band(f, None, 900))
        p0 = r.integers(0, N)
        dirn = 1 if r.random() < 0.5 else -1
        pan = np.clip(dirn * (t - d / 2) / (d / 3), -1, 1)
        a = (pan + 1) * np.pi / 4
        idx = (np.arange(n) + p0) % N
        np.add.at(x, idx, np.stack([v * g * np.cos(a), v * g * np.sin(a)], axis=1))
    return x


def river(r):
    """Babbling stream: bubbles over a band of flowing noise."""
    x = st_noise(r, 200, 3500, -1) * (0.5 * gusts(N, r, (2, 9), 0.3))[:, None]
    for _ in range(int(LOOP * 90)):
        b = V.bubble(r, r.uniform(350, 2600))
        place(x, b, r.integers(0, N), r.uniform(0.02, 0.12), r.uniform(-1, 1))
    return x


def waves_pier(r):
    """Sea against the pier posts: slow swells, slaps on wood, foam hiss."""
    x = st_noise(r, 40, 500, -2) * 0.3
    per = LOOP / 5
    for k in range(5):
        t0 = k * per + r.uniform(-0.5, 0.5)
        d = r.uniform(3.5, 5)
        n = int(d * SR)
        t = np.arange(n) / SR
        e = np.sin(np.pi * t / d) ** 2
        wash = noise(n, r, 200, 6000, -0.8) * e * 0.7
        place(x, wash, t0 * SR, 1.0, r.uniform(-0.5, 0.5))
        slap = V.splash(r, 0.4) * 0.6
        m = len(slap)
        slap += filt(r.standard_normal(m), lambda f: peak(f, 120, 2)) * np.exp(-np.arange(m) / (SR * 0.04)) * 0.5
        place(x, slap, (t0 + d * 0.45) * SR, 0.8, r.uniform(-0.7, 0.7))
    for _ in range(int(LOOP * 25)):
        place(x, V.bubble(r, r.uniform(500, 2000)), r.integers(0, N), r.uniform(0.02, 0.08), r.uniform(-1, 1))
    return x


def lake(r):
    """Still lake: tiny laps at the shore and the odd plink."""
    x = st_noise(r, 80, 1500, -1.5) * (0.25 * gusts(N, r, (2, 8), 0.6))[:, None]
    for _ in range(int(LOOP * 20)):
        place(x, V.bubble(r, r.uniform(400, 1500), rise=1), r.integers(0, N), r.uniform(0.03, 0.12), r.uniform(-1, 1))
    for _ in range(10):
        lap = V.splash(r, 0.7) * 0.3
        place(x, filt(lap, lambda f: band(f, None, 2500)), r.integers(0, N), 1, r.uniform(-0.6, 0.6))
    return x


def room_tone(r, hum=0.0):
    x = st_noise(r, 30, 400, -2) * 0.35
    if hum:
        h = V.tone(np.full(N, qfreq(100.0, N)), (1, 0.3, 0.15))
        x += stereo(h * hum)
    return x


def clock_room(r):
    """Bedroom / old house: low room tone, a wall clock ticking."""
    x = room_tone(r) * 0.8
    for k in range(int(LOOP)):
        n = 600
        tick = filt(noise(n, r, 1500, 7000), lambda f: peak(f, 2800 if k % 2 else 2300, 4)) * np.exp(-np.arange(n) / (SR * 0.003))
        place(x, tick, k * SR, 0.18, -0.35)
    return verb(x, r, 0.4, 0.2)


def birds_through_window(r):
    x = birds_town(r)
    return np.stack([filt(x[:, c], lambda f: band(f, 300, 2500)) for c in range(2)], axis=1) * 0.6


def cafe(r):
    x = murmur(r, 10, 3200, 0.7, 0.35) * 1.2
    x += room_tone(r, 0.05)
    for _ in range(14):
        place(x, V.cup_clink(r), r.integers(0, N), r.uniform(0.08, 0.25), r.uniform(-0.8, 0.8))
    return verb(x, r, 0.6, 0.15)


def kitchen(r):
    x = room_tone(r, 0.0) * 0.7
    fridge = V.tone(np.full(N, qfreq(60.0, N)), (0.3, 1, 0.5, 0.25)) * (0.05 * (1 + 0.1 * lfo(N, 3)))
    x += stereo(fridge, 0.3)
    for _ in range(int(LOOP * 18)):        # a pot simmering on the stove
        place(x, V.bubble(r, r.uniform(200, 700), 0.03), r.integers(0, N), r.uniform(0.02, 0.07), r.uniform(-0.2, 0.5))
    return verb(x, r, 0.5, 0.2)


def library(r):
    x = room_tone(r, 0.03) * 0.9
    x += st_noise(r, 100, 1200, -1) * 0.04
    for _ in range(4):
        n = int(1.2 * SR)
        page = noise(n, r, 1500, 8000) * np.exp(-((np.arange(n) / SR - 0.3) / 0.15) ** 2)
        place(x, page, r.integers(0, N), 0.05, r.uniform(-0.8, 0.8))
    return verb(x, r, 1.6, 0.35)


def arcade(r):
    x = room_tone(r, 0.12) * 0.8
    x += murmur(r, 5, 2600, 0.6, 0.25) * 0.5
    for _ in range(30):
        place(x, V.arcade_bleep(r), r.integers(0, N), r.uniform(0.04, 0.12), r.uniform(-1, 1))
    bass = np.zeros(N)
    beat = LOOP / 64
    for k in range(64):
        n = int(0.12 * SR)
        tt = np.arange(n) / SR
        bass_n = np.sin(TAU * 55 * tt) * np.exp(-tt / 0.05)
        idx = (np.arange(n) + int(k * beat * SR)) % N
        bass[idx] += bass_n * (0.06 if k % 2 == 0 else 0.0)
    x += stereo(filt(bass, lambda f: band(f, None, 200)))
    return x


def cave(r):
    """Crystal cave: deep breathing drone, resonant air, drips echoing."""
    g = gusts(N, r, (1, 4), 0.6)
    x = np.stack([filt(noise(N, r, tilt=-2), lambda f: peak(f, 70, 3) + 0.7 * peak(f, 140, 5) + 0.3 * peak(f, 310, 8)) for _ in range(2)], axis=1)
    x *= g[:, None] * 0.8
    dr = np.zeros((N, 2))
    for _ in range(36):
        place(dr, V.drip(r), r.integers(0, N), r.uniform(0.1, 0.5), r.uniform(-1, 1))
    return x + verb(dr, r, 3.5, 0.9, 6000)


def _rain(r, density, lo, hi, drops, drop_band, bed=0.5):
    x = st_noise(r, lo, hi, -0.6) * bed
    for _ in range(int(LOOP * drops)):
        n = 120
        e = noise(n, r, *drop_band) * np.exp(-np.arange(n) / (SR * 0.0015))
        place(x, e, r.integers(0, N), r.uniform(0.05, 0.3) * density, r.uniform(-1, 1))
    return x


def rain_open(r):
    return _rain(r, 1.0, 300, 9000, 220, (2000, 9000))


def rain_leaves(r):
    """Rain on foliage: fuller patter on leaves, drips falling from the canopy."""
    x = _rain(r, 1.2, 250, 8000, 360, (1200, 7000), 0.45)
    for _ in range(80):
        place(x, V.drip(r, r.uniform(700, 1400)), r.integers(0, N), r.uniform(0.05, 0.15), r.uniform(-1, 1))
    return x


def rain_water(r):
    """Rain onto a river/sea/lake surface: plinks and a soft hiss."""
    x = _rain(r, 0.7, 400, 8000, 120, (2500, 9000), 0.4)
    for _ in range(int(LOOP * 120)):
        place(x, V.bubble(r, r.uniform(900, 3200), 0.012), r.integers(0, N), r.uniform(0.03, 0.12), r.uniform(-1, 1))
    return x


def rain_roof(r):
    """Rain on a roof heard from inside, gutter trickling."""
    x = _rain(r, 0.8, 80, 2500, 260, (300, 2200), 0.6)
    tr = np.zeros((N, 2))
    for _ in range(int(LOOP * 40)):
        place(tr, V.bubble(r, r.uniform(300, 1100), 0.02), r.integers(0, N), r.uniform(0.03, 0.1), 0.6)
    x += tr
    return np.stack([filt(x[:, c], lambda f: band(f, 60, 3500)) for c in range(2)], axis=1)


def rain_city(r):
    x = _rain(r, 1.0, 300, 9000, 200, (1800, 9000))
    for _ in range(int(LOOP * 35)):
        place(x, V.bubble(r, r.uniform(400, 1200), 0.02), r.integers(0, N), r.uniform(0.02, 0.08), -0.5)
    return x


def _pad(r, chord, bright=0.3, shimmer=0.0, motion=1):
    x = np.zeros((N, 2))
    for i, hz in enumerate(chord):
        for d, side in ((-0.6, 0), (0.6, 1)):
            f = qfreq(hz * (1 + d / 1200), N)
            amp = 1 / (i + 1) ** 0.4
            e = 0.6 + 0.4 * lfo(N, motion * (i % 3 + 1), r.uniform(0, TAU))
            v = V.tone(np.full(N, f), (1, bright, bright ** 2, bright ** 3)) * e * amp
            x[:, side] += v
    x *= 0.12
    if shimmer:
        tw = np.zeros((N, 2))
        for _ in range(int(shimmer)):
            place(tw, V.twinkle(r), r.integers(0, N), r.uniform(0.04, 0.12), r.uniform(-1, 1))
        x += verb(tw, r, 2.5, 0.7, 9000)
    return verb(x, r, 3.0, 0.5, 4000)


C, D, E, F, G, A, B = 261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88


def dream_bloom(r):        # memory garden: warm major add9
    return _pad(r, [F / 2, C, A, E * 2, G * 2], 0.25, 14)


def dream_lantern(r):      # lantern field: amber, slow
    return _pad(r, [D / 2, A / 2, F, A, E * 2], 0.2, 10)


def dream_stars(r):        # star path / starfall: open fifths, sparkly
    return _pad(r, [E / 2, B / 2, E, B, G * 2 * 1.0595], 0.35, 22, 2)


def dream_eternal(r):      # eternal garden: bright, hopeful
    return _pad(r, [G / 2, D, B, D * 2, A * 2], 0.3, 16)


def dream_hall(r):         # hall of tomorrow: big airy space
    x = _pad(r, [C / 2, G / 2, D, E, B], 0.2, 8)
    return x + wind_soft(r) * 0.25


def dream_fade(r):         # arsip memudar: minor, thin, whispers drifting past
    x = _pad(r, [A / 2, E, C * 2, B], 0.15, 4) * 0.8
    w = np.zeros((N, 2))
    for _ in range(9):
        place(w, V.whisper(r), r.integers(0, N), r.uniform(0.05, 0.15), r.uniform(-1, 1))
    return x + verb(w, r, 2.5, 0.8)


def gears(r):
    """Clockwork station: several clocks ticking at different speeds plus a soft gear whirr."""
    x = np.zeros((N, 2))
    for per, fc, pan, g in ((1.0, 2600, -0.6, 0.2), (0.5, 3400, 0.5, 0.12), (2.0, 1500, 0.0, 0.25), (4 / 3, 2100, 0.8, 0.12), (0.25, 4200, -0.2, 0.05)):
        k = 0
        while k * per < LOOP:
            n = 500
            tick = filt(noise(n, r), lambda f: peak(f, fc, 6)) * np.exp(-np.arange(n) / (SR * 0.003))
            place(x, tick, k * per * SR, g, pan)
            k += 1
    wh = np.stack([filt(noise(N, r), lambda f: peak(f, 420, 10) + peak(f, 640, 12)) for _ in range(2)], axis=1)
    x += wh * (0.05 * (0.7 + 0.3 * lfo(N, 4)))[:, None]
    return verb(x, r, 1.8, 0.4)


def fire(r):
    x = st_noise(r, 60, 900, -1.5) * (0.35 * gusts(N, r, (2, 10), 0.4))[:, None]
    for _ in range(int(LOOP * 14)):
        n = int(r.uniform(0.002, 0.012) * SR)
        e = noise(n, r, 1000, 9000) * np.exp(-np.arange(n) / (n / 3))
        place(x, e, r.integers(0, N), r.uniform(0.1, 0.6) ** 2, r.uniform(-0.4, 0.4))
    return x


def fountain(r):
    x = st_noise(r, 400, 9000, -0.6) * 0.5
    for _ in range(int(LOOP * 160)):
        place(x, V.bubble(r, r.uniform(500, 3000)), r.integers(0, N), r.uniform(0.02, 0.1), r.uniform(-1, 1))
    return x


def waterfall(r):
    x = st_noise(r, 40, 7000, -1.0) * (0.8 + 0.2 * gusts(N, r, (3, 12), 1.0))[:, None]
    x += st_noise(r, 30, 200, -2) * 0.5
    return x


LAYERS = {
    # name: (recipe, target loudness dBFS rms, vorbis quality)
    "wind_soft": (wind_soft, -27, 0), "wind_high": (wind_high, -24, 0), "wind_trees": (wind_trees, -25, 0),
    "birds_park": (birds_park, -27, 1), "birds_forest": (birds_forest, -28, 1), "birds_town": (birds_town, -30, 1),
    "crickets": (crickets, -29, 1), "frogs": (frogs, -29, 0), "cicadas": (cicadas, -31, 0),
    "city_crowd": (city_crowd, -26, 0), "traffic": (traffic, -25, 0),
    "river": (river, -25, 0), "waves_pier": (waves_pier, -24, 0), "lake": (lake, -28, 0),
    "room_tone": (room_tone, -36, -1), "clock_room": (clock_room, -34, 0), "birds_window": (birds_through_window, -34, 0),
    "cafe": (cafe, -26, 0), "kitchen": (kitchen, -30, 0), "library": (library, -34, 0), "arcade": (arcade, -26, 0),
    "cave": (cave, -26, 0),
    "rain_open": (rain_open, -24, 0), "rain_leaves": (rain_leaves, -24, 0), "rain_water": (rain_water, -25, 0),
    "rain_roof": (rain_roof, -27, 0), "rain_city": (rain_city, -24, 0),
    "dream_bloom": (dream_bloom, -27, 0), "dream_lantern": (dream_lantern, -27, 0), "dream_stars": (dream_stars, -27, 0),
    "dream_eternal": (dream_eternal, -27, 0), "dream_hall": (dream_hall, -27, 0), "dream_fade": (dream_fade, -28, 0),
    "gears": (gears, -28, 0),
    # positional emitters
    "fire": (fire, -22, 0), "fountain": (fountain, -21, 0), "waterfall": (waterfall, -20, 0),
}

SPOT_MAKERS = {
    "gull": V.gull, "buoy_bell": V.buoy_bell, "creak": V.creak, "ship_horn": V.ship_horn, "fish_splash": V.fish_splash,
    "dove": V.dove, "bike_bell": V.bike_bell, "car_horn": V.car_horn, "bus_hiss": V.bus_hiss,
    "crossing_beep": V.crossing_beep, "train_far": V.train, "dog_far": V.dog_far, "wind_chime": V.wind_chime,
    "tokek": V.tokek, "owl": V.owl, "woodpecker": V.woodpecker, "cuckoo": V.cuckoo, "whistler": V.whistler,
    "frog": V.frog, "drip": V.drip, "crystal": V.crystal, "cup_clink": V.cup_clink, "espresso": V.espresso,
    "arcade_bleep": V.arcade_bleep, "thunder": V.thunder, "twinkle": V.twinkle, "whisper": V.whisper,
    "clock_chime": V.clock_chime, "kettle": V.kettle,
}
SPOT_VARIANTS = 3
MONO = {"room_tone", "kitchen"}


def build_layers(only=None):
    for i, (name, (fn, rms, q)) in enumerate(sorted(LAYERS.items())):
        if only and name not in only:
            continue
        x = fn(rng(1000 + i * 17))
        x = norm(x, -1.0, rms)
        if name in MONO:
            x = x.mean(axis=1)
        write_ogg(os.path.join(AMB, name + ".ogg"), x, q)
        print("layer", name, os.path.getsize(os.path.join(AMB, name + ".ogg")) // 1024, "KB")


def build_spots(only=None):
    for i, (name, fn) in enumerate(sorted(SPOT_MAKERS.items())):
        if only and name not in only:
            continue
        for v in range(SPOT_VARIANTS):
            r = rng(5000 + i * 31 + v)
            x = fn(r)
            k = min(len(x) // 4, int(0.012 * SR))
            x = x * np.minimum(1, np.minimum(np.arange(len(x)), len(x) - 1 - np.arange(len(x))) / k)
            x = np.concatenate([np.zeros(80), x, np.zeros(int(0.05 * SR))])
            x = norm(x, -3.0)
            write_ogg(os.path.join(SPOTS, "%s_%d.ogg" % (name, v + 1)), x, 1)
        print("spot", name)


# ------------------------------------------------------------------ area profiles
# when: day (05-18), night (19-04), dawn (05-09), dusk (16-19), dry, rain, wind (berangin)
def L(id, vol, when=""):
    return {"id": id, "vol": vol, "when": when}


def S(id, every, vol, when="", far=False):
    return {"id": id, "every": every, "vol": vol, "when": when, "far": far}


OUT_RAIN = [L("rain_open", 0.9, "rain")]
NIGHT_BUGS = [L("crickets", 0.7, "night,dry")]
THUNDER = [S("thunder", [25, 60], 0.55, "rain", True)]

AREAS = {
    "plaza": {"reverb": "plaza", "flow": {"id": "river", "r": 260, "vol": 0.45}, "layers": [L("city_crowd", 0.75, "day,dry"), L("city_crowd", 0.3, "night,dry"), L("birds_town", 0.6, "day,dry"),
              L("wind_soft", 0.35), L("wind_soft", 0.5, "wind"), L("rain_city", 0.9, "rain")] + NIGHT_BUGS,
              "spots": [S("dove", [8, 18], 0.5, "day,dry"), S("bike_bell", [14, 30], 0.45, "day,dry", True), S("wind_chime", [20, 40], 0.35, "dry"),
                        S("dog_far", [30, 70], 0.3, "night", True)] + THUNDER},
    "jalan_kota": {"reverb": "street", "layers": [L("traffic", 0.85, "day"), L("traffic", 0.4, "night"), L("city_crowd", 0.45, "day,dry"),
                   L("birds_town", 0.35, "dawn,dry"), L("wind_soft", 0.3), L("rain_city", 0.95, "rain")] + NIGHT_BUGS,
                   "spots": [S("car_horn", [12, 28], 0.4, "", True), S("bus_hiss", [18, 40], 0.45, "day"), S("crossing_beep", [25, 50], 0.35, "day"),
                             S("train_far", [45, 90], 0.5, "", True), S("bike_bell", [20, 40], 0.4, "day,dry")] + THUNDER},
    "perumahan": {"reverb": "street", "layers": [L("birds_town", 0.75, "day,dry"), L("cicadas", 0.6, "day,dry"), L("wind_trees", 0.4), L("wind_trees", 0.7, "wind"),
                  L("traffic", 0.15, "day"), L("rain_open", 0.85, "rain"), L("crickets", 0.8, "night,dry")],
                  "spots": [S("dog_far", [25, 55], 0.4, "", True), S("wind_chime", [16, 35], 0.5, "dry"), S("tokek", [40, 80], 0.6, "night"),
                            S("dove", [15, 30], 0.4, "dawn,dry"), S("bike_bell", [30, 60], 0.35, "day,dry", True)] + THUNDER},
    "taman_kota": {"reverb": "open", "lake": {"id": "lake", "r": 300, "vol": 0.7}, "layers": [L("birds_park", 0.85, "day,dry"), L("wind_trees", 0.4), L("wind_trees", 0.7, "wind"), L("cicadas", 0.35, "day,dry"),
                   L("rain_leaves", 0.9, "rain"), L("crickets", 0.75, "night,dry"), L("frogs", 0.45, "night")],
                   "spots": [S("whistler", [8, 18], 0.5, "day,dry"), S("dove", [15, 30], 0.4, "day,dry"), S("owl", [40, 80], 0.45, "night,dry", True),
                             S("wind_chime", [30, 60], 0.3, "dry")] + THUNDER},
    "riverside": {"reverb": "open", "layers": [L("wind_soft", 0.45), L("wind_soft", 0.7, "wind"), L("birds_park", 0.45, "day,dry"), L("rain_water", 0.9, "rain"),
                  L("crickets", 0.6, "night,dry"), L("frogs", 0.75, "night")],
                  "flow": {"id": "river", "r": 520, "vol": 0.95}, "lake": {"id": "lake", "r": 360, "vol": 0.6},
                  "spots": [S("fish_splash", [18, 40], 0.45, "dry"), S("frog", [10, 25], 0.5, "dusk"), S("creak", [25, 50], 0.35, "")] + THUNDER},
    "dermaga": {"reverb": "harbor", "layers": [L("wind_soft", 0.55), L("wind_high", 0.5, "wind"), L("rain_water", 0.95, "rain"), L("crickets", 0.4, "night,dry")],
                "flow": {"id": "waves_pier", "r": 700, "vol": 1.0},
                "spots": [S("gull", [7, 16], 0.6, "day,dry"), S("creak", [6, 14], 0.45, ""), S("buoy_bell", [18, 35], 0.4, "", True),
                          S("ship_horn", [50, 100], 0.55, "", True), S("fish_splash", [25, 50], 0.35, "dry")] + THUNDER},
    "hutan_bisik": {"reverb": "forest", "layers": [L("wind_trees", 0.7), L("wind_trees", 0.95, "wind"), L("birds_forest", 0.85, "day,dry"),
                    L("rain_leaves", 1.0, "rain"), L("crickets", 0.6, "night,dry"), L("frogs", 0.35, "night")],
                    "flow": {"id": "river", "r": 420, "vol": 0.8},
                    "spots": [S("woodpecker", [18, 40], 0.45, "day,dry", True), S("cuckoo", [25, 55], 0.45, "day,dry", True), S("owl", [18, 40], 0.55, "night,dry"),
                              S("whistler", [10, 22], 0.4, "dawn,dry", True)] + THUNDER},
    "bukit_bintang": {"reverb": "open", "layers": [L("wind_high", 0.7), L("wind_high", 1.0, "wind"), L("birds_park", 0.3, "day,dry"), L("rain_open", 0.9, "rain"),
                      L("crickets", 0.45, "night,dry")],
                      "spots": [S("wind_chime", [20, 40], 0.3, "dry"), S("owl", [45, 90], 0.35, "night,dry", True), S("whistler", [20, 40], 0.3, "day,dry", True)] + THUNDER},
    # interiors
    "arland_room": {"reverb": "room", "layers": [L("clock_room", 0.7), L("birds_window", 0.7, "day,dry"), L("crickets", 0.2, "night,dry"), L("rain_roof", 0.7, "rain")],
                    "spots": [S("dog_far", [60, 120], 0.15, "day,dry", True)] + [S("thunder", [30, 70], 0.3, "rain", True)]},
    "sofia_room": {"reverb": "room", "layers": [L("clock_room", 0.6), L("birds_window", 0.75, "day,dry"), L("crickets", 0.2, "night,dry"), L("rain_roof", 0.7, "rain")],
                   "spots": [S("wind_chime", [40, 90], 0.15, "dry", True)] + [S("thunder", [30, 70], 0.3, "rain", True)]},
    "rumah_sari": {"reverb": "room", "layers": [L("clock_room", 1.0), L("birds_window", 0.5, "day,dry"), L("crickets", 0.25, "night,dry"), L("rain_roof", 0.7, "rain")],
                   "spots": [S("clock_chime", [70, 140], 0.35), S("kettle", [80, 160], 0.2, "day"), S("tokek", [50, 100], 0.25, "night", True)]},
    "cafe": {"reverb": "room", "layers": [L("cafe", 0.9), L("rain_roof", 0.5, "rain")],
             "spots": [S("espresso", [25, 50], 0.4), S("cup_clink", [5, 12], 0.4), S("wind_chime", [40, 80], 0.3)]},
    "dapur": {"reverb": "room", "layers": [L("kitchen", 0.9), L("birds_window", 0.4, "day,dry"), L("rain_roof", 0.6, "rain")],
              "spots": [S("cup_clink", [12, 25], 0.35), S("kettle", [50, 100], 0.3), S("espresso", [60, 120], 0.2)]},
    "galeri_komunitas": {"reverb": "hall", "layers": [L("room_tone", 1.0), L("city_crowd", 0.2), L("rain_roof", 0.6, "rain")],
                         "spots": [S("cup_clink", [25, 50], 0.25), S("wind_chime", [40, 80], 0.2)]},
    "toko_bunga": {"reverb": "room", "layers": [L("room_tone", 0.9), L("birds_window", 0.6, "day,dry"), L("rain_roof", 0.6, "rain")],
                   "spots": [S("wind_chime", [15, 35], 0.45)]},
    "arcade": {"reverb": "room", "layers": [L("arcade", 0.9), L("rain_roof", 0.3, "rain")], "spots": [S("arcade_bleep", [4, 10], 0.35)]},
    "perpustakaan": {"reverb": "hall", "layers": [L("library", 1.0), L("rain_roof", 0.5, "rain")], "spots": [S("clock_chime", [90, 180], 0.2)]},
    "ruang_arsip": {"reverb": "hall", "layers": [L("library", 0.8), L("dream_fade", 0.3)], "spots": [S("whisper", [30, 60], 0.2)]},
    "ruang_dua_surat": {"reverb": "hall", "layers": [L("library", 0.7), L("dream_bloom", 0.4)], "spots": [S("twinkle", [20, 40], 0.3)]},
    # memory / dream realms
    "memory_garden": {"reverb": "dream", "layers": [L("dream_bloom", 0.8), L("wind_soft", 0.3), L("birds_park", 0.25)], "spots": [S("twinkle", [10, 22], 0.35), S("wind_chime", [25, 50], 0.3)]},
    "lantern_field": {"reverb": "dream", "layers": [L("dream_lantern", 0.8), L("crickets", 0.5), L("wind_soft", 0.35)], "spots": [S("twinkle", [12, 25], 0.3), S("wind_chime", [20, 40], 0.3)]},
    "star_path": {"reverb": "dream", "layers": [L("dream_stars", 0.8), L("wind_high", 0.35)], "spots": [S("twinkle", [7, 15], 0.4)]},
    "starfall_village": {"reverb": "dream", "layers": [L("dream_stars", 0.6), L("crickets", 0.4), L("wind_soft", 0.4)], "spots": [S("wind_chime", [12, 25], 0.4), S("twinkle", [15, 30], 0.3), S("owl", [50, 100], 0.3, "", True)]},
    "eternal_garden": {"reverb": "dream", "lake": {"id": "lake", "r": 300, "vol": 0.5}, "layers": [L("dream_eternal", 0.8), L("birds_park", 0.4), L("wind_soft", 0.3)], "spots": [S("whistler", [12, 25], 0.35), S("twinkle", [15, 30], 0.3)]},
    "rain_garden": {"reverb": "dream", "layers": [L("rain_leaves", 0.8), L("dream_lantern", 0.45)], "spots": [S("wind_chime", [15, 30], 0.35), S("thunder", [50, 100], 0.3, "", True)]},
    "clockwork_station": {"reverb": "hall", "layers": [L("gears", 0.9), L("dream_stars", 0.3)], "spots": [S("clock_chime", [40, 80], 0.35), S("twinkle", [25, 50], 0.25)]},
    "moonlight_lake": {"reverb": "dream", "layers": [L("lake", 0.9), L("dream_lantern", 0.35), L("crickets", 0.5), L("frogs", 0.35)], "spots": [S("fish_splash", [20, 40], 0.35), S("owl", [40, 80], 0.3, "", True), S("twinkle", [25, 50], 0.25)]},
    "memory_bridge": {"reverb": "dream", "layers": [L("wind_high", 0.5), L("dream_stars", 0.55)], "spots": [S("wind_chime", [12, 25], 0.4), S("twinkle", [15, 30], 0.3)]},
    "hall_of_tomorrow": {"reverb": "cathedral", "layers": [L("dream_hall", 0.9)], "spots": [S("twinkle", [12, 25], 0.3), S("crystal", [25, 50], 0.3)]},
    "gua_kristal": {"reverb": "cave", "layers": [L("cave", 1.0)], "spots": [S("drip", [2, 6], 0.55), S("crystal", [8, 18], 0.4)]},
    "arsip_memudar": {"reverb": "cathedral", "layers": [L("dream_fade", 0.9), L("wind_soft", 0.3)], "spots": [S("whisper", [15, 30], 0.35), S("clock_chime", [60, 120], 0.2, "", True)]},
    "kenangan_gazebo": {"reverb": "dream", "layers": [L("rain_roof", 0.6), L("rain_leaves", 0.5), L("dream_bloom", 0.35)], "spots": [S("wind_chime", [15, 30], 0.35), S("thunder", [45, 90], 0.3, "", True)]},
}

# Positional loops attached to props wherever they appear (volume falls off with distance).
EMITTERS = {
    "hd_fountain_grand": {"id": "fountain", "r": 560, "vol": 1.0},
    "hd_fountain_tiered": {"id": "fountain", "r": 420, "vol": 0.8},
    "hd_waterfall": {"id": "waterfall", "r": 760, "vol": 1.0},
    "hd_campfire": {"id": "fire", "r": 320, "vol": 0.9},
}

# Reverb on the spot (one-shot) bus per kind of place: room_size, damping, wet, predelay ms.
REVERB = {
    "open": [0.25, 0.6, 0.06, 20], "street": [0.4, 0.5, 0.1, 30], "plaza": [0.5, 0.5, 0.13, 40], "harbor": [0.45, 0.4, 0.1, 50],
    "forest": [0.6, 0.6, 0.18, 30], "room": [0.25, 0.7, 0.12, 5], "hall": [0.6, 0.5, 0.2, 15], "dream": [0.75, 0.4, 0.28, 40],
    "cathedral": [0.9, 0.35, 0.35, 60], "cave": [0.92, 0.25, 0.42, 70],
}


def build_json():
    areas = json.load(open(os.path.join(ROOT, "assets", "data", "maps.json")))["areas"]
    missing = [a for a in areas if a not in AREAS]
    if missing:
        raise SystemExit("areas without a soundscape: %s" % missing)
    data = {"_doc": "Per-area soundscape (tools/audio/make_soundscape.py). layers loop from assets/audio/amb, spots are random one-shots "
                    "from assets/audio/spots (<id>_1..%d.ogg), emitters/flow/lake are positional loops. when: day,night,dawn,dusk,dry,rain,wind." % SPOT_VARIANTS,
            "spot_variants": SPOT_VARIANTS, "reverb": REVERB, "emitters": EMITTERS, "areas": AREAS}
    with open(os.path.join(ROOT, "assets", "audio", "area_sound.json"), "w") as f:
        json.dump(data, f, indent=1)
    print("area_sound.json:", len(AREAS), "areas")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = set(sys.argv[2:]) or None
    if what in ("all", "layers"):
        build_layers(only)
    if what in ("all", "spots"):
        build_spots(only)
    if what in ("all", "json"):
        build_json()
