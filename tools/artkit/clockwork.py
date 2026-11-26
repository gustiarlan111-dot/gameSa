"""V8 landmarks for Clockwork Station ("Waktu yang Tidak Bisa Kembali"), drawn from code with the v6
kit rules (2 texels per world unit, top-left light, coloured outlines, limited ramps, ordered dither).

  clock_tower()   the station's clock tower, ~7 character heights tall (the map's landmark)
  train_car()     an old passenger carriage standing on a short stretch of track
  lamp_clock()    platform lamp post with a hanging two-faced clock (lines the paths)
  gear_big()      a brass gear half sunk in the ground, mossy

Every builder returns a Sprite whose bottom-centre is the prop's foot point on the map.
Registered in tools/kit_extra.py (hd_clock_tower, hd_train_car, hd_lamp_clock, hd_gear_big).
"""
import numpy as np
from kit import Sprite, quant, bayer, outline, noise, hexrgb, ramp, STONE, METAL, LEAF, WOOD
from landmarks import GOLD, SLATE, CREAM, ground_shadow, glow, hgrad, vgrad, bricks

BRASS = ramp('#4a3212', '#6e4c1a', '#94682a', '#b98a3c', '#d6ab58', '#ecca7c', '#fbe6a8')
TEAL = ramp('#13282e', '#1b3940', '#254c54', '#30606a', '#3f7680', '#558e96', '#73a8ae')
SANDSTONE = ramp('#5a4a3a', '#776451', '#94806a', '#b09c83', '#c9b79c', '#ddcfb5', '#eee4cf')
FACE = ramp('#9c9078', '#c4b89c', '#e2d8bf', '#f3ecd8', '#fdf9ee')
WARM = ramp('#d98a2c', '#f5b44a', '#ffd776', '#fff0b8', '#fffbe6')


def _gear(sp, cx, cy, r, teeth, R, dith, hole=0.38, phase=0.0):
    """Mask + shading for a toothed gear (returns the mask)."""
    ang = np.arctan2(sp.yy + 0.5 - cy, sp.xx + 0.5 - cx)
    d = np.hypot(sp.xx + 0.5 - cx, sp.yy + 0.5 - cy)
    tooth = (np.cos(ang * teeth + phase) > 0.15) * (r * 0.16)
    m = (d <= r * 0.84 + tooth) & (d >= r * hole)
    spokes = np.zeros_like(m)
    for k in range(5):
        a = phase + k * 2 * np.pi / 5
        along = (sp.xx + 0.5 - cx) * np.cos(a) + (sp.yy + 0.5 - cy) * np.sin(a)
        across = -(sp.xx + 0.5 - cx) * np.sin(a) + (sp.yy + 0.5 - cy) * np.cos(a)
        spokes |= (np.abs(across) < r * 0.09) & (along > 0) & (d < r * 0.7)
    ring = (d >= r * 0.58) & (d <= r * 0.84 + tooth)
    hub = d <= r * 0.2
    full = ring | spokes | hub
    shade = 0.55 + 0.35 * (-(sp.xx - cx) / r * 0.6 - (sp.yy - cy) / r * 0.8) + (noise(sp.h, sp.w, 3, int(cx + cy)) - 0.5) * 0.15
    sp.put(full, quant(shade, R, dith))
    sp.put(ring & (d > r * 0.8 + tooth - 2), R[min(len(R) - 1, 5)])       # bright rim
    sp.put(hub & (d > r * 0.12), R[2])
    return full


def clock_tower(W=300, H=800):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 8, 128, 14)
    # stepped plinth
    for i, (hw, y0, hh) in enumerate([(132, H - 34, 26), (118, H - 58, 26)]):
        m = sp.rect(cx - hw, y0, hw * 2, hh)
        sp.put(m, quant(hgrad(sp, cx - hw, cx + hw, 0.85, 0.35) + (noise(H, W, 3, 10 + i) - 0.5) * 0.12, STONE, dith))
        sp.put(sp.rect(cx - hw, y0, hw * 2, 2), STONE[6])
    # shaft: sandstone blocks with stone quoins at the corners
    sx0, sx1, sy0, sy1 = cx - 92, cx + 92, 330, H - 58
    shaft = sp.rect(sx0, sy0, sx1 - sx0, sy1 - sy0)
    bricks(sp, shaft, SANDSTONE, sx0, sy0, bw=30, bh=14, seed=3)
    sp.rgb[shaft] *= (1.08 - 0.32 * np.clip((sp.xx[shaft] - sx0) / (sx1 - sx0), 0, 1))[:, None]
    for qx in (sx0, sx1 - 16):
        for k, y in enumerate(range(int(sy0), int(sy1), 24)):
            w = 16 if k % 2 == 0 else 22
            x = qx if qx == sx0 else sx1 - w
            q = sp.rect(x, y, w, 22)
            sp.put(q, quant(hgrad(sp, x, x + w, 0.9, 0.5) * (0.95 if qx == sx0 else 0.7), STONE, dith))
    # string courses
    for y in (sy0, 560):
        sp.put(sp.rect(sx0 - 8, y - 4, sx1 - sx0 + 16, 10), quant(hgrad(sp, sx0, sx1, 0.95, 0.4), STONE, dith))
        sp.put(sp.rect(sx0 - 8, y - 4, sx1 - sx0 + 16, 2), STONE[6])
    # arched door with a lit fanlight
    dw, dh, db = 64, 120, H - 58
    door = sp.rect(cx - dw / 2, db - dh + dw / 2, dw, dh - dw / 2) | sp.ellipse(cx, db - dh + dw / 2, dw / 2, dw / 2)
    sp.put(door & ~sp.rect(0, 0, W, db - dh + dw / 2 - 1) | (door & (sp.yy >= db - dh)), quant(hgrad(sp, cx - dw / 2, cx + dw / 2, 0.7, 0.25), WOOD, dith))
    fan = sp.ellipse(cx, db - dh + dw / 2, dw / 2 - 6, dw / 2 - 6) & (sp.yy < db - dh + dw / 2)
    sp.put(fan, quant(vgrad(sp, db - dh, db - dh + dw / 2, 1.0, 0.6), WARM, dith))
    for a in np.linspace(0.3, np.pi - 0.3, 4):
        bx = cx + np.cos(a) * (dw / 2 - 6)
        by = db - dh + dw / 2 - np.sin(a) * (dw / 2 - 6)
        n = max(int(np.hypot(bx - cx, by - (db - dh + dw / 2))), 1)
        for t in np.linspace(0, 1, n):
            sp.rgb[int(db - dh + dw / 2 - (db - dh + dw / 2 - by) * t), int(cx + (bx - cx) * t)] = WOOD[1]
    sp.put(sp.rect(cx - 1, db - dh + dw / 2, 2, dh - dw / 2), WOOD[1])
    sp.put(sp.ellipse(cx + 18, db - 54, 3, 3), BRASS[5])
    arch = sp.ellipse(cx, db - dh + dw / 2, dw / 2 + 8, dw / 2 + 8) & ~sp.ellipse(cx, db - dh + dw / 2, dw / 2, dw / 2) & (sp.yy < db - dh + dw / 2)
    sp.put(arch, quant(hgrad(sp, cx - dw, cx + dw, 0.95, 0.45), STONE, dith))
    # exposed gear behind a round window (the station's heart)
    gx, gy, gr = cx, 470, 46
    win = sp.ellipse(gx, gy, gr + 6, gr + 6)
    sp.put(win, hexrgb('#1a1626'))
    g = _gear(sp, gx + 8, gy + 6, gr, 12, BRASS, dith, phase=0.3)
    sp.a[g & ~win] = 0                                             # only inside the window
    _gear(sp, gx - 26, gy - 22, 22, 8, BRASS, dith, phase=1.1)
    sp.a[~win & (np.hypot(sp.xx - gx, sp.yy - gy) < gr + 30) & (sp.yy < 560) & (sp.yy > 400) & ~shaft] = 0
    ring = sp.ellipse(gx, gy, gr + 12, gr + 12) & ~win
    sp.put(ring, quant(hgrad(sp, gx - gr, gx + gr, 0.95, 0.4), STONE, dith))
    # slit windows
    for wy in (380, 620):
        for wx in (cx - 52, cx + 40):
            sp.put(sp.rect(wx, wy, 12, 34) | sp.ellipse(wx + 6, wy, 6, 6), hexrgb('#231d33'))
            sp.put(sp.rect(wx + 2, wy + 4, 3, 26), quant(np.full((H, W), 0.7), WARM))
    # clock storey: a wider block, cornice, big face
    bx0, bx1, by0, by1 = cx - 110, cx + 110, 148, 334
    blk = sp.rect(bx0, by0, bx1 - bx0, by1 - by0)
    sp.put(blk, quant(hgrad(sp, bx0, bx1, 0.9, 0.3) + (noise(H, W, 4, 21) - 0.5) * 0.1, CREAM, dith))
    sp.put(sp.rect(bx0 - 10, by1 - 12, bx1 - bx0 + 20, 14), quant(hgrad(sp, bx0, bx1, 0.95, 0.4), STONE, dith))
    sp.put(sp.rect(bx0 - 12, by0 - 6, bx1 - bx0 + 24, 14), quant(hgrad(sp, bx0, bx1, 0.95, 0.4), STONE, dith))
    sp.put(sp.rect(bx0 - 12, by0 - 6, bx1 - bx0 + 24, 2), STONE[6])
    for px in (bx0 + 4, bx1 - 18):                                 # pilasters
        sp.put(sp.rect(px, by0 + 8, 14, by1 - by0 - 20), quant(hgrad(sp, px, px + 14, 0.95, 0.5), STONE, dith))
    fcx, fcy, fr = cx, 242, 76
    sp.put(sp.ellipse(fcx, fcy, fr + 10, fr + 10), quant(hgrad(sp, fcx - fr, fcx + fr, 1.0, 0.35), BRASS, dith))
    sp.put(sp.ellipse(fcx, fcy, fr + 3, fr + 3), BRASS[1])
    face = sp.ellipse(fcx, fcy, fr, fr)
    sp.put(face, quant(0.95 - 0.35 * np.clip(np.hypot(sp.xx - fcx + 20, sp.yy - fcy + 24) / (fr * 1.6), 0, 1), FACE, dith))
    sp.put(sp.ellipse(fcx, fcy, fr - 10, fr - 10) & ~sp.ellipse(fcx, fcy, fr - 12, fr - 12), FACE[0])
    for k in range(60):                                            # minute and hour ticks
        a = k * np.pi / 30
        r0 = fr - (20 if k % 5 == 0 else 13)
        for t in np.linspace(r0, fr - 6, 10):
            x, y = fcx + np.cos(a) * t, fcy + np.sin(a) * t
            w = 2.4 if k % 5 == 0 else 1.0
            sp.put(sp.ellipse(x, y, w, w), hexrgb('#2c2236') if k % 5 == 0 else FACE[0])

    def hand(a, ln, w, col):
        for t in np.linspace(-ln * 0.15, ln, 80):
            sp.put(sp.ellipse(fcx + np.cos(a) * t, fcy + np.sin(a) * t, w, w), col)
    hand(np.deg2rad(-150), fr * 0.55, 3.6, hexrgb('#2c2236'))     # ten past ten: the hour it stopped
    hand(np.deg2rad(-30), fr * 0.82, 2.4, hexrgb('#2c2236'))
    hand(np.deg2rad(110), fr * 0.7, 1.0, hexrgb('#b23a48'))
    sp.put(sp.ellipse(fcx, fcy, 6, 6), BRASS[4])
    glow(sp, fcx, fcy, fr * 1.25, hexrgb('#fff1c2'), 0.12)
    # spire: slate roof with dormer, gold finial
    roof = sp.poly([(cx - 124, by0 + 4), (cx + 124, by0 + 4), (cx + 16, 30), (cx - 16, 30)])
    shingle = ((sp.yy.astype(int) // 10) % 2) * 0.06 + (((sp.xx + (sp.yy // 10) % 2 * 8).astype(int) % 16) < 1) * -0.15
    sp.put(roof, quant(hgrad(sp, cx - 124, cx + 124, 0.9, 0.2) + shingle, SLATE, dith))
    sp.put(sp.poly([(cx - 124, by0 + 4), (cx + 124, by0 + 4), (cx + 118, by0 - 4), (cx - 118, by0 - 4)]), SLATE[5])
    dor = sp.poly([(cx - 24, 120), (cx + 24, 120), (cx + 24, 90), (cx, 70), (cx - 24, 90)])
    sp.put(dor, quant(hgrad(sp, cx - 24, cx + 24, 0.9, 0.4), CREAM, dith))
    sp.put(sp.rect(cx - 9, 92, 18, 24) | sp.ellipse(cx, 92, 9, 8), quant(np.full((H, W), 0.75), WARM))
    sp.put(sp.poly([(cx - 30, 92), (cx + 30, 92), (cx, 64)]) & ~sp.poly([(cx - 22, 92), (cx + 22, 92), (cx, 72)]), SLATE[1])
    sp.put(sp.rect(cx - 3, 6, 6, 28), quant(hgrad(sp, cx - 3, cx + 3, 1.0, 0.4), GOLD))
    sp.put(sp.ellipse(cx, 18, 7, 7), GOLD[4])
    sp.put(sp.poly([(cx, 0), (cx + 4, 8), (cx - 4, 8)]), GOLD[5])
    # ivy climbing the left corner and over the plinth
    rng = np.random.default_rng(5)
    for k in range(260):
        t = k / 260
        y = H - 64 - t ** 1.4 * 300
        x = sx0 + 6 + np.sin(t * 7) * 10 + rng.normal(0, 5)
        sp.put(sp.ellipse(x, y, 5, 4), LEAF[rng.integers(1, 6)])
    for k in range(60):
        x = rng.uniform(cx - 130, cx + 130)
        sp.put(sp.ellipse(x, H - 30 + rng.normal(0, 3), 5, 4), LEAF[rng.integers(1, 5)])
    outline(sp, hexrgb('#1b1628'), width=2)
    return sp


def train_car(W=500, H=264):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 26, 230, 16, 0.38)
    # track: sleepers + two rails (seen from the front-left, rails as long bars)
    for x in range(0, W, 26):
        sp.put(sp.rect(x + 2, H - 30, 18, 22), quant(hgrad(sp, x, x + 20, 0.8, 0.3) - (sp.yy - (H - 30)) / 60, WOOD, dith))
    sp.put(sp.rect(0, H - 34, W, 6), quant(np.full((H, W), 0.55), METAL))
    sp.put(sp.rect(0, H - 34, W, 2), METAL[6])
    sp.put(sp.rect(0, H - 14, W, 5), quant(np.full((H, W), 0.45), METAL))
    sp.put(sp.rect(0, H - 14, W, 1), METAL[5])
    # wheels and bogies
    for wx in (90, 150, W - 150, W - 90):
        sp.put(sp.ellipse(wx, H - 46, 24, 24), quant(0.4 + 0.3 * (-(sp.xx - wx) - (sp.yy - (H - 46))) / 34, METAL, dith))
        sp.put(sp.ellipse(wx, H - 46, 18, 18) & ~sp.ellipse(wx, H - 46, 15, 15), METAL[1])
        for a in np.linspace(0, np.pi, 4, endpoint=False):
            for t in np.linspace(-15, 15, 30):
                sp.put(sp.ellipse(wx + np.cos(a) * t, H - 46 + np.sin(a) * t, 1.2, 1.2), METAL[1])
        sp.put(sp.ellipse(wx, H - 46, 5, 5), BRASS[4])
    for bx in (120, W - 120):
        sp.put(sp.rect(bx - 56, H - 68, 112, 12), quant(hgrad(sp, bx - 56, bx + 56, 0.6, 0.2), METAL, dith))
    # body
    b0, b1, top, bot = 18, W - 18, 66, H - 66
    body = sp.rect(b0, top, b1 - b0, bot - top)
    plank = (((sp.xx.astype(int) - b0) % 22) < 1) * -0.12
    sp.put(body, quant(vgrad(sp, top, bot, 0.85, 0.45) + plank + (noise(H, W, 3, 7) - 0.5) * 0.08, TEAL, dith))
    sp.put(sp.rect(b0, bot - 30, b1 - b0, 30), quant(vgrad(sp, bot - 30, bot, 0.5, 0.25), TEAL, dith))
    for y in (top + 8, bot - 32):
        sp.put(sp.rect(b0, y, b1 - b0, 4), quant(hgrad(sp, b0, b1, 1.0, 0.5), BRASS, dith))
    # windows: six lit, one dark and broken (time stopped here)
    for i in range(7):
        wx = b0 + 34 + i * 62
        wy = top + 24
        win = sp.rect(wx, wy, 44, 50) | sp.ellipse(wx + 22, wy, 22, 10)
        sp.put(sp.rect(wx - 4, wy - 4, 52, 58) | sp.ellipse(wx + 22, wy - 2, 26, 13), BRASS[2])
        if i == 4:
            sp.put(win, hexrgb('#1c1a2a'))
            sp.put(sp.poly([(wx + 6, wy + 10), (wx + 30, wy + 4), (wx + 18, wy + 36)]), hexrgb('#3a4058'))
        else:
            sp.put(win, quant(vgrad(sp, wy - 10, wy + 50, 1.0, 0.55), WARM, dith))
            sp.put(sp.rect(wx + 20, wy - 8, 3, 58), BRASS[1])
            sp.put(sp.rect(wx, wy + 22, 44, 3), BRASS[1])
            sp.put(sp.rect(wx + 4, wy + 30, 36, 14), quant(np.full((H, W), 0.6), ramp('#7a3346', '#a04760', '#c4647c')))
    # door at one end with steps
    dx = b1 - 52
    sp.put(sp.rect(dx, top + 20, 34, bot - top - 20), quant(hgrad(sp, dx, dx + 34, 0.6, 0.25), TEAL, dith))
    sp.put(sp.rect(dx + 6, top + 28, 22, 34), quant(np.full((H, W), 0.7), WARM))
    sp.put(sp.rect(dx - 4, bot - 2, 42, 6), METAL[3])
    sp.put(sp.rect(dx - 8, bot + 6, 50, 6), METAL[2])
    # curved roof with vents
    roof = sp.ellipse(cx, top + 4, (b1 - b0) / 2 + 8, 34) & (sp.yy < top + 6)
    sp.put(roof, quant(vgrad(sp, top - 30, top + 6, 0.9, 0.35), SLATE, dith))
    sp.put(sp.rect(b0 - 8, top + 2, b1 - b0 + 16, 6), SLATE[1])
    for vx in (130, 250, 370):
        sp.put(sp.rect(vx - 12, top - 38, 24, 12), quant(hgrad(sp, vx - 12, vx + 12, 0.9, 0.4), METAL, dith))
    # little plate: the departure that never left
    sp.put(sp.rect(b0 + 30, bot - 26, 90, 18), hexrgb('#f0e6c8'))
    for k in range(6):
        sp.put(sp.rect(b0 + 38 + k * 13, bot - 20, 8, 6), hexrgb('#2c2236'))
    glow(sp, cx, top + 50, 180, hexrgb('#ffd37a'), 0.14)
    outline(sp, hexrgb('#101a1e'), width=2)
    return sp


def lamp_clock(W=124, H=224):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    iron = ramp('#15181d', '#22272e', '#323941', '#46505a', '#5e6a75', '#7a8691')
    ground_shadow(sp, cx, H - 5, 22, 5)
    sp.put(sp.rect(cx - 12, H - 22, 24, 18), quant(hgrad(sp, cx - 12, cx + 12, 0.8, 0.3), iron, dith))
    sp.put(sp.rect(cx - 4, 40, 8, H - 58), quant(hgrad(sp, cx - 4, cx + 4, 0.9, 0.3), iron))
    for yy in (90, H - 34):
        sp.put(sp.ellipse(cx, yy, 7, 3), BRASS[4])
    # lantern on top
    cage = sp.poly([(cx - 14, 14), (cx + 14, 14), (cx + 10, 40), (cx - 10, 40)])
    sp.put(cage, quant(vgrad(sp, 14, 40, 1.0, 0.7), WARM))
    sp.put(sp.rect(cx - 1, 14, 2, 26), BRASS[1])
    sp.put(sp.poly([(cx - 18, 14), (cx + 18, 14), (cx + 6, 4), (cx - 6, 4)]), quant(hgrad(sp, cx - 18, cx + 18, 0.9, 0.3), BRASS, dith))
    sp.put(sp.rect(cx - 12, 39, 24, 4), BRASS[2])
    glow(sp, cx, 27, 34, hexrgb('#ffd37a'), 0.45)
    # bracket arm and the hanging clock
    sp.put(sp.rect(cx, 62, 34, 4), iron[2])
    for t in np.linspace(0, 1, 30):
        sp.put(sp.ellipse(cx + 4 + t * 24, 66 + np.sin(t * np.pi) * 8, 1.4, 1.4), iron[3])
    sp.put(sp.rect(cx + 30, 66, 2, 10), iron[2])
    ccx, ccy, cr = cx + 31, 98, 22
    sp.put(sp.ellipse(ccx, ccy, cr + 4, cr + 4), quant(hgrad(sp, ccx - cr, ccx + cr, 1.0, 0.35), BRASS, dith))
    sp.put(sp.ellipse(ccx, ccy, cr, cr), quant(0.95 - 0.3 * np.clip(np.hypot(sp.xx - ccx + 6, sp.yy - ccy + 6) / (cr * 1.6), 0, 1), FACE, dith))
    for k in range(12):
        a = k * np.pi / 6
        sp.put(sp.ellipse(ccx + np.cos(a) * (cr - 4), ccy + np.sin(a) * (cr - 4), 1.3, 1.3), hexrgb('#2c2236'))
    for a, ln, w in ((np.deg2rad(-150), cr * 0.5, 1.6), (np.deg2rad(-30), cr * 0.78, 1.1)):
        for t in np.linspace(0, ln, 24):
            sp.put(sp.ellipse(ccx + np.cos(a) * t, ccy + np.sin(a) * t, w, w), hexrgb('#2c2236'))
    outline(sp, hexrgb('#0c0e11'), width=1)
    return sp


def gear_big(W=132, H=96):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 10, 60, 8, 0.3)
    g = _gear(sp, cx, H - 22, 56, 11, BRASS, dith, phase=0.4)
    sp.a[sp.yy > H - 16] = 0                                       # sunk into the ground
    # verdigris and moss on the lower teeth
    rng = np.random.default_rng(3)
    vd = g & (noise(H, W, 6, 9) > 0.62)
    sp.rgb[vd] = sp.rgb[vd] * 0.45 + hexrgb('#4f9a86') * 0.55
    for k in range(40):
        x = rng.uniform(cx - 64, cx + 64)
        sp.put(sp.ellipse(x, H - 16 + rng.normal(0, 2), 5, 3.5), LEAF[rng.integers(1, 5)])
    outline(sp, hexrgb('#2a1c0c'), width=2)
    return sp


if __name__ == '__main__':
    import sys
    from pathlib import Path
    out = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp')
    for n, f in (('clock_tower', clock_tower), ('train_car', train_car), ('lamp_clock', lamp_clock), ('gear_big', gear_big)):
        f().save(out / ('%s.png' % n))
        print(n)
