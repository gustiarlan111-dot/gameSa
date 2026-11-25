"""HD forest landmarks for Hutan Bisik, drawn from scratch with the v6 kit rules
(2 texels per world unit, top-left light, coloured outlines). Bottom-centre = map foot point."""
import numpy as np
from kit import (Sprite, quant, bayer, sphere_shade, outline, noise, hexrgb, ramp, WOOD, STONE, METAL, LEAF,
                 LEAF_DARK, FLOWERS, WATER, BARK)
from landmarks import ground_shadow, vgrad, hgrad, darken, lighten, glow, GOLD, text_mask

ROCK = ramp('#262a33', '#363b46', '#484e5a', '#5c6370', '#737a86', '#8e959e', '#adb3b8')
MOSS = ramp('#1f3a26', '#2b4f2f', '#3a6637', '#4f7e40', '#679750')
CAVE_GLOW = ramp('#1c1640', '#2b2366', '#41389a', '#6a5fd0', '#a39cf0', '#e0dcff')
CANVAS = ramp('#5a3f2a', '#7a5838', '#9c754a', '#bf9864', '#d9b780', '#ecd3a0')
FLAME = ramp('#8a2a10', '#c2481a', '#ee7a26', '#ffb347', '#ffe08a', '#fff6d8')


def _rock_mass(sp, cx, cy, rx, ry, seed, R=ROCK, moss=0.35):
    """Lumpy boulder: several shaded ellipsoids with cracks and moss on top."""
    rng = np.random.default_rng(seed)
    dith = bayer(sp.h, sp.w)
    mine = np.zeros((sp.h, sp.w), bool)
    for k in range(7):
        x = cx + rng.uniform(-0.55, 0.55) * rx
        y = cy + rng.uniform(-0.35, 0.35) * ry
        r1, r2 = rx * rng.uniform(0.45, 0.7), ry * rng.uniform(0.5, 0.8)
        m = sp.ellipse(x, y, r1, r2)
        mine |= m
        sh = sphere_shade(sp, x - r1 * 0.2, y - r2 * 0.25, r1 * 1.1, r2 * 1.1)
        sp.put(m, quant(sh * 0.85 + (noise(sp.h, sp.w, 4, seed + k) - 0.5) * 0.25, R, dith))
        edge = m & ~sp.ellipse(x, y + 2, r1 - 2, r2 - 2) & (sp.yy > y)
        darken(sp, edge, 0.7)
    if moss:
        top = np.clip((cy - sp.yy) / ry, 0, 1)
        mm = mine & (noise(sp.h, sp.w, 14, seed + 9) * (0.5 + top) > 1.25 - moss * 0.8)
        sp.rgb[mm] = quant(0.45 + (noise(sp.h, sp.w, 7, seed) - 0.5) * 0.5 + top * 0.2, MOSS, bayer(sp.h, sp.w))[mm]


def cave_mouth(W=440, H=330):
    """Rock outcrop with a cave opening at the bottom centre, glowing crystals inside."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 8, W / 2 - 10, 18, 0.4)
    # back cliff
    _rock_mass(sp, cx, H * 0.48, W * 0.46, H * 0.42, 3, moss=0.45)
    _rock_mass(sp, cx - 120, H * 0.66, 100, 80, 5)
    _rock_mass(sp, cx + 125, H * 0.68, 95, 75, 7)
    # strata lines
    strata = (sp.a > 0.5) & ((np.sin(sp.yy * 0.16 + noise(H, W, 18, 2) * 4) > 0.96))
    darken(sp, strata, 0.78)
    # cave opening (dark gradient, lit crystals)
    mouth = sp.ellipse(cx, H - 10, 68, 112) & (sp.yy < H - 6)
    sp.put(mouth, quant(vgrad(sp, H - 120, H, 0.05, 0.35), CAVE_GLOW, dith))
    rim = sp.ellipse(cx, H - 10, 78, 122) & ~mouth & (sp.yy < H - 6)
    sp.put(rim, quant(hgrad(sp, cx - 78, cx + 78, 0.75, 0.25), ROCK, dith))
    for k, (x, h, w) in enumerate(((cx - 40, 40, 10), (cx - 26, 26, 8), (cx + 30, 46, 11), (cx + 46, 24, 8), (cx + 6, 20, 7))):
        cr = sp.poly([(x - w, H - 8), (x + w, H - 8), (x + w * 0.3, H - 8 - h), (x - w * 0.4, H - 8 - h * 0.8)])
        sp.put(cr, quant(hgrad(sp, x - w, x + w, 0.95, 0.5), CAVE_GLOW))
        glow(sp, x, H - 8 - h / 2, 40, hexrgb('#a39cf0'), 0.3)
    # hanging vines + ferns at the base
    rng = np.random.default_rng(4)
    for k in range(18):
        x = rng.uniform(cx - 90, cx + 90)
        y0 = H - 10 - np.sqrt(max(0, 1 - ((x - cx) / 80) ** 2)) * 118
        ln = rng.uniform(16, 60)
        for t in np.linspace(0, ln, int(ln / 3)):
            sp.put(sp.ellipse(x + np.sin(t * 0.2) * 2, y0 + t, 2.6, 2.2), LEAF[rng.integers(2, 6)])
    for x in list(np.linspace(20, cx - 90, 7)) + list(np.linspace(cx + 90, W - 20, 7)):
        for j in range(6):
            a = rng.uniform(np.pi * 1.05, np.pi * 1.95)
            sp.put(sp.ellipse(x + np.cos(a) * 12, H - 14 + np.sin(a) * 14, 6, 3), LEAF[rng.integers(2, 6)])
    outline(sp, ROCK[0] * 0.8, width=2)
    return sp


def waterfall(W=320, H=400):
    """Rock ledge with a waterfall falling into a foamy pool (the stream continues south)."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    _rock_mass(sp, cx - 100, 150, 90, 150, 11, moss=0.5)
    _rock_mass(sp, cx + 100, 150, 90, 150, 12, moss=0.5)
    _rock_mass(sp, cx, 70, 140, 70, 13, moss=0.55)
    # falling sheet
    fall = sp.rect(cx - 52, 60, 104, H - 140)
    streak = np.sin(sp.xx * 0.42 + noise(H, W, 16, 4) * 3) * 0.5 + 0.5
    sp.put(fall, quant(0.55 + streak * 0.35 + vgrad(sp, 60, H - 80, 0.1, -0.1), WATER, dith))
    lighten(sp, fall & (streak > 0.93), 0.55, (235, 248, 252))
    sp.put(sp.ellipse(cx, 62, 56, 10), WATER[6])
    # pool + foam
    pool = sp.ellipse(cx, H - 60, W / 2 - 30, 52)
    sp.put(pool, quant(0.35 + vgrad(sp, H - 112, H - 8, 0.2, -0.1) + (noise(H, W, 5, 6) - 0.5) * 0.15, WATER, dith))
    foam = sp.ellipse(cx, H - 82, 74, 18) | (pool & (noise(H, W, 8, 8) > 0.68) & (sp.yy < H - 56))
    sp.put(foam, hexrgb('#e6f6fa'))
    sp.put(sp.rect(cx - 56, H - 40, 112, 40), quant(0.45 + (noise(H, W, 4, 3) - 0.5) * 0.2, WATER, dith))
    for x in (cx - 120, cx + 118):
        _rock_mass(sp, x, H - 50, 46, 34, int(x), moss=0.3)
    glow(sp, cx, H - 90, 70, hexrgb('#cfeff6'), 0.2)
    outline(sp, ROCK[0] * 0.8, width=2)
    return sp


def tent(W=200, H=156):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 8, W / 2 - 6, 14, 0.4)
    body = sp.poly([(10, H - 12), (W - 10, H - 12), (cx + 18, 14), (cx - 18, 14)])
    sp.put(body, quant(hgrad(sp, 10, W - 10, 0.85, 0.35) + (((sp.xx - cx) % 26) < 2) * -0.15, CANVAS, dith))
    door = sp.poly([(cx - 34, H - 12), (cx + 34, H - 12), (cx, 34)])
    sp.put(door, quant(vgrad(sp, 34, H, 0.1, 0.3), ramp('#1e1712', '#2c2118', '#3c2d20', '#4f3b2a')))
    flap = sp.poly([(cx - 34, H - 12), (cx - 56, H - 12), (cx - 2, 36)])
    sp.put(flap, quant(hgrad(sp, cx - 56, cx, 0.95, 0.6), CANVAS))
    sp.put(sp.rect(cx - 2, 2, 4, 20), WOOD[2])
    sp.put(sp.poly([(cx + 2, 4), (cx + 26, 10), (cx + 2, 16)]), hexrgb('#e0627a'))
    for x in (12, W - 14):
        sp.put(sp.rect(x - 2, H - 20, 4, 12), WOOD[1])
    sp.put(sp.rect(10, H - 14, W - 20, 3), CANVAS[1])
    # lantern hanging at the door, bedroll peeking out
    sp.put(sp.rect(cx + 40, 66, 10, 14), hexrgb('#ffd776'))
    glow(sp, cx + 45, 73, 30, hexrgb('#ffd37a'), 0.35)
    sp.put(sp.rect(cx - 20, H - 26, 40, 10), hexrgb('#5b7fa8'))
    outline(sp, CANVAS[0] * 0.8, width=2)
    return sp


def campfire(W=84, H=80):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 10, 36, 10, 0.35)
    rng = np.random.default_rng(3)
    for k in range(10):
        a = k / 10 * 2 * np.pi
        x, y = cx + np.cos(a) * 30, H - 18 + np.sin(a) * 11
        sp.put(sp.ellipse(x, y, 7, 5), quant(sphere_shade(sp, x - 2, y - 2, 7, 5), ROCK, dith))
    for a, b in (((cx - 22, H - 14), (cx + 18, H - 26)), ((cx + 22, H - 14), (cx - 18, H - 26))):
        for t in np.linspace(0, 1, 30):
            sp.put(sp.ellipse(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 4.5, 4), BARK[3])
    sp.put(sp.ellipse(cx, H - 20, 12, 5), hexrgb('#ff9a3a'))
    flame = sp.poly([(cx - 14, H - 20), (cx + 14, H - 20), (cx + 8, H - 44), (cx + 2, H - 36), (cx, H - 62), (cx - 5, H - 40), (cx - 10, H - 48)])
    sp.put(flame, quant(vgrad(sp, H - 62, H - 18, 0.95, 0.35), FLAME))
    inner = sp.poly([(cx - 7, H - 20), (cx + 7, H - 20), (cx + 2, H - 40), (cx - 3, H - 34)])
    sp.put(inner, FLAME[5])
    glow(sp, cx, H - 32, 40, hexrgb('#ffb347'), 0.45)
    outline(sp, hexrgb('#2a1a10'), inner=False, width=1)
    return sp


def log_bench(W=136, H=54, seed=0):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 6, W / 2 - 4, 7, 0.32)
    log = sp.rect(10, 12, W - 22, 30) | sp.ellipse(10, 27, 8, 15)
    sp.put(log, quant(vgrad(sp, 12, 42, 0.85, 0.3) + (np.sin(sp.xx * 0.9 + seed) > 0.8) * -0.12, BARK, dith))
    sp.put(sp.rect(10, 12, W - 22, 6), quant(0.75 + (noise(H, W, 2, seed) - 0.5) * 0.3, WOOD))
    end = sp.ellipse(W - 12, 27, 9, 15)
    sp.put(end, hexrgb('#c9a06a'))
    for r in (6, 3):
        sp.put(sp.ellipse(W - 12, 27, r, r * 1.6) & ~sp.ellipse(W - 12, 27, r - 1, r * 1.6 - 1.5), hexrgb('#8a6038'))
    mm = log & (noise(H, W, 4, seed + 3) > 0.7) & (sp.yy < 24)
    sp.rgb[mm] = MOSS[3]
    for x in (26, W - 40):
        sp.put(sp.rect(x, 40, 8, H - 46), BARK[1])
    outline(sp, BARK[0], width=1)
    return sp


def stone_lantern(W=68, H=128, lit=True):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 28, 7, 0.35)
    def block(x0, y0, w, h):
        m = sp.rect(x0, y0, w, h)
        sp.put(m, quant(hgrad(sp, x0, x0 + w, 0.85, 0.3) + (noise(H, W, 3, int(y0)) - 0.5) * 0.15, STONE, dith))
        sp.put(sp.rect(x0, y0, w, 2), STONE[6])
    block(cx - 24, H - 18, 48, 14)
    block(cx - 8, 66, 16, H - 84)
    block(cx - 20, 58, 40, 10)
    block(cx - 16, 34, 32, 26)
    sp.put(sp.rect(cx - 9, 40, 18, 14), hexrgb('#ffd776') if lit else hexrgb('#2a2a30'))
    roof = sp.poly([(cx - 30, 36), (cx + 30, 36), (cx + 14, 18), (cx - 14, 18)])
    sp.put(roof, quant(hgrad(sp, cx - 30, cx + 30, 0.85, 0.3), STONE, dith))
    sp.put(sp.ellipse(cx, 14, 6, 6), STONE[4])
    mm = (sp.a > 0.5) & (noise(H, W, 5, 7) > 0.7)
    sp.rgb[mm] = sp.rgb[mm] * 0.5 + MOSS[3] * 0.5
    if lit:
        glow(sp, cx, 47, 34, hexrgb('#ffd37a'), 0.4)
    outline(sp, STONE[0], width=1)
    return sp


def carved_stone(symbol='moon', W=80, H=104):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 30, 7, 0.35)
    m = sp.poly([(cx - 30, H - 6), (cx + 30, H - 6), (cx + 26, 30), (cx + 10, 8), (cx - 14, 10), (cx - 28, 28)])
    sp.put(m, quant(hgrad(sp, cx - 30, cx + 30, 0.85, 0.3) + (noise(H, W, 4, 5) - 0.5) * 0.2, ROCK, dith))
    mm = m & (noise(H, W, 5, 9) > 0.66)
    sp.rgb[mm] = sp.rgb[mm] * 0.45 + MOSS[3] * 0.55
    c = hexrgb('#bfe6ff')
    if symbol == 'moon':
        sym = sp.ellipse(cx, 50, 16, 16) & ~sp.ellipse(cx + 7, 45, 14, 14)
    else:
        pts = []
        for k in range(10):
            r = 17 if k % 2 == 0 else 7
            a = -np.pi / 2 + k * np.pi / 5
            pts.append((cx + np.cos(a) * r, 52 + np.sin(a) * r))
        sym = sp.poly(pts)
    sp.put(sym, c)
    glow(sp, cx, 50, 30, hexrgb('#9fd8ff'), 0.35)
    outline(sp, ROCK[0], width=1)
    return sp


def chest(opened=False, W=72, H=64):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 30, 6, 0.35)
    body = sp.rect(8, 30, W - 16, H - 36)
    sp.put(body, quant(hgrad(sp, 8, W - 8, 0.85, 0.35) + (((sp.yy - 30) % 9) < 1.5) * -0.15, WOOD, dith))
    for x in (8, W - 16):
        sp.put(sp.rect(x, 30, 8, H - 36), quant(hgrad(sp, x, x + 8, 0.9, 0.4), GOLD))
    if opened:
        sp.put(sp.rect(10, 26, W - 20, 8), hexrgb('#2a1a10'))
        sp.put(sp.ellipse(cx, 30, 18, 5), GOLD[4])
        lid = sp.rect(8, 4, W - 16, 22)
        sp.put(lid, quant(vgrad(sp, 4, 26, 0.4, 0.75), WOOD, dith))
        sp.put(sp.rect(8, 22, W - 16, 4), GOLD[2])
        glow(sp, cx, 28, 30, hexrgb('#fff0a8'), 0.4)
    else:
        lid = sp.rect(8, 14, W - 16, 18) | sp.ellipse(cx, 16, W / 2 - 8, 8)
        sp.put(lid, quant(hgrad(sp, 8, W - 8, 0.95, 0.45), WOOD, dith))
        sp.put(sp.rect(8, 28, W - 16, 4), GOLD[2])
        sp.put(sp.rect(cx - 6, 28, 12, 12), GOLD[4])
        sp.put(sp.rect(cx - 2, 33, 4, 5), hexrgb('#2a1a10'))
    outline(sp, WOOD[0], width=1)
    return sp


def bridge_stream(broken=False, W=300, H=164):
    """Plank bridge across the stream (floor layer: walked over)."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    deck_y0, deck_y1 = 36, H - 36
    planks = sp.rect(10, deck_y0, W - 20, deck_y1 - deck_y0)
    v = 0.6 + (((sp.xx - 10) % 22) < 2) * -0.3 + (noise(H, W, 3, 5) - 0.5) * 0.15
    col = quant(v, WOOD, dith)
    if broken:
        hole = sp.rect(W / 2 - 46, deck_y0 - 4, 92, deck_y1 - deck_y0 + 8)
        jag = (np.sin(sp.yy * 0.5) * 6)
        hole = sp.rect(W / 2 - 46, deck_y0 - 4, 92, deck_y1 - deck_y0 + 8) & (np.abs(sp.xx - W / 2) < 40 + jag)
        planks = planks & ~hole
    sp.put(planks, col)
    for y in (deck_y0 - 8, deck_y1):                            # side beams + rope rails
        beam = sp.rect(4, y, W - 8, 10)
        if broken:
            beam = beam & ~(np.abs(sp.xx - W / 2) < 30)
        sp.put(beam, quant(vgrad(sp, y, y + 10, 0.8, 0.35), WOOD, dith))
    for x in (8, W - 18, W / 2 - 60, W / 2 + 50):
        for y in (deck_y0 - 12, deck_y1 - 2):
            sp.put(sp.rect(x, y, 10, 12), quant(hgrad(sp, x, x + 10, 0.85, 0.35), WOOD))
    if broken:
        rng = np.random.default_rng(2)
        for k in range(4):
            x = W / 2 + rng.uniform(-30, 30)
            sp.put(sp.poly([(x, deck_y1 + 4), (x + 18, deck_y1 + 14), (x + 14, deck_y1 + 20), (x - 4, deck_y1 + 10)]), WOOD[2])
    outline(sp, WOOD[0], width=1)
    return sp


def rock_ledge(W=232, H=100, seed=21):
    sp = Sprite(W, H)
    ground_shadow(sp, W / 2, H - 8, W / 2 - 6, 12, 0.38)
    _rock_mass(sp, W / 2, H * 0.55, W * 0.44, H * 0.38, seed, moss=0.5)
    rng = np.random.default_rng(seed)
    for k in range(10):
        x = rng.uniform(16, W - 16)
        for j in range(5):
            a = rng.uniform(np.pi * 1.1, np.pi * 1.9)
            sp.put(sp.ellipse(x + np.cos(a) * 9, H - 12 + np.sin(a) * 10, 5, 2.6), LEAF[rng.integers(2, 6)])
    outline(sp, ROCK[0] * 0.8, width=2)
    return sp


def light_shaft(W=260, H=520, seed=0):
    """Soft diagonal god-ray (mostly transparent); drawn above the canopy floor for atmosphere."""
    sp = Sprite(W, H)
    u = (sp.xx - sp.yy * 0.38 - 30) / 90
    band = np.clip(1 - np.abs(u - 0.6) * 1.6, 0, 1) * np.clip(sp.yy / 80, 0, 1) * np.clip((H - sp.yy) / 160, 0, 1)
    band *= 0.75 + 0.25 * noise(H, W, 24, seed)
    sp.rgb[:] = hexrgb('#fff3c8')
    sp.a = band * 0.22
    for k in range(20):
        rng = np.random.default_rng(seed + k)
        x, y = rng.uniform(40, W - 40), rng.uniform(60, H - 60)
        if band[int(y), int(x)] > 0.3:
            m = sp.ellipse(x, y, 1.4, 1.4)
            sp.rgb[m] = hexrgb('#fffbe6'); sp.a[m] = 0.8
    return sp
