"""Extra HD kit sprites for the Godot map remaster, in the same light/outline rules as
tools/artkit (top-left light, coloured outlines, shared ramps). Registers each sprite in
props.json as props/hd/<id>@2x.png.

Usage: python3 tools/godot/kit_extra.py [id ...] [--sheet out.png]
"""
import sys, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/artkit'))
import kit, nature, built, landmarks as lm, forest as fo, clockwork as cwk                                        # noqa: E402
from kit import (Sprite, quant, bayer, sphere_shade, outline, noise, hexrgb, ramp, BARK, STONE, LEAF,   # noqa: E402
                 LEAF_DARK, WOOD, METAL, FLOWERS)

A = ROOT / 'assets'
OUT = A / 'props' / 'hd'

DREAM = ramp('#2e2656', '#40357a', '#5a4b9c', '#7865bb', '#9a86d6', '#bdaaee', '#e0d4ff')
DREAM_BLUE = ramp('#1d2f5a', '#26437a', '#335d9a', '#467ab6', '#6198cc', '#86b6e0', '#b6d6f2')
LANTERN = ramp('#8a3c12', '#c2611e', '#ef8f3b', '#ffc27a', '#ffe3a8')
CRYSTAL = ramp('#2b2a6a', '#3f3f99', '#5a5cc4', '#7c84e0', '#a5b3f2', '#d3defc', '#ffffff')
CRYSTAL_CYAN = ramp('#164a5c', '#1f6a80', '#2b8ea3', '#45b3c4', '#76d2dc', '#b4ecef', '#ffffff')
TERRACOTTA = ramp('#5a2a1a', '#7a3a22', '#9c4e2c', '#bb6638', '#d2814c', '#e3a06c')
CLOTH_RED = ramp('#6a1f26', '#8f2c33', '#b33e44', '#d35a5c', '#ec8a86')


def glow(sp, cx, cy, r, col, strength=0.55):
    """Soft additive halo baked into the sprite (alpha fades out)."""
    d = np.sqrt((sp.xx - cx) ** 2 + (sp.yy - cy) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    c = np.asarray(col, np.float32)
    keep = sp.a > 0.5
    sp.rgb = np.where(keep[..., None], np.clip(sp.rgb + c * a[..., None] * 0.6, 0, 255),
                      np.where((a > sp.a)[..., None], c, sp.rgb))
    sp.a = np.where(keep, sp.a, np.maximum(sp.a, a))


def dream_tree(R=DREAM, seed=31, sparkle='#fff6c8'):
    sp = nature.broadleaf(R, seed)
    rng = np.random.default_rng(seed + 5)
    leaf = (sp.a > 0.5) & (sp.yy < sp.h - 110)
    ys, xs = np.nonzero(leaf)
    s = hexrgb(sparkle)
    for i in rng.integers(0, len(ys), 70):
        y, x = ys[i], xs[i]
        sp.rgb[y, x] = s
        if rng.random() < 0.3:
            sp.rgb[max(0, y - 1):y + 2, x] = s * 0.9
            sp.rgb[y, max(0, x - 1):x + 2] = s * 0.9
    return sp


def lantern_tree(seed=41):
    sp = nature.broadleaf(LEAF_DARK, seed)
    rng = np.random.default_rng(seed)
    leaf = sp.a > 0.5
    for i in range(9):
        x = int(rng.uniform(40, sp.w - 40))
        ys = np.nonzero(leaf[:, x])[0]
        if not len(ys):
            continue
        y = int(ys.max() - rng.uniform(4, 40))
        if y > sp.h - 110:
            continue
        sp.put(sp.rect(x, y - 12, 1, 12), BARK[1])
        body = sp.ellipse(x, y + 5, 6, 7)
        sp.put(body, quant(sphere_shade(sp, x, y + 5, 6, 7) * 0.6 + 0.4, LANTERN))
        sp.put(sp.rect(x - 4, y - 2, 9, 2), BARK[1])
        glow(sp, x, y + 5, 16, LANTERN[3], 0.35)
    return sp


def willow(seed=51, w=200, h=250):
    sp = Sprite(w, h)
    rng = np.random.default_rng(seed)
    cx, base = w / 2, h - 6
    trunk = sp.poly([(cx - 9, base - 120), (cx + 9, base - 120), (cx + 14, base), (cx - 14, base)])
    sp.put(trunk, quant(0.7 - (sp.xx - cx + 14) / 28 * 0.6, BARK, bayer(h, w)))
    clusters = []
    for i in range(18):
        a = rng.uniform(np.pi, 2 * np.pi)
        clusters.append((cx + np.cos(a) * rng.uniform(0, 62), base - 160 + np.sin(a) * rng.uniform(0, 40),
                         rng.uniform(26, 34), 0.5))
    nature._leafy_cluster_field(sp, clusters, LEAF, seed)
    # hanging strands
    for i in range(46):
        x0 = cx + rng.uniform(-88, 88)
        top = base - 175 + abs(x0 - cx) * 0.45 + rng.uniform(-6, 6)
        length = rng.uniform(60, 120)
        for y in range(int(top), int(min(base - 8, top + length))):
            t = (y - top) / length
            x = int(x0 + np.sin(t * 2.2 + i) * 2)
            if 0 <= x < w - 2:
                sp.put(sp.rect(x, y, 3, 1), LEAF[2 + (i % 4)] * (1 - t * 0.15))
    outline(sp, LEAF[0] * 0.75)
    return sp


def mushrooms(glowing=False, seed=61, w=96, h=66):
    sp = Sprite(w, h)
    rng = np.random.default_rng(seed)
    capR = CRYSTAL_CYAN if glowing else CLOTH_RED
    for i in range(5):
        x = rng.uniform(20, w - 20)
        s = rng.uniform(0.95, 1.45)
        top = h - 8 - 22 * s
        sp.put(sp.rect(int(x - 3 * s), int(top + 6 * s), int(6 * s) + 1, int(h - 6 - top - 6 * s)), hexrgb('#efe4cf'))
        cap = sp.ellipse(x, top + 6 * s, 12 * s, 8 * s) & (sp.yy < top + 8 * s)
        sp.put(cap, quant(sphere_shade(sp, x, top + 6 * s, 12 * s, 8 * s), capR))
        for k in range(3):
            sp.put(sp.ellipse(x + rng.uniform(-6, 6) * s, top + rng.uniform(1, 5) * s, 1.6, 1.3), hexrgb('#fff6ea'))
        if glowing:
            glow(sp, x, top + 6 * s, 22 * s, capR[4], 0.45)
    outline(sp, capR[0] * 0.8, width=2)
    return sp


def crystal(R=CRYSTAL, seed=71, w=90, h=120):
    sp = Sprite(w, h)
    rng = np.random.default_rng(seed)
    base = h - 8
    shards = [(w / 2, 1.0, 0), (w / 2 - 22, 0.62, -0.35), (w / 2 + 22, 0.7, 0.3), (w / 2 - 34, 0.38, -0.6), (w / 2 + 34, 0.42, 0.55)]
    for x, s, lean in sorted(shards, key=lambda q: q[1]):
        hh = (h - 26) * s
        bw = 12 + 10 * s
        tipx = x + lean * hh * 0.35
        pts = [(x - bw / 2, base), (x - bw / 2 + lean * hh * 0.25, base - hh * 0.78), (tipx, base - hh), (x + bw / 2 + lean * hh * 0.25, base - hh * 0.78), (x + bw / 2, base)]
        m = sp.poly(pts)
        left = sp.xx < (x + lean * (base - sp.yy) * 0.3)
        sh = np.where(left, 0.82, 0.48) + (base - sp.yy) / hh * 0.15
        sp.put(m, quant(sh, R))
        sp.put(m & (np.abs(sp.xx - (x + lean * (base - sp.yy) * 0.3)) < 1.2), R[-1])
    sp.put(sp.ellipse(w / 2, base, w * 0.42, 6) & (sp.a < 0.5), STONE[2])
    glow(sp, w / 2, base - 40, 60, R[4], 0.35)
    outline(sp, R[0] * 0.8)
    return sp


def star_stone(seed=81, w=70, h=80):
    sp = nature.rock(seed, w, h, STONE)
    cx, cy = w / 2, h * 0.55
    star = []
    for i in range(10):
        a = -np.pi / 2 + i * np.pi / 5
        r = 11 if i % 2 == 0 else 4.5
        star.append((cx + np.cos(a) * r, cy + np.sin(a) * r))
    m = sp.poly(star) & (sp.a > 0.5)
    sp.rgb[m] = hexrgb('#fff1a8')
    glow(sp, cx, cy, 26, hexrgb('#ffe680'), 0.45)
    return sp


def lantern_post(seed=91, w=60, h=170):
    sp = Sprite(w, h)
    cx = w / 2
    sp.put(sp.rect(cx - 4, 40, 8, h - 50), quant(0.75 - (sp.xx - cx + 4) / 8 * 0.6, WOOD))
    sp.put(sp.rect(cx - 12, h - 14, 24, 10), WOOD[1])
    sp.put(sp.rect(cx - 4, 34, 22, 5), WOOD[2])                    # arm
    lx, ly = cx + 15, 62
    sp.put(sp.rect(lx, 38, 1, 12), METAL[1])
    body = sp.ellipse(lx, ly, 10, 13)
    sp.put(body, quant(sphere_shade(sp, lx, ly, 10, 13) * 0.55 + 0.45, LANTERN))
    for yy in (ly - 6, ly, ly + 6):
        sp.put(body & (np.abs(sp.yy - yy) < 0.8), LANTERN[1])
    sp.put(sp.rect(lx - 7, ly - 14, 14, 3) | sp.rect(lx - 7, ly + 12, 14, 3), WOOD[0])
    outline(sp, WOOD[0] * 0.8)
    glow(sp, lx, ly, 34, LANTERN[3], 0.5)
    return sp


def planter(flowers=0, seed=101, w=80, h=72):
    sp = Sprite(w, h)
    pot = sp.poly([(12, 34), (w - 12, 34), (w - 20, h - 6), (20, h - 6)])
    sp.put(pot, quant(0.8 - (sp.xx - 12) / (w - 24) * 0.55, TERRACOTTA))
    sp.put(sp.rect(8, 30, w - 16, 8), TERRACOTTA[4])
    sp.put(sp.rect(8, 36, w - 16, 2), TERRACOTTA[1])
    b = nature.bush(seed, w=w, h=46, flowers=FLOWERS[flowers % len(FLOWERS)])
    m = b.a > 0.5
    sub = np.zeros((h, w), bool)
    sub[0:46, :] = m
    sp.rgb[0:46][m] = b.rgb[m]
    sp.a[0:46][m] = 1
    outline(sp, TERRACOTTA[0] * 0.8)
    return sp


def crate(seed=111, w=64, h=64):
    sp = Sprite(w, h)
    front = sp.rect(6, 18, 46, 40)
    top = sp.poly([(6, 18), (18, 6), (w - 2, 6), (52, 18)])
    side = sp.poly([(52, 18), (w - 2, 6), (w - 2, 46), (52, 58)])
    built._planks(sp, front, WOOD, True, 10, seed)
    sp.put(top, WOOD[5])
    sp.put(side, WOOD[2])
    for m in (sp.rect(6, 18, 46, 4), sp.rect(6, 54, 46, 4), sp.rect(6, 18, 4, 40), sp.rect(48, 18, 4, 40)):
        sp.put(m, WOOD[1])
    outline(sp, WOOD[0] * 0.8)
    return sp


def barrel(seed=121, w=56, h=72):
    sp = Sprite(w, h)
    body = sp.ellipse(w / 2, h / 2 + 4, 22, 32) & sp.rect(4, 12, w - 8, h - 18)
    stave = ((sp.xx - 6) % 9 < 1.2)
    sh = 0.85 - np.abs(sp.xx - w / 2 + 6) / 26 * 0.6
    col = quant(sh, WOOD)
    col[stave] = WOOD[1]
    sp.put(body, col)
    for y in (20, h - 18):
        sp.put(body & (np.abs(sp.yy - y) < 2.5), METAL[2])
    sp.put(sp.ellipse(w / 2, 13, 20, 5), WOOD[4])
    outline(sp, WOOD[0] * 0.8)
    return sp


def umbrella_table(awning=('#e88aa8', '#fbf3ee'), w=150, h=170):
    sp = Sprite(w, h)
    cx = w / 2
    sp.put(sp.rect(cx - 3, 50, 6, h - 64), METAL[3])
    top = sp.ellipse(cx, h - 40, 44, 12)
    sp.put(sp.rect(cx - 4, h - 40, 8, 30), METAL[2])
    sp.put(top, hexrgb('#f6efe6'))
    sp.put(sp.ellipse(cx, h - 42, 44, 10), hexrgb('#ffffff'))
    for sx in (-1, 1):
        chair = sp.rect(cx + sx * 56 - 10, h - 46, 20, 34)
        sp.put(chair, hexrgb('#c79bd6'))
        sp.put(sp.rect(cx + sx * 56 - 10, h - 46, 20, 6), hexrgb('#e2c3ec'))
    can = sp.poly([(cx, 8), (w - 6, 54), (6, 54)])
    seg = (np.floor((np.arctan2(sp.yy - 8, sp.xx - cx) * 7)) % 2) == 0
    c0, c1 = hexrgb(awning[0]), hexrgb(awning[1])
    col = np.where(seg[..., None], c0, c1) * (1 - (sp.xx - 6) / (w - 12) * 0.2)[..., None]
    sp.put(can, col)
    sp.put(sp.rect(6, 52, w - 12, 5) & sp.poly([(0, 50), (w, 50), (w, 60), (0, 60)]), c0 * 0.8)
    outline(sp, c0 * 0.45)
    return sp


def flowerbed(seed=131, w=140, h=60):
    sp = Sprite(w, h)
    sp.put(sp.rect(4, 24, w - 8, h - 30), WOOD[2])
    sp.put(sp.rect(4, 24, w - 8, 4), WOOD[4])
    sp.put(sp.rect(10, 28, w - 20, 10), hexrgb('#6e5038'))
    rng = np.random.default_rng(seed)
    for i in range(22):
        x, y = rng.uniform(12, w - 12), rng.uniform(10, 30)
        sp.put(sp.ellipse(x, y, rng.uniform(5, 8), rng.uniform(4, 6)), LEAF[rng.integers(2, 6)])
    for i in range(24):
        x, y = rng.uniform(12, w - 12), rng.uniform(6, 28)
        F = FLOWERS[i % 4]
        sp.put(sp.ellipse(x, y, 3.2, 2.8), F[2])
        sp.put(sp.ellipse(x - 1, y - 1, 1.2, 1.2), F[3])
    outline(sp, WOOD[0] * 0.8)
    return sp


# ---------------------------------------------------------------- town clutter (plaza pass)
def sacks(seed=141, w=80, h=56):
    sp = Sprite(w, h)
    BURLAP = ramp('#5e4a32', '#7a6244', '#957c58', '#ad946c', '#c4ab82', '#d8c39c')
    rng = np.random.default_rng(seed)
    for i, (x, y, r) in enumerate(((22, 36, 16), (54, 38, 17), (38, 22, 15))):
        m = sp.ellipse(x, y, r, r * 0.9)
        sp.put(m, quant(sphere_shade(sp, x, y, r, r * 0.9) * 0.8 + (noise(h, w, 2, seed + i) - 0.5) * 0.15, BURLAP))
        sp.put(sp.rect(x - 5, y - r * 0.9 - 2, 10, 5), BURLAP[1])
        if i == 2:
            sp.put(sp.ellipse(x, y - r * 0.9, 9, 3), hexrgb('#e9d98a'))
    outline(sp, BURLAP[0] * 0.8)
    return sp


def crate_stack(seed=151):
    a = crate(seed).image()
    from PIL import Image
    w, h = a.width + 30, a.height + 40
    im = Image.new('RGBA', (w, h))
    im.alpha_composite(a, (0, 40))
    im.alpha_composite(a, (30, 38))
    im.alpha_composite(a.resize((52, 52)), (14, 0))
    return im


def cart(seed=161, w=170, h=120):
    sp = Sprite(w, h)
    built._planks(sp, sp.rect(20, 40, 120, 44), WOOD, True, 11, seed)
    sp.put(sp.rect(20, 36, 120, 6), WOOD[5])
    sp.put(sp.rect(138, 66, 30, 6), WOOD[2])                      # handle
    rng = np.random.default_rng(seed)
    cols = [FLOWERS[0][2], FLOWERS[1][2], FLOWERS[4][2], hexrgb('#8fc65a'), hexrgb('#e2564e')]
    for i in range(26):                                            # fruit / flowers heaped on top
        x, y = rng.uniform(28, 132), rng.uniform(22, 40)
        sp.put(sp.ellipse(x, y, 6, 5), cols[i % len(cols)])
        sp.put(sp.ellipse(x - 2, y - 2, 2, 1.5), hexrgb('#fff4dc'))
    for cx in (46, 116):
        wheel = sp.ellipse(cx, 92, 20, 20)
        sp.put(wheel, WOOD[1])
        sp.put(sp.ellipse(cx, 92, 15, 15), WOOD[3])
        sp.put(sp.ellipse(cx, 92, 4, 4), METAL[3])
        for a in range(0, 180, 45):
            t = np.radians(a)
            sp.put((np.abs((sp.xx - cx) * np.sin(t) - (sp.yy - 92) * np.cos(t)) < 1.6) & sp.ellipse(cx, 92, 15, 15), WOOD[1])
    outline(sp, WOOD[0] * 0.8)
    return sp


def bunting(w=360, h=130, seed=171):
    """Two poles with a sagging string of triangle flags; poles collide, flags do not."""
    sp = Sprite(w, h)
    for x in (8, w - 16):
        sp.put(sp.rect(x, 14, 8, h - 16), quant(0.75 - (sp.xx - x) / 8 * 0.6, WOOD))
        sp.put(sp.ellipse(x + 4, 12, 6, 6), WOOD[5])
    cols = [hexrgb(c) for c in ('#e2566c', '#f2c94c', '#5aa7d6', '#7fc67a', '#f29bc0', '#ffffff')]
    xs = np.linspace(16, w - 16, 15)
    sag = lambda x: 22 + 26 * np.sin((x - 16) / (w - 32) * np.pi)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        sp.put(np.abs(sp.yy - sag(sp.xx)) < 1.1 & (sp.xx >= x0) & (sp.xx <= x1) if False else
               ((np.abs(sp.yy - sag(sp.xx)) < 1.1) & (sp.xx >= x0) & (sp.xx <= x1)), METAL[2])
    for i, x in enumerate(xs[1:-1]):
        y = sag(x)
        tri = sp.poly([(x - 9, y), (x + 9, y), (x, y + 20)])
        sp.put(tri, cols[i % len(cols)])
        sp.put(tri & (sp.xx > x + 2), cols[i % len(cols)] * 0.8)
    outline(sp, WOOD[0] * 0.7, inner=False, width=1)
    return sp


def lantern_string(w=360, h=150, seed=181):
    sp = Sprite(w, h)
    for x in (8, w - 16):
        sp.put(sp.rect(x, 14, 8, h - 16), quant(0.75 - (sp.xx - x) / 8 * 0.6, WOOD))
    sag = lambda x: 22 + 30 * np.sin((x - 16) / (w - 32) * np.pi)
    sp.put((np.abs(sp.yy - sag(sp.xx)) < 1.1) & (sp.xx > 12) & (sp.xx < w - 12), BARK[1])
    for x in np.linspace(40, w - 40, 7):
        y = sag(x) + 14
        sp.put(sp.rect(int(x), int(y) - 13, 1, 10), BARK[1])
        body = sp.ellipse(x, y, 9, 11)
        sp.put(body, quant(sphere_shade(sp, x, y, 9, 11) * 0.55 + 0.45, LANTERN))
        sp.put(sp.rect(int(x) - 6, int(y) - 12, 12, 3) | sp.rect(int(x) - 6, int(y) + 10, 12, 3), WOOD[0])
        glow(sp, x, y, 24, LANTERN[3], 0.4)
    outline(sp, WOOD[0] * 0.7, inner=False, width=1)
    return sp


def tree_planter(seed=191):
    from PIL import Image
    t = nature.broadleaf(LEAF, seed, w=150, h=220).image()
    box = Sprite(110, 52)
    box.put(box.rect(6, 8, 98, 40), quant(0.75 - (box.xx - 6) / 98 * 0.5, STONE))
    box.put(box.rect(2, 4, 106, 8), STONE[5])
    box.put(box.rect(10, 12, 90, 6), hexrgb('#5b4330'))
    outline(box, STONE[0])
    im = Image.new('RGBA', (150, 250))
    im.alpha_composite(t, (0, 0))
    im.alpha_composite(box.image(), (20, 198))
    return im


def flower_cart():
    sp = cart(167)
    return sp


def bollard(w=26, h=50):
    sp = Sprite(w, h)
    sp.put(sp.rect(6, 10, 14, 36), quant(0.8 - (sp.xx - 6) / 14 * 0.6, METAL))
    sp.put(sp.ellipse(13, 10, 7, 4), METAL[5])
    sp.put(sp.rect(6, 20, 14, 3), hexrgb('#d9b25a'))
    outline(sp, METAL[0])
    return sp


def bike_rack(w=120, h=60):
    sp = Sprite(w, h)
    for x in range(14, w - 10, 26):
        sp.put(sp.rect(x, 14, 4, 40) | sp.rect(x + 14, 14, 4, 40) | sp.rect(x, 12, 18, 4), METAL[3])
    sp.put(sp.rect(6, 50, w - 12, 4), METAL[2])
    outline(sp, METAL[0], width=1)
    return sp


# ---------------------------------------------------------------- forest undergrowth
def fern(seed=201, w=110, h=70, R=LEAF):
    sp = Sprite(w, h)
    rng = np.random.default_rng(seed)
    base = (w / 2, h - 4)
    for i in range(9):
        ang = np.radians(rng.uniform(-170, -10))
        L = rng.uniform(34, 52)
        ex, ey = base[0] + np.cos(ang) * L, base[1] + np.sin(ang) * L * 0.75
        n = 12
        for k in range(n):
            t = k / n
            x = base[0] + (ex - base[0]) * t
            y = base[1] + (ey - base[1]) * t - np.sin(t * np.pi) * 6
            r = (1 - t) * 6 + 2
            sp.put(sp.ellipse(x, y, r * 1.2, r * 0.7), R[2 + int((1 - t) * 2 + (i % 2))])
        sp.put(sp.ellipse(ex, ey, 2.5, 2), R[5])
    outline(sp, R[0] * 0.8, width=1)
    return sp


def tall_grass(seed=211, w=70, h=56, R=LEAF):
    sp = Sprite(w, h)
    rng = np.random.default_rng(seed)
    for i in range(30):
        x0 = rng.uniform(8, w - 8)
        top = rng.uniform(4, 28)
        bend = rng.uniform(-10, 10)
        for y in range(int(top), h - 2):
            t = (y - top) / (h - top)
            x = x0 + bend * (1 - t) ** 2
            sp.put(sp.rect(int(x), y, 2, 1), R[2 + (i % 4)])
    outline(sp, R[0] * 0.8, inner=False, width=1)
    return sp


def fallen_log(seed=221, w=170, h=60):
    sp = Sprite(w, h)
    body = sp.rect(14, 18, w - 34, 30)
    sp.put(body, quant(0.85 - np.abs(sp.yy - 30) / 16 * 0.6 + (noise(h, w, 3, seed) - 0.5) * 0.2, BARK))
    end = sp.ellipse(w - 20, 33, 10, 15)
    rings = (np.sqrt(((sp.xx - (w - 20)) / 10) ** 2 + ((sp.yy - 33) / 15) ** 2) * 4) % 1
    sp.put(end, np.where((rings < 0.3)[..., None], hexrgb('#a9825a'), hexrgb('#cfa977')))
    moss = body & (sp.yy < 26) & (noise(h, w, 4, seed + 1) > 0.5)
    sp.rgb[moss] = LEAF[4]
    rng = np.random.default_rng(seed)
    for i in range(3):
        x = rng.uniform(30, w - 50)
        sp.put(sp.ellipse(x, 18, 5, 3) & (sp.yy < 18), hexrgb('#e8d6b4'))
    outline(sp, BARK[0])
    return sp


def big_oak(seed=231, R=LEAF):
    return nature.broadleaf(R, seed, w=240, h=320)


KIT = {
    'hd_tree_dream_a': (lambda: dream_tree(DREAM, 31), 16, 9, 'sort'),
    'hd_tree_dream_b': (lambda: dream_tree(DREAM_BLUE, 33, '#e8f6ff'), 16, 9, 'sort'),
    'hd_tree_dream_c': (lambda: dream_tree(kit.CHERRY, 35), 16, 9, 'sort'),
    'hd_tree_lantern': (lambda: lantern_tree(41), 16, 9, 'sort'),
    'hd_tree_lantern_b': (lambda: lantern_tree(43), 16, 9, 'sort'),
    'hd_tree_willow': (lambda: willow(51), 18, 9, 'sort'),
    'hd_tree_dark_a': (lambda: nature.broadleaf(LEAF_DARK, 23), 16, 9, 'sort'),
    'hd_tree_dark_b': (lambda: nature.broadleaf(LEAF_DARK, 27), 16, 9, 'sort'),
    'hd_mushrooms': (lambda: mushrooms(False, 61), 0, 0, 'sort'),
    'hd_mushrooms_glow': (lambda: mushrooms(True, 63), 0, 0, 'sort'),
    'hd_crystal': (lambda: crystal(CRYSTAL, 71), 30, 10, 'sort'),
    'hd_crystal_cyan': (lambda: crystal(CRYSTAL_CYAN, 73), 30, 10, 'sort'),
    'hd_star_stone': (lambda: star_stone(81), 26, 10, 'sort'),
    'hd_lantern_post': (lambda: lantern_post(91), 8, 6, 'sort'),
    'hd_planter_pink': (lambda: planter(0, 101), 30, 10, 'sort'),
    'hd_planter_violet': (lambda: planter(2, 103), 30, 10, 'sort'),
    'hd_crate': (lambda: crate(111), 26, 10, 'sort'),
    'hd_barrel': (lambda: barrel(121), 22, 9, 'sort'),
    'hd_umbrella_table': (lambda: umbrella_table(), 60, 14, 'sort'),
    'hd_flowerbed': (lambda: flowerbed(131), 60, 10, 'sort'),
    'hd_bush_berry': (lambda: nature.bush(19, flowers=FLOWERS[0]), 0, 0, 'sort'),  # walk-through, rustles
    'hd_fern_a': (lambda: fern(201), 0, 0, 'sort'),
    'hd_fern_b': (lambda: fern(203, R=LEAF_DARK), 0, 0, 'sort'),
    'hd_grass_tall': (lambda: tall_grass(211), 0, 0, 'sort'),
    'hd_grass_tall_b': (lambda: tall_grass(213, R=LEAF_DARK), 0, 0, 'sort'),
    'hd_log': (lambda: fallen_log(221), 60, 12, 'sort'),
    'hd_tree_big_a': (lambda: big_oak(231), 22, 11, 'sort'),
    'hd_tree_big_b': (lambda: big_oak(233, LEAF_DARK), 22, 11, 'sort'),
    'hd_sacks': (lambda: sacks(141), 30, 10, 'sort'),
    'hd_crate_stack': (lambda: crate_stack(151), 40, 12, 'sort'),
    'hd_cart': (lambda: cart(161), 60, 14, 'sort'),
    'hd_bunting': (lambda: bunting(), 0, 0, 'sort'),
    'hd_lantern_string': (lambda: lantern_string(), 0, 0, 'sort'),
    'hd_tree_planter': (lambda: tree_planter(191), 46, 14, 'sort'),
    'hd_bollard': (lambda: bollard(), 8, 6, 'sort'),
    'hd_bike_rack': (lambda: bike_rack(), 50, 8, 'sort'),
    # Plaza landmarks, drawn new (replace the old v43/v51 PNGs)
    'hd_house_arland': (lambda: lm.house('arland', 600, 500), 250, 82, 'sort'),
    'hd_house_sofia': (lambda: lm.house('sofia', 620, 500), 260, 82, 'sort'),
    'hd_cafe_senja': (lambda: lm.house('cafe', 680, 500), 280, 82, 'sort'),
    'hd_fountain_grand': (lambda: lm.fountain_grand(), 190, 70, 'sort'),
    'hd_fountain_tiered': (lambda: lm.fountain_tiered(), 48, 18, 'sort'),
    'hd_mural_old': (lambda: lm.mural_wall(False), 112, 12, 'sort'),
    'hd_mural_new': (lambda: lm.mural_wall(True), 112, 12, 'sort'),
    'hd_notice_board': (lambda: lm.notice_board(), 50, 8, 'sort'),
    'hd_mailbox': (lambda: lm.mailbox(), 6, 4, 'sort'),
    'hd_mailbox_old': (lambda: lm.old_mailbox(), 12, 6, 'sort'),
    'hd_bicycle': (lambda: lm.bicycle(), 30, 6, 'sort'),
    'hd_vending': (lambda: lm.vending(), 26, 12, 'sort'),
    'hd_signpost_w': (lambda: lm.signpost([('Taman', -1), ('Plaza', 1)]), 6, 4, 'sort'),
    'hd_signpost_e': (lambda: lm.signpost([('Jalan Kota', 1), ('Plaza', -1)]), 6, 4, 'sort'),
    'hd_signpost_s': (lambda: lm.signpost([('Danau', 1), ('Plaza', -1)]), 6, 4, 'sort'),
    'hd_banner_cafe': (lambda: lm.banner_pole(), 0, 0, 'sort'),
    'hd_lamp_gold': (lambda: lm.lamp_gold(), 0, 0, 'sort'),
    'hd_birdbath': (lambda: lm.birdbath(), 22, 12, 'sort'),
    'hd_garden_plot': (lambda: lm.garden_plot(), 70, 20, 'sort'),
    'hd_flower_buckets': (lambda: lm.flower_buckets(0), 70, 14, 'sort'),
    'hd_flower_buckets_b': (lambda: lm.flower_buckets(1), 70, 14, 'sort'),
    'hd_flower_buckets_c': (lambda: lm.flower_buckets(2), 70, 14, 'sort'),
    'hd_column_stone': (lambda: lm.column_stone(), 14, 10, 'sort'),
    # V8: Clockwork Station landmarks (tools/artkit/clockwork.py)
    'hd_clock_tower': (lambda: cwk.clock_tower(), 128, 26, 'sort'),
    'hd_train_car': (lambda: cwk.train_car(), 236, 22, 'sort'),
    'hd_lamp_clock': (lambda: cwk.lamp_clock(), 0, 0, 'sort'),
    'hd_gear_big': (lambda: cwk.gear_big(), 44, 8, 'sort'),
    'hd_railing_iron': (lambda: lm.railing_iron(), 98, 8, 'sort'),
    'hd_fence_picket': (lambda: lm.fence_picket(), 98, 8, 'sort'),
    'hd_fence_picket_b': (lambda: lm.fence_picket(seed=5), 98, 8, 'sort'),
    # Hutan Bisik landmarks, drawn new
    'hd_cave_mouth': (lambda: fo.cave_mouth(), 0, 0, 'sort'),
    'hd_waterfall': (lambda: fo.waterfall(), 0, 0, 'sort'),
    'hd_tent': (lambda: fo.tent(), 76, 16, 'sort'),
    'hd_campfire': (lambda: fo.campfire(), 22, 8, 'sort'),
    'hd_log_bench': (lambda: fo.log_bench(seed=0), 56, 10, 'sort'),
    'hd_log_bench_b': (lambda: fo.log_bench(seed=3), 56, 10, 'sort'),
    'hd_stone_lantern': (lambda: fo.stone_lantern(), 18, 8, 'sort'),
    'hd_carving_moon': (lambda: fo.carved_stone('moon'), 22, 8, 'sort'),
    'hd_carving_star': (lambda: fo.carved_stone('star'), 22, 8, 'sort'),
    'hd_chest': (lambda: fo.chest(False), 26, 10, 'sort'),
    'hd_chest_open': (lambda: fo.chest(True), 26, 10, 'sort'),
    'hd_bridge_broken': (lambda: fo.bridge_stream(True), 0, 0, 'floor'),
    'hd_bridge_fixed': (lambda: fo.bridge_stream(False), 0, 0, 'floor'),
    'hd_rock_ledge': (lambda: fo.rock_ledge(), 0, 0, 'sort'),
    'hd_rock_ledge_b': (lambda: fo.rock_ledge(seed=33), 0, 0, 'sort'),
    'hd_light_shaft': (lambda: fo.light_shaft(seed=1), 0, 0, 'sort'),
    'hd_signpost_hill': (lambda: lm.signpost([('Bukit', 1), ('Kemah', -1)]), 6, 4, 'sort'),
    'hd_signpost_park': (lambda: lm.signpost([('Taman', 1), ('Kemah', -1)]), 6, 4, 'sort'),
    'hd_signpost_camp': (lambda: lm.signpost([('Gua', -1), ('Sungai', 1)]), 6, 4, 'sort'),
    # Jalan Kota (town street), drawn new
    'hd_shop_florist': (lambda: lm.shopfront('florist', 400), 184, 24, 'sort'),
    'hd_shop_bakery': (lambda: lm.shopfront('bakery', 400), 184, 24, 'sort'),
    'hd_shop_mart': (lambda: lm.shopfront('mart', 360), 164, 24, 'sort'),
    'hd_shop_arcade': (lambda: lm.shopfront('arcade', 400), 184, 24, 'sort'),
    'hd_shop_books': (lambda: lm.shopfront('books', 260), 114, 24, 'sort'),
    'hd_signpost_town_w': (lambda: lm.signpost([('Plaza', -1), ('Halte', 1)]), 6, 4, 'sort'),
    'hd_signpost_town_e': (lambda: lm.signpost([('Perumahan', 1), ('Plaza', -1)]), 6, 4, 'sort'),
    'hd_library': (lambda: lm.library(), 260, 30, 'sort'),
    'hd_house_pink': (lambda: lm.house_variant('pink'), 250, 82, 'sort'),
    'hd_house_mint': (lambda: lm.house_variant('mint'), 250, 82, 'sort'),
    'hd_house_butter': (lambda: lm.house_variant('butter'), 260, 82, 'sort'),
    'hd_house_violet': (lambda: lm.house_variant('violet'), 250, 82, 'sort'),
    'hd_house_redbrick': (lambda: lm.house_variant('redbrick'), 260, 82, 'sort'),
    'hd_signpost_res': (lambda: lm.signpost([('Jalan Kota', -1), ('Perpustakaan', 1)]), 6, 4, 'sort'),
    'hd_fishing_hut': (lambda: lm.fishing_hut(), 120, 20, 'sort'),
    'hd_telescope': (lambda: lm.telescope(), 16, 6, 'sort'),
    'hd_observatory': (lambda: lm.observatory(), 196, 40, 'sort'),
    'hd_pier_post': (lambda: lm.pier_post(), 10, 6, 'sort'),
    'hd_lifebuoy': (lambda: lm.lifebuoy_post(), 8, 6, 'sort'),
    'hd_signpost_lake': (lambda: lm.signpost([('Plaza', -1), ('Dermaga', 1)]), 6, 4, 'sort'),
    'hd_car_red': (lambda: lm.car('#c4433f'), 104, 30, 'sort'),
    'hd_car_blue': (lambda: lm.car('#3d6fd3', facing=-1), 104, 30, 'sort'),
    'hd_car_cream': (lambda: lm.car('#e8dcbb'), 104, 30, 'sort'),
    'hd_car_green': (lambda: lm.car('#4f8a6a', facing=-1), 104, 30, 'sort'),
    'hd_bus_shelter': (lambda: lm.bus_shelter(), 96, 14, 'sort'),
    'hd_kiosk': (lambda: lm.kiosk(), 76, 16, 'sort'),
    'hd_flower_stall': (lambda: lm.flower_stall(), 88, 14, 'sort'),
}


def build(only=None, sheet=None):
    OUT.mkdir(parents=True, exist_ok=True)
    pj = A / 'data/props.json'
    data = json.loads(pj.read_text(encoding='utf-8'))
    shots = []
    for pid, (fn, cw, ch, layer) in KIT.items():
        if only and pid not in only:
            continue
        r = fn()
        img = r.image() if hasattr(r, 'image') else r
        rel = 'props/hd/%s@2x.png' % pid
        img.save(A / rel, optimize=True)
        data['props'][pid] = {'image': rel, 'cw': cw, 'ch': ch, 'layer': layer}
        shots.append((pid, img))
        print(pid, img.size)
    pj.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if sheet:
        kit.sheet(shots, sheet)


if __name__ == '__main__':
    args = sys.argv[1:]
    sheet = None
    if '--sheet' in args:
        i = args.index('--sheet'); sheet = args[i + 1]; del args[i:i + 2]
    build(set(args) or None, sheet)
