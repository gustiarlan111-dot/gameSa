"""HD landmark sprites for the Plaza (and reusable for town maps): drawn from scratch with the v6 kit
rules (2 texels per world unit, top-left light, coloured outlines, limited ramps).

Every builder returns a Sprite whose bottom-centre is the prop's foot point on the map.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from kit import (Sprite, quant, bayer, sphere_shade, outline, noise, hexrgb, ramp, WOOD, STONE, METAL,
                 PLASTER, BRICK, LEAF, FLOWERS, WATER, BARK)

FONT = Path(__file__).resolve().parents[2] / 'fonts' / 'Inter-Bold.otf'

SIDING_BLUE = ramp('#24395a', '#2f4b73', '#3d608e', '#4f77a6', '#6690bb', '#86abcf', '#a9c6e0')
TRIM = ramp('#6f7276', '#9ea3a6', '#c9cdcd', '#e4e6e3', '#f6f6f1')
SLATE = ramp('#1d2430', '#273141', '#344155', '#43536a', '#56687f', '#6f8399', '#8ea0b3')
TERRA = ramp('#4c1f17', '#6b2c1e', '#8b3c26', '#a84f31', '#c2683f', '#d98a59', '#eaab7c')
GREEN_ROOF = ramp('#1a3430', '#234740', '#2f5c4f', '#3d735e', '#518a6d', '#6ea283', '#90bb9c')
CREAM = ramp('#7a6a52', '#9c8a6c', '#bba985', '#d6c6a0', '#e8dcbb', '#f4ecd4', '#fdf8ea')
SHUTTER_GREEN = ramp('#1c3a2c', '#285240', '#356a52', '#478466', '#5f9d7c')
SHOP_WOOD = ramp('#2c1a14', '#432519', '#5c3320', '#76432a', '#905637', '#ab6d48')
GOLD = ramp('#5a3a10', '#8a5c18', '#b98424', '#dcae3c', '#f2d36c', '#fff0a8')
CURTAIN = {'rose': ramp('#7a3346', '#a04760', '#c4647c', '#e08ea0'),
           'cream': ramp('#9a8564', '#c2ad86', '#e0d0ad', '#f3ead2'),
           'teal': ramp('#1f5056', '#2d6c72', '#3f8a8e', '#63aeb0')}


# ----------------------------------------------------------------------------- helpers

def text_mask(sp, txt, cx, cy, size, font=FONT):
    """Boolean mask of centred text (anti-aliasing thresholded so it stays crisp)."""
    im = Image.new('L', (sp.w, sp.h), 0)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(font), size)
    bb = d.textbbox((0, 0), txt, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), txt, fill=255, font=f)
    return np.asarray(im) > 110


def vgrad(sp, y0, y1, a, b):
    t = np.clip((sp.yy - y0) / max(1, y1 - y0), 0, 1)
    return a + (b - a) * t


def hgrad(sp, x0, x1, a, b):
    t = np.clip((sp.xx - x0) / max(1, x1 - x0), 0, 1)
    return a + (b - a) * t


def darken(sp, m, k):
    sp.rgb[m] = sp.rgb[m] * k


def lighten(sp, m, k, col=(255, 250, 230)):
    c = np.asarray(col, np.float32)
    sp.rgb[m] = sp.rgb[m] * (1 - k) + c * k


def clapboard(sp, m, R, x0, y0, board=11, seed=0):
    """Lap siding: each board lit on top, shadow line under the board above, soft grain."""
    rng = np.random.default_rng(seed)
    row = np.floor((sp.yy - y0) / board).astype(int)
    tone = rng.uniform(-0.05, 0.05, 400)[np.clip(row, 0, 399)]
    pos = ((sp.yy - y0) % board) / board
    grain = (noise(sp.h, sp.w, 3, seed + 4) - 0.5) * 0.08
    v = 0.56 + tone + grain + pos * 0.18 + (pos < 0.18) * -0.22
    sp.put(m, quant(v, R, bayer(sp.h, sp.w)))


def bricks(sp, m, R, x0, y0, bw=24, bh=11, seed=0, mortar=None):
    """Running bond, every brick its own tone, light mortar, worn corners."""
    rng = np.random.default_rng(seed)
    row = np.floor((sp.yy - y0) / bh).astype(int)
    off = (row % 2) * (bw // 2)
    col_i = np.floor((sp.xx - x0 + off) / bw).astype(int)
    key = (row * 131 + col_i * 17) % 997
    tone = rng.uniform(-0.16, 0.12, 1000)[key]
    lx = (sp.xx - x0 + off) % bw
    ly = (sp.yy - y0) % bh
    v = 0.55 + tone + (ly < 3) * 0.08 - (ly > bh - 3) * 0.1 + (noise(sp.h, sp.w, 2, seed + 7) - 0.5) * 0.12
    c = quant(v, R, bayer(sp.h, sp.w))
    mort = (lx < 2) | (ly < 2)
    mc = np.asarray(mortar if mortar is not None else hexrgb('#c9b9a3'), np.float32)
    c[mort] = mc * (0.92 + 0.08 * (noise(sp.h, sp.w, 2, seed)[mort, None]))
    sp.put(m, c)


def plaster(sp, m, R, seed=0, base=0.72):
    n = noise(sp.h, sp.w, 9, seed) - 0.5
    n2 = noise(sp.h, sp.w, 3, seed + 1) - 0.5
    sp.put(m, quant(base + n * 0.12 + n2 * 0.06, R, bayer(sp.h, sp.w)))


def tile_roof(sp, m, R, top, bot, tw=22, th=16, seed=0, moss=0.0, scallop=True):
    """Rows of clay/slate tiles seen from above the eave: each tile rounded, lit at the top, a dark
    gap under every row, per-tile tone and a little moss on the lower rows."""
    rng = np.random.default_rng(seed)
    row = np.floor((sp.yy - top) / th).astype(int)
    off = (row % 2) * (tw // 2)
    ci = np.floor((sp.xx + off) / tw).astype(int)
    key = (row * 71 + ci * 13) % 991
    tone = rng.uniform(-0.1, 0.1, 1000)[key]
    lx = ((sp.xx + off) % tw) / tw
    ly = ((sp.yy - top) % th) / th
    depth = np.clip((sp.yy - top) / max(1, bot - top), 0, 1)
    round_ = 1 - ((lx - 0.5) * 2) ** 2
    v = 0.48 + tone + round_ * 0.2 + (1 - ly) * 0.12 - depth * 0.12 + (lx < 0.5) * 0.04
    gap = ly > 0.82
    if scallop:
        gap = gap | ((ly > 0.62) & (np.abs(lx - 0.5) > 0.5 - (1 - ly) * 1.4))
    c = quant(v, R, bayer(sp.h, sp.w))
    c[gap] = R[0]
    sp.put(m, c)
    sides = (lx < 0.06)
    darken(sp, m & sides & ~gap, 0.86)
    if moss > 0:
        mn = noise(sp.h, sp.w, 6, seed + 9)
        mm = m & (mn > 1 - moss * depth) & ~gap
        sp.rgb[mm] = sp.rgb[mm] * 0.45 + LEAF[3] * 0.55


def window(sp, x, y, w, h, frame=TRIM, curtain='cream', shutters=None, box=True, arch=False, lit=False,
           panes=(2, 2)):
    dith = bayer(sp.h, sp.w)
    # recess shadow + frame
    sp.put(sp.rect(x - 6, y - 6, w + 12, h + 12), frame[1])
    sp.put(sp.rect(x - 5, y - 5, w + 10, h + 10), frame[3])
    sp.put(sp.rect(x - 5, y - 5, w + 10, 2), frame[4])
    glass = sp.rect(x, y, w, h)
    if arch:
        sp.put(sp.ellipse(x + w / 2, y, w / 2 + 5, h * 0.28 + 5) & (sp.yy < y), frame[3])
        glass = glass | (sp.ellipse(x + w / 2, y, w / 2, h * 0.28) & (sp.yy < y))
    g = np.clip((sp.yy - y) / h, 0, 1)
    if lit:
        col = quant(0.95 - g * 0.5, ramp('#b9742c', '#e2a24a', '#f5c86c', '#ffe6a0', '#fff6d6'), dith)
    else:
        col = quant(0.35 + g * 0.25 + ((sp.xx - x) / w) * 0.1, ramp('#20354a', '#2c4c66', '#3f6a86', '#5e8ea8', '#8fb8cc'), dith)
    sp.put(glass, col)
    # interior hint: dark band lower half
    if not lit:
        darken(sp, glass & (sp.yy > y + h * 0.62), 0.82)
    # reflection streaks
    diag = (sp.xx - x) + (sp.yy - y) * 0.9
    refl = glass & (((diag % 46) > 6) & ((diag % 46) < 13) | ((diag % 46) > 17) & ((diag % 46) < 19))
    lighten(sp, refl & (sp.yy < y + h * 0.75), 0.35, (220, 240, 250))
    # curtains
    if curtain:
        C = CURTAIN[curtain]
        cw = max(4, w // 4)
        for cx0, side in ((x, 0), (x + w - cw, 1)):
            cm = sp.rect(cx0, y + 1, cw, h - 2)
            fold = ((sp.xx - cx0) % 5) / 5
            cm = cm & ((sp.xx - cx0 < cw * (0.6 + 0.4 * (1 - (sp.yy - y) / h))) if side == 0
                       else (x + w - sp.xx < cw * (0.6 + 0.4 * (1 - (sp.yy - y) / h))))
            sp.put(cm, quant(0.4 + fold * 0.5, C))
        sp.put(sp.rect(x, y, w, 3), C[0])
    # mullions
    px, py = panes
    for i in range(1, px):
        sp.put(sp.rect(x + w * i // px - 1, y, 3, h), frame[3])
    for j in range(1, py):
        sp.put(sp.rect(x, y + h * j // py - 1, w, 3), frame[3])
    # sill
    sp.put(sp.rect(x - 9, y + h + 4, w + 18, 6), frame[3])
    sp.put(sp.rect(x - 9, y + h + 4, w + 18, 2), frame[4])
    sp.put(sp.rect(x - 7, y + h + 10, w + 14, 2), frame[0])
    if shutters is not None:
        S = shutters
        for sx in (x - 6 - w // 3 - 2, x + w + 8):
            m = sp.rect(sx, y - 5, w // 3, h + 10)
            sp.put(m, quant(0.55 + (((sp.yy - y) % 7) < 2) * -0.25 + hgrad(sp, sx, sx + w // 3, 0.1, -0.1), S))
            sp.put(sp.rect(sx, y - 5, w // 3, 2) & m, S[-1])
    if box:
        bm = sp.rect(x - 7, y + h + 12, w + 14, 14)
        sp.put(bm, quant(vgrad(sp, y + h + 12, y + h + 26, 0.7, 0.3), WOOD))
        rng = np.random.default_rng(int(x * 3 + y * 7))
        for i in range(int((w + 14) / 5)):
            fx = x - 6 + i * 5 + rng.integers(0, 3)
            fy = y + h + 12 - rng.integers(0, 6)
            sp.put(sp.ellipse(fx, fy, 4, 3.5), LEAF[rng.integers(2, 5)])
        for i in range(int((w + 14) / 7)):
            fx = x - 4 + i * 7 + rng.integers(0, 3)
            fy = y + h + 8 - rng.integers(0, 6)
            F = FLOWERS[rng.integers(0, 5)]
            sp.put(sp.ellipse(fx, fy, 2.6, 2.4), F[2])
            sp.put(sp.ellipse(fx - 0.7, fy - 0.7, 1.1, 1.1), F[3])


def door(sp, cx, bot, w, h, R, frame=TRIM, glass=True, arch=False, double=False):
    x = cx - w / 2
    y = bot - h
    sp.put(sp.rect(x - 10, y - 10, w + 20, h + 10), frame[2])
    sp.put(sp.rect(x - 8, y - 8, w + 16, h + 8), frame[3])
    sp.put(sp.rect(x - 8, y - 8, w + 16, 2), frame[4])
    if arch:
        sp.put(sp.ellipse(cx, y, w / 2 + 8, 16) & (sp.yy < y), frame[3])
        sp.put(sp.ellipse(cx, y, w / 2, 10) & (sp.yy < y), hexrgb('#f3d48a'))
    dm = sp.rect(x, y, w, h)
    v = 0.55 + hgrad(sp, x, x + w, 0.12, -0.12)
    sp.put(dm, quant(v, R))
    # panels
    n = 2 if double else 1
    pw = w / n
    for i in range(n):
        px0 = x + i * pw
        for (py0, ph) in ((y + 10, h * 0.38), (y + h * 0.55, h * 0.36)):
            pm = sp.rect(px0 + 7, py0, pw - 14, ph)
            darken(sp, pm, 0.85)
            sp.put(sp.rect(px0 + 7, py0, pw - 14, 2) & pm, R[-1] if len(R) > 4 else R[3])
            darken(sp, sp.rect(px0 + 7, py0 + ph - 2, pw - 14, 2), 0.7)
        if glass:
            gm = sp.rect(px0 + 10, y + 13, pw - 20, h * 0.32)
            sp.put(gm, quant(vgrad(sp, y, y + h * 0.4, 0.8, 0.4), ramp('#2c4c66', '#3f6a86', '#5e8ea8', '#8fb8cc', '#c4e0ea')))
    if double:
        sp.put(sp.rect(cx - 1, y, 2, h), R[0])
    kx = cx + (w / 2 - 9 if not double else 7)
    sp.put(sp.ellipse(kx, y + h * 0.55, 3, 3), GOLD[4])
    sp.put(sp.ellipse(kx + 0.8, y + h * 0.55 + 0.8, 1.5, 1.5), GOLD[2])


def wall_lamp(sp, x, y, lit=True):
    sp.put(sp.rect(x - 2, y - 6, 4, 10), METAL[2])
    sp.put(sp.rect(x - 7, y + 2, 14, 18), METAL[1])
    sp.put(sp.rect(x - 5, y + 4, 10, 14), hexrgb('#ffe3a0') if lit else hexrgb('#9aa6a8'))
    sp.put(sp.poly([(x - 9, y + 3), (x + 9, y + 3), (x + 5, y - 3), (x - 5, y - 3)]), METAL[2])


def potted_plant(sp, cx, bot, s=1.0, seed=0, flowers=True):
    rng = np.random.default_rng(seed)
    pw, ph = 24 * s, 20 * s
    pot = sp.poly([(cx - pw / 2, bot - ph), (cx + pw / 2, bot - ph), (cx + pw / 2 - 4 * s, bot), (cx - pw / 2 + 4 * s, bot)])
    sp.put(pot, quant(hgrad(sp, cx - pw / 2, cx + pw / 2, 0.8, 0.3), ramp('#5a2a1a', '#7a3a22', '#9c4e2c', '#bb6638', '#d2814c')))
    sp.put(sp.rect(cx - pw / 2 - 2, bot - ph - 4 * s, pw + 4, 5 * s), hexrgb('#c2683f'))
    for i in range(int(16 * s)):
        a = rng.uniform(np.pi * 1.05, np.pi * 1.95)
        r = rng.uniform(4, 16) * s
        x = cx + np.cos(a) * r
        y = bot - ph - 4 * s + np.sin(a) * r * 0.9
        sp.put(sp.ellipse(x, y, 5 * s, 4 * s), LEAF[rng.integers(2, 6)])
    if flowers:
        F = FLOWERS[seed % 5]
        for i in range(int(7 * s)):
            a = rng.uniform(np.pi * 1.1, np.pi * 1.9)
            r = rng.uniform(3, 13) * s
            sp.put(sp.ellipse(cx + np.cos(a) * r, bot - ph - 6 * s + np.sin(a) * r * 0.9, 2.6 * s, 2.4 * s), F[2])


def shrub_row(sp, x0, x1, bot, seed=0, R=LEAF, hmax=26):
    rng = np.random.default_rng(seed)
    dith = bayer(sp.h, sp.w)
    for i in range(int((x1 - x0) / 9)):
        x = x0 + i * 9 + rng.uniform(-3, 3)
        r = rng.uniform(10, 16)
        y = bot - r * 0.7 - rng.uniform(0, hmax - 16)
        m = sp.ellipse(x, y, r, r * 0.85)
        sp.put(m, quant(sphere_shade(sp, x - 2, y - 3, r, r * 0.85) * 0.9 + (noise(sp.h, sp.w, 3, seed + i) - 0.5) * 0.3, R, dith))


def gutter(sp, x0, x1, y, R=METAL):
    sp.put(sp.rect(x0, y, x1 - x0, 7), R[3])
    sp.put(sp.rect(x0, y, x1 - x0, 2), R[5])
    sp.put(sp.rect(x0, y + 6, x1 - x0, 2), R[1])


def downpipe(sp, x, y0, y1, R=METAL):
    sp.put(sp.rect(x, y0, 7, y1 - y0), quant(hgrad(sp, x, x + 7, 0.85, 0.3), R))
    for yy in range(int(y0) + 30, int(y1), 46):
        sp.put(sp.rect(x - 1, yy, 9, 3), R[1])


def chimney(sp, x, y, w, h, R=BRICK):
    m = sp.rect(x, y, w, h)
    bricks(sp, m, R, x, y, 14, 8, seed=x)
    darken(sp, m & (sp.xx > x + w * 0.6), 0.78)
    sp.put(sp.rect(x - 5, y - 2, w + 10, 9), STONE[4])
    sp.put(sp.rect(x - 5, y - 2, w + 10, 2), STONE[6])
    sp.put(sp.rect(x + 6, y - 8, 9, 7) | sp.rect(x + w - 15, y - 8, 9, 7), hexrgb('#9c4e2c'))


def ground_shadow(sp, cx, cy, rx, ry, k=0.32):
    """Soft contact shadow painted as translucent dark below the sprite."""
    d = ((sp.xx - cx) / rx) ** 2 + ((sp.yy - cy) / ry) ** 2
    a = np.clip(1 - d, 0, 1) ** 0.8 * k
    free = sp.a < 0.05
    sp.rgb[free] = np.asarray(hexrgb('#1a2418'), np.float32)
    sp.a[free] = np.maximum(sp.a[free], a[free])


# ----------------------------------------------------------------------------- houses

_HOUSE_NO = [None]


def house(kind='arland', W=600, H=500):
    """Front elevation in 3/4 top-down view: roof slope seen from above, front wall, porch, garden
    strip. Footprint (cw*2 px) is centred; the door sits at the exact horizontal centre."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    bot = H - 4
    if kind == 'arland':
        wallR, roofR, trimR, x0, x1 = SIDING_BLUE, SLATE, TRIM, 52, W - 52
        wall_top = 262
    elif kind == 'sofia':
        wallR, roofR, trimR, x0, x1 = BRICK, TERRA, CREAM, 42, W - 42
        wall_top = 258
    else:
        wallR, roofR, trimR, x0, x1 = CREAM, GREEN_ROOF, TRIM, 46, W - 46
        wall_top = 250
    found = 22
    wall_bot = bot - found
    ground_shadow(sp, cx, bot - 4, (x1 - x0) / 2 + 30, 16, 0.38)
    # --- foundation (cut stone)
    fm = sp.rect(x0 - 6, wall_bot, x1 - x0 + 12, found)
    rng = np.random.default_rng(len(kind))
    sp.put(fm, quant(0.5 + (noise(H, W, 4, 3) - 0.5) * 0.3, STONE, dith))
    for xx in np.arange(x0 - 6, x1 + 6, 34):
        sp.put(sp.rect(xx + rng.integers(0, 6), wall_bot, 2, found), STONE[1])
    sp.put(sp.rect(x0 - 6, wall_bot + found // 2, x1 - x0 + 12, 2), STONE[1])
    sp.put(sp.rect(x0 - 8, wall_bot - 2, x1 - x0 + 16, 5), STONE[5])
    # --- front wall
    wm = sp.rect(x0, wall_top, x1 - x0, wall_bot - wall_top)
    if kind == 'arland':
        clapboard(sp, wm, wallR, x0, wall_top, 11, 5)
    elif kind == 'sofia':
        bricks(sp, wm, wallR, x0, wall_top, 26, 12, 7)
    else:
        plaster(sp, wm, wallR, 9, 0.7)
        # lower half wood panelling
        pm = sp.rect(x0, wall_bot - 52, x1 - x0, 52)
        sp.put(pm, quant(0.5 + ((sp.xx - x0) % 30 < 2) * -0.25 + vgrad(sp, wall_bot - 52, wall_bot, 0.1, -0.1), SHOP_WOOD, dith))
        sp.put(sp.rect(x0, wall_bot - 54, x1 - x0, 5), SHOP_WOOD[4])
    # corner boards / quoins
    for qx in (x0, x1 - 14):
        if kind == 'sofia':
            for k, yy in enumerate(range(wall_top, int(wall_bot), 22)):
                ww = 22 if k % 2 == 0 else 14
                qq = sp.rect(qx if qx == x0 else x1 - ww, yy, ww, 20)
                sp.put(qq, quant(0.68 + (noise(H, W, 3, k) - 0.5) * 0.2, CREAM, dith))
                sp.put(sp.rect(qx if qx == x0 else x1 - ww, yy + 19, ww, 2), CREAM[1])
        else:
            sp.put(sp.rect(qx, wall_top, 14, wall_bot - wall_top), trimR[3])
            sp.put(sp.rect(qx, wall_top, 3, wall_bot - wall_top), trimR[4])
            sp.put(sp.rect(qx + 11, wall_top, 3, wall_bot - wall_top), trimR[1])
    # frieze board under the eave
    sp.put(sp.rect(x0, wall_top, x1 - x0, 12), trimR[3])
    sp.put(sp.rect(x0, wall_top + 10, x1 - x0, 2), trimR[1])
    # eave shadow onto the wall (ambient occlusion)
    ao = wm & (sp.yy < wall_top + 34)
    sp.rgb[ao] = sp.rgb[ao] * (0.62 + 0.38 * ((sp.yy[ao] - wall_top) / 34))[:, None]
    # --- door + porch
    if kind == 'cafe':
        dw, dh = 96, 138
    else:
        dw, dh = 72, 132
    doorR = {'arland': ramp('#3a2a1e', '#56392a', '#714b36', '#8c5f44', '#a87756'),
             'sofia': SHUTTER_GREEN, 'cafe': SHOP_WOOD}[kind]
    door(sp, cx, wall_bot, dw, dh, doorR, trimR, glass=True, arch=(kind == 'sofia'), double=(kind == 'cafe'))
    # steps
    for i, (sw, sh_) in enumerate(((dw + 52, 9), (dw + 36, 9))):
        sy = bot - 9 * (i + 1) - 1
        st = sp.rect(cx - sw / 2, sy, sw, sh_)
        sp.put(st, quant(0.62 - i * 0.05 + hgrad(sp, cx - sw / 2, cx + sw / 2, 0.08, -0.12), STONE, dith))
        sp.put(sp.rect(cx - sw / 2, sy, sw, 2), STONE[6])
    # doormat
    sp.put(sp.rect(cx - dw / 2 + 6, wall_bot - 5, dw - 12, 5), hexrgb('#8a5a3a'))
    # porch canopy with brackets
    if kind != 'cafe':
        py = wall_bot - dh - 30
        can = sp.poly([(cx - dw / 2 - 30, py + 22), (cx + dw / 2 + 30, py + 22), (cx + dw / 2 + 20, py), (cx - dw / 2 - 20, py)])
        tile_roof(sp, can, roofR, py, py + 22, 14, 8, seed=11, scallop=False)
        sp.put(sp.rect(cx - dw / 2 - 30, py + 20, dw + 60, 5), roofR[0])
        for bx in (cx - dw / 2 - 18, cx + dw / 2 + 12):
            sp.put(sp.poly([(bx, py + 24), (bx + 6, py + 24), (bx + 6, py + 44)]), WOOD[2])
        wall_lamp(sp, cx + dw / 2 + 26, wall_bot - dh + 12)
        # house number plate
        sp.put(sp.rect(cx - dw / 2 - 34, wall_bot - dh + 20, 20, 14), trimR[3])
        sp.put(text_mask(sp, _HOUSE_NO[0] or ('7' if kind == 'arland' else '9'), cx - dw / 2 - 24, wall_bot - dh + 27, 11), hexrgb('#2b2b30'))
    # windows
    wy = wall_top + 64
    if kind == 'arland':
        for wx in (x0 + 52, x1 - 52 - 74):
            window(sp, wx, wy, 74, 74, TRIM, 'cream', shutters=ramp('#3a3e4a', '#4a5262', '#5e6878', '#7a8494', '#98a2b0'), panes=(2, 2))
        potted_plant(sp, cx - dw / 2 - 26, bot - 2, 1.1, 1)
        potted_plant(sp, cx + dw / 2 + 26, bot - 2, 0.9, 3)
        downpipe(sp, x1 - 6, wall_top + 4, wall_bot)
    elif kind == 'sofia':
        for wx in (x0 + 50, x1 - 50 - 70):
            window(sp, wx, wy + 6, 70, 80, CREAM, 'rose', shutters=SHUTTER_GREEN, arch=True, panes=(2, 3))
        potted_plant(sp, cx - dw / 2 - 28, bot - 2, 1.0, 0)
        potted_plant(sp, cx + dw / 2 + 28, bot - 2, 1.15, 2)
        downpipe(sp, x0 - 2, wall_top + 4, wall_bot)
    else:
        # shop windows, warm lit interior, gold lettering on the glass
        for wx, ww in ((x0 + 32, 150), (x1 - 32 - 150, 150)):
            sp.put(sp.rect(wx - 10, wall_top + 52, ww + 20, wall_bot - wall_top - 58), SHOP_WOOD[1])
            window(sp, wx, wall_top + 60, ww, 120, ramp('#2c1a14', '#432519', '#5c3320', '#76432a', '#905637'),
                   curtain=None, box=False, lit=True, panes=(3, 1))
            # silhouettes of cups/shelves inside
            for k in range(5):
                sp.put(sp.rect(wx + 12 + k * 28, wall_top + 140, 14, 14), hexrgb('#b86c34'))
            sp.put(sp.rect(wx + 4, wall_top + 156, ww - 8, 4), hexrgb('#7a4426'))
        # striped awning over the whole front
        ay0, ay1 = wall_top + 14, wall_top + 58
        aw = sp.poly([(x0 - 14, ay1), (x1 + 14, ay1), (x1 + 4, ay0), (x0 - 4, ay0)])
        stripe = (((sp.xx - x0) // 26) % 2 == 0)
        a0 = quant(vgrad(sp, ay0, ay1, 0.85, 0.45), ramp('#7a2a1a', '#a33d22', '#c95a2c', '#e57d3e', '#f4a462'))
        a1 = quant(vgrad(sp, ay0, ay1, 0.85, 0.45), CREAM)
        sp.put(aw, np.where(stripe[..., None], a0, a1))
        for xx in range(int(x0 - 14), int(x1 + 14), 26):
            lip = sp.ellipse(xx + 13, ay1, 13, 9) & (sp.yy >= ay1)
            sp.put(lip, a0 if ((xx - x0) // 26) % 2 == 0 else a1)
        darken(sp, sp.rect(x0, ay1 + 8, x1 - x0, 14) & wm, 0.7)
        # menu board by the door
        mx = cx + dw / 2 + 40
        sp.put(sp.poly([(mx, bot - 4), (mx + 36, bot - 4), (mx + 30, bot - 70), (mx + 6, bot - 70)]), WOOD[2])
        sp.put(sp.rect(mx + 9, bot - 64, 18, 52), hexrgb('#243028'))
        for k in range(5):
            sp.put(sp.rect(mx + 12, bot - 58 + k * 9, 8 + (k * 5) % 7, 2), hexrgb('#e8e2cf'))
        potted_plant(sp, cx - dw / 2 - 26, bot - 2, 1.2, 4)
        wall_lamp(sp, cx - dw / 2 - 10, wall_top + 74)
        wall_lamp(sp, cx + dw / 2 + 10, wall_top + 74)
    # --- roof
    r_top = 40
    over = 26
    roof_poly = [(x0 - over, wall_top + 6), (x1 + over, wall_top + 6), (x1 - 34, r_top), (x0 + 34, r_top)]
    rm = sp.poly(roof_poly)
    tile_roof(sp, rm, roofR, r_top, wall_top + 6, 24 if kind != 'arland' else 20, 18 if kind != 'arland' else 14,
              seed=3 + len(kind), moss=0.35 if kind == 'sofia' else 0.18, scallop=(kind != 'arland'))
    # roof side light falloff (right side in shadow)
    darken(sp, rm & (sp.xx > cx), 0.95)
    darken(sp, rm & (sp.xx > x1 - 40), 0.9)
    # ridge cap
    rc = sp.rect(x0 + 30, r_top - 8, x1 - x0 - 60, 12)
    sp.put(rc, quant(hgrad(sp, x0, x1, 0.85, 0.4), roofR))
    sp.put(sp.rect(x0 + 30, r_top - 8, x1 - x0 - 60, 3), roofR[-1])
    # bargeboards on the hip edges
    for (ax, ay), (bx, by) in (((x0 - over, wall_top + 6), (x0 + 34, r_top)), ((x1 + over, wall_top + 6), (x1 - 34, r_top))):
        for t in np.linspace(0, 1, 160):
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            sp.put(sp.ellipse(px, py, 4, 4), roofR[1] if ax > cx else roofR[4])
    # fascia + gutter
    sp.put(sp.rect(x0 - over, wall_top + 2, x1 - x0 + 2 * over, 8), trimR[2])
    gutter(sp, x0 - over + 4, x1 + over - 4, wall_top + 8)
    # dormer / feature
    if kind == 'arland':
        dx0 = x0 + 92
        dm = sp.rect(dx0, 112, 96, 92)
        clapboard(sp, dm, wallR, dx0, 112, 10, 9)
        window(sp, dx0 + 22, 136, 52, 50, TRIM, 'teal', box=False, panes=(2, 2))
        droof = sp.poly([(dx0 - 14, 122), (dx0 + 48, 82), (dx0 + 110, 122)])
        darken(sp, sp.poly([(dx0 - 20, 126), (dx0 + 48, 86), (dx0 + 120, 130), (dx0 + 104, 214), (dx0 + 96, 214)]) & rm & ~dm, 0.72)
        tile_roof(sp, droof, roofR, 82, 122, 16, 10, seed=21, scallop=False)
        lighten(sp, droof & (sp.xx < dx0 + 48), 0.12)
        sp.put(sp.poly([(dx0 - 16, 124), (dx0 + 48, 80), (dx0 + 112, 124), (dx0 + 104, 126), (dx0 + 48, 88), (dx0 - 8, 126)]), TRIM[3])
        darken(sp, sp.rect(dx0, 122, 96, 10) & dm, 0.7)
        chimney(sp, x1 - 140, 14, 40, 70)
        # a small satellite-free detail: weather vane
        sp.put(sp.rect(cx + 40, 6, 3, 30), METAL[2])
        sp.put(sp.poly([(cx + 30, 12), (cx + 56, 12), (cx + 52, 18), (cx + 30, 18)]), METAL[4])
    elif kind == 'sofia':
        # round attic window in a little gable
        gx = cx
        gm = sp.poly([(gx - 70, 186), (gx, 98), (gx + 70, 186)])
        bricks(sp, gm, BRICK, gx - 70, 98, 20, 10, 13)
        sp.put(sp.ellipse(gx, 158, 22, 22), CREAM[3])
        sp.put(sp.ellipse(gx, 158, 17, 17), quant(vgrad(sp, 140, 176, 0.8, 0.3), ramp('#2c4c66', '#3f6a86', '#5e8ea8', '#8fb8cc')))
        sp.put(sp.rect(gx - 1, 141, 3, 34) | sp.rect(gx - 17, 157, 34, 3), CREAM[3])
        groof = sp.poly([(gx - 86, 192), (gx, 88), (gx + 86, 192), (gx + 70, 192), (gx, 108), (gx - 70, 192)])
        sp.put(groof, quant(hgrad(sp, gx - 86, gx + 86, 0.8, 0.35), TERRA))
        chimney(sp, x0 + 70, 18, 38, 64)
        # climbing ivy on the left corner
        rngv = np.random.default_rng(17)
        for k in range(220):
            t = rngv.uniform(0, 1)
            yy = wall_bot - t * (wall_bot - wall_top - 30)
            xx = x0 + 6 + rngv.normal(0, 14) * (0.4 + t)
            sp.put(sp.ellipse(xx, yy, 4, 3.4), LEAF[rngv.integers(1, 5)])
    else:
        # cafe sign board on the roof front
        sy0 = 142
        sp.put(sp.rect(cx - 150, sy0 - 4, 300, 62), SHOP_WOOD[0])
        sm = sp.rect(cx - 144, sy0, 288, 54)
        sp.put(sm, quant(vgrad(sp, sy0, sy0 + 54, 0.7, 0.35) + ((sp.yy - sy0) % 9 < 1) * -0.1, SHOP_WOOD))
        sp.put(sp.rect(cx - 144, sy0, 288, 3), SHOP_WOOD[5])
        tm = text_mask(sp, 'KAFE SENJA', cx + 1, sy0 + 29, 34)
        sp.put(np.roll(np.roll(tm, 2, 0), 2, 1), SHOP_WOOD[0])
        sp.put(tm, quant(vgrad(sp, sy0 + 10, sy0 + 46, 0.95, 0.55), GOLD))
        # coffee cup emblem
        for ex in (cx - 168, cx + 168):
            sp.put(sp.ellipse(ex, sy0 + 27, 20, 20), SHOP_WOOD[1])
            sp.put(sp.ellipse(ex, sy0 + 27, 16, 16), CREAM[4])
            sp.put(sp.rect(ex - 8, sy0 + 22, 14, 12), hexrgb('#7a4426'))
            sp.put(sp.ellipse(ex + 7, sy0 + 28, 4, 4) & ~sp.ellipse(ex + 7, sy0 + 28, 2, 2), hexrgb('#7a4426'))
            sp.put(sp.rect(ex - 5, sy0 + 13, 2, 6) | sp.rect(ex + 1, sy0 + 11, 2, 7), CREAM[1])
        chimney(sp, x1 - 120, 18, 36, 60, STONE)
        # string lights along the fascia
        for k, xx in enumerate(range(int(x0 - 10), int(x1 + 10), 22)):
            yy = wall_top + 20 + 5 * np.sin(k * 0.9)
            sp.put(sp.ellipse(xx, yy, 3.4, 3.4), hexrgb(['#ffe39a', '#ffc56e', '#ffefc0'][k % 3]))
    outline(sp, roofR[0] * 0.75, width=2)
    return sp


# ----------------------------------------------------------------------------- water features

def fountain_grand(W=460, H=360):
    """Big two-tier plaza fountain; basin centre sits ~100px above the foot (world 50)."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    by = H - 96                      # basin centre
    rx, ry = W / 2 - 14, 86
    ground_shadow(sp, cx, by + 40, rx + 10, ry * 0.75, 0.35)
    # outer basin wall (front face visible)
    face = sp.ellipse(cx, by + 26, rx, ry) & ~sp.ellipse(cx, by - 2, rx, ry) | (sp.ellipse(cx, by + 26, rx, ry) & (sp.yy > by))
    blocks = ((np.arctan2(sp.yy - by, (sp.xx - cx) / 1.6) * 10).astype(int) % 2 == 0)
    sp.put(face, quant(0.5 + hgrad(sp, cx - rx, cx + rx, 0.18, -0.2) + blocks * 0.05, STONE, dith))
    ang = np.arctan2((sp.yy - by - 26) / ry, (sp.xx - cx) / rx)
    seams = face & ((np.abs(((ang * 12 / np.pi) % 1) - 0.5) < 0.04))
    darken(sp, seams, 0.75)
    # rim (top surface)
    rim = sp.ellipse(cx, by, rx, ry) & ~sp.ellipse(cx, by, rx - 22, ry - 15)
    sp.put(rim, quant(0.78 + (noise(H, W, 3, 4) - 0.5) * 0.15 + vgrad(sp, by - ry, by + ry, 0.05, -0.2), STONE, dith))
    sp.put(sp.ellipse(cx, by, rx, ry) & ~sp.ellipse(cx, by + 2, rx - 2, ry - 1) & (sp.yy < by), STONE[6])
    # water
    wm = sp.ellipse(cx, by, rx - 22, ry - 15)
    rip = np.sin(np.sqrt(((sp.xx - cx) / 1.7) ** 2 + (sp.yy - by) ** 2 * 1.0) * 0.32) * 0.5 + 0.5
    sp.put(wm, quant(0.45 + vgrad(sp, by - ry, by + ry, -0.15, 0.2) + rip * 0.05 + (noise(H, W, 5, 8) - 0.5) * 0.14, WATER, dith))
    darken(sp, wm & ~sp.ellipse(cx, by + 6, rx - 30, ry - 20) & (sp.yy < by), 0.78)   # rim shadow on water
    hi = wm & (rip > 0.97) & (noise(H, W, 2, 11) > 0.55)
    lighten(sp, hi, 0.6, (230, 246, 250))
    # lily pads + coins
    rng = np.random.default_rng(6)
    for k in range(5):
        a = rng.uniform(0, 2 * np.pi)
        lx, ly = cx + np.cos(a) * (rx - 60), by + np.sin(a) * (ry - 34)
        sp.put(sp.ellipse(lx, ly, 13, 7) & ~(sp.poly([(lx, ly), (lx + 14, ly - 3), (lx + 14, ly + 3)])), LEAF[3 + k % 2])
        if k % 2 == 0:
            sp.put(sp.ellipse(lx - 3, ly - 2, 3.5, 3), FLOWERS[0][3])
    # central pedestal
    pm = sp.poly([(cx - 34, by + 10), (cx + 34, by + 10), (cx + 20, by - 96), (cx - 20, by - 96)])
    sp.put(pm, quant(hgrad(sp, cx - 34, cx + 34, 0.85, 0.25) + (noise(H, W, 3, 2) - 0.5) * 0.08, STONE, dith))
    for yy in (by - 20, by - 60):
        sp.put(sp.rect(cx - 30, yy, 60, 5), STONE[2])
    sp.put(sp.ellipse(cx, by + 10, 36, 9) & (sp.yy > by + 6), hexrgb('#d8eef2'))   # foam ring at the base
    # upper bowl
    uy = by - 118
    bowl = sp.ellipse(cx, uy + 10, 92, 30) & (sp.yy > uy)
    sp.put(bowl, quant(hgrad(sp, cx - 92, cx + 92, 0.8, 0.25) + vgrad(sp, uy, uy + 40, 0.1, -0.15), STONE, dith))
    sp.put(sp.ellipse(cx, uy, 92, 22), STONE[5])
    sp.put(sp.ellipse(cx, uy + 1, 80, 17), quant(vgrad(sp, uy - 17, uy + 17, 0.35, 0.75), WATER, dith))
    # spray column and crown
    sm_ = sp.rect(cx - 6, uy - 92, 12, 92)
    sp.put(sm_, quant(hgrad(sp, cx - 6, cx + 6, 0.95, 0.6), WATER))
    sp.put(sp.ellipse(cx, uy - 94, 14, 9), hexrgb('#eaf7fa'))
    # falling sheets from the bowl lip (translucent streaks)
    for k, a in enumerate(np.linspace(0.15, np.pi - 0.15, 9)):
        sx = cx + np.cos(a) * 88
        top = uy + 10 + np.sin(a) * 26
        streak = sp.rect(sx - 2, top, 4, by - 10 - top + np.sin(a) * 30)
        sp.rgb[streak] = sp.rgb[streak] * 0.4 + np.array([200, 232, 240]) * 0.6
        sp.a[streak] = np.maximum(sp.a[streak], 0.8)
    # arcs from crown to bowl
    for side in (-1, 1):
        for t in np.linspace(0, 1, 50):
            x = cx + side * t * 74
            y = uy - 94 + (t * 2.2 - 1.2) ** 2 * 40 - 8
            sp.put(sp.ellipse(x, y, 2.4, 2.4), hexrgb('#d2eef4'), 0.85)
    # splash dots in basin
    for k in range(60):
        a = rng.uniform(0, 2 * np.pi)
        r = rng.uniform(0.55, 0.75)
        sp.put(sp.ellipse(cx + np.cos(a) * 92 * r * 1.2, by + np.sin(a) * 30 * r, 1.8, 1.4), hexrgb('#eaf7fa'))
    outline(sp, STONE[0], width=2)
    return sp


def fountain_tiered(W=240, H=200):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 16, 80, 18)
    # octagonal base basin
    by = H - 46
    face = sp.rect(cx - 96, by, 192, 34) & ~(sp.xx < cx - 96 + (sp.yy - by) * 0)
    sp.put(face, quant(hgrad(sp, cx - 96, cx + 96, 0.75, 0.3) + (((sp.xx - cx) % 32) < 2) * -0.2, STONE, dith))
    top = sp.ellipse(cx, by, 98, 30)
    sp.put(top, STONE[5])
    sp.put(sp.ellipse(cx, by + 1, 84, 22), quant(vgrad(sp, by - 22, by + 22, 0.35, 0.75), WATER, dith))
    # three tiers
    for i, (r, y) in enumerate(((60, by - 54), (40, by - 98), (22, by - 132))):
        sp.put(sp.rect(cx - 10 + i * 2, y, 20 - i * 4, (by if i == 0 else y + 44) - y), quant(hgrad(sp, cx - 10, cx + 10, 0.85, 0.3), STONE))
        sp.put(sp.ellipse(cx, y + 8, r, r * 0.32) & (sp.yy > y), quant(hgrad(sp, cx - r, cx + r, 0.8, 0.3), STONE, dith))
        sp.put(sp.ellipse(cx, y, r, r * 0.28), STONE[5])
        sp.put(sp.ellipse(cx, y + 1, r - 6, r * 0.2), WATER[4])
        for a in np.linspace(0.3, np.pi - 0.3, 5):
            sx = cx + np.cos(a) * (r - 2)
            st = sp.rect(sx - 1, y + 8, 3, 34 if i else 44)
            sp.rgb[st] = sp.rgb[st] * 0.35 + np.array([205, 235, 242]) * 0.65
            sp.a[st] = np.maximum(sp.a[st], 0.8)
    sp.put(sp.ellipse(cx, by - 146, 6, 9), hexrgb('#eaf7fa'))
    outline(sp, STONE[0], width=2)
    return sp


def birdbath(W=184, H=142):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 10, 50, 12)
    sp.put(sp.poly([(cx - 34, H - 8), (cx + 34, H - 8), (cx + 24, H - 22), (cx - 24, H - 22)]), quant(hgrad(sp, cx - 34, cx + 34, 0.8, 0.3), STONE, dith))
    stem = sp.poly([(cx - 14, H - 22), (cx + 14, H - 22), (cx + 9, 64), (cx - 9, 64)])
    sp.put(stem, quant(hgrad(sp, cx - 14, cx + 14, 0.85, 0.3), STONE, dith))
    for yy in (H - 50, 84):
        sp.put(sp.ellipse(cx, yy, 15, 4), STONE[3])
    sp.put(sp.ellipse(cx, 58, 70, 22) & (sp.yy > 46), quant(hgrad(sp, cx - 70, cx + 70, 0.8, 0.3), STONE, dith))
    sp.put(sp.ellipse(cx, 46, 72, 18), STONE[5])
    sp.put(sp.ellipse(cx, 47, 60, 12), quant(vgrad(sp, 35, 59, 0.3, 0.8), WATER, dith))
    # moss & a little bird on the rim
    rng = np.random.default_rng(2)
    for k in range(30):
        x = cx + rng.uniform(-60, 60)
        y = 58 + rng.uniform(-3, 12)
        sp.put(sp.ellipse(x, y, 3, 2), LEAF[rng.integers(2, 5)])
    bx, byy = cx + 44, 34
    sp.put(sp.ellipse(bx, byy, 10, 7), hexrgb('#8a5a3a'))
    sp.put(sp.ellipse(bx + 2, byy + 2, 7, 4), hexrgb('#e9c79a'))
    sp.put(sp.ellipse(bx - 8, byy - 6, 6, 5.5), hexrgb('#7a4a2c'))
    sp.put(sp.poly([(bx - 14, byy - 6), (bx - 19, byy - 4), (bx - 14, byy - 3)]), hexrgb('#e7a73a'))
    sp.put(sp.ellipse(bx - 9, byy - 7, 1.4, 1.4), hexrgb('#101010'))
    sp.put(sp.poly([(bx + 8, byy - 2), (bx + 20, byy - 8), (bx + 18, byy + 1)]), hexrgb('#5a3826'))
    outline(sp, STONE[0], width=2)
    return sp


# ----------------------------------------------------------------------------- street furniture

def mural_wall(painted=False, W=240, H=184):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 8, W / 2, 12)
    x0, x1, top, bot = 8, W - 8, 30, H - 10
    wm = sp.rect(x0, top, x1 - x0, bot - top)
    bricks(sp, wm, BRICK, x0, top, 22, 10, 31)
    # coping stones
    sp.put(sp.rect(x0 - 6, top - 12, x1 - x0 + 12, 14), quant(vgrad(sp, top - 12, top + 2, 0.85, 0.5), STONE, dith))
    for xx in range(x0 - 6, x1 + 6, 30):
        sp.put(sp.rect(xx, top - 12, 2, 14), STONE[2])
    # plaster panel
    pm = sp.rect(x0 + 14, top + 12, x1 - x0 - 28, bot - top - 34)
    if painted:
        t = (sp.yy - (top + 12)) / (bot - top - 34)
        sky = quant(0.9 - t * 0.7, ramp('#3b2c6a', '#5d3f8a', '#a35a8f', '#e0866e', '#f6b86a', '#fde0a0'), dith)
        sp.put(pm, sky)
        # stars
        rng = np.random.default_rng(9)
        for k in range(26):
            x = rng.uniform(x0 + 20, x1 - 20); y = rng.uniform(top + 16, top + 60)
            sp.put(sp.ellipse(x, y, 1.6, 1.6), hexrgb('#fff6d0'))
        # moon
        sp.put(sp.ellipse(x1 - 54, top + 36, 13, 13) & ~sp.ellipse(x1 - 48, top + 32, 11, 11), hexrgb('#fff0b8'))
        # rolling hills + town roofs
        hills = pm & (sp.yy > top + 92 + 10 * np.sin(sp.xx * 0.04))
        sp.put(hills, quant(vgrad(sp, top + 90, bot, 0.7, 0.3), LEAF, dith))
        hills2 = pm & (sp.yy > top + 108 + 8 * np.sin(sp.xx * 0.07 + 2))
        sp.put(hills2, quant(vgrad(sp, top + 100, bot, 0.5, 0.2), LEAF_DARK_(), dith))
        # two small figures holding hands under a heart-shaped kite
        for fx, c in ((W / 2 - 12, '#3d608e'), (W / 2 + 12, '#c4647c')):
            sp.put(sp.ellipse(fx, top + 96, 5, 5), hexrgb('#f1c9a5'))
            sp.put(sp.poly([(fx - 6, top + 118), (fx + 6, top + 118), (fx + 4, top + 101), (fx - 4, top + 101)]), hexrgb(c))
        sp.put(sp.rect(W / 2 - 8, top + 108, 16, 2), hexrgb('#f1c9a5'))
        hx, hy = W / 2 + 34, top + 46
        heart = sp.ellipse(hx - 5, hy, 6, 6) | sp.ellipse(hx + 5, hy, 6, 6) | sp.poly([(hx - 11, hy + 1), (hx + 11, hy + 1), (hx, hy + 14)])
        sp.put(heart, hexrgb('#ee6a7a'))
        for k in range(30):
            sp.put(sp.ellipse(hx - k * 1.3, hy + 14 + k * 1.6, 0.8, 0.8), hexrgb('#fff0d8'))
        # paint drips + signature
        for k in range(6):
            sp.put(sp.rect(x0 + 30 + k * 30, bot - 22, 2, 4 + k % 3 * 3), hexrgb(['#e0866e', '#5d3f8a', '#4f8a47'][k % 3]))
    else:
        plaster(sp, pm, PLASTER, 41, 0.6)
        # faded old mural: washed-out shapes + peeling patches
        ghost = pm & (sp.yy > top + 92 + 10 * np.sin(sp.xx * 0.04))
        sp.rgb[ghost] = sp.rgb[ghost] * 0.85 + np.array([120, 150, 120]) * 0.15
        peel = pm & (noise(H, W, 7, 5) > 0.8)
        bricks(sp, peel, BRICK, x0, top, 22, 10, 31)
        cracks = pm & (np.abs(noise(H, W, 11, 8) - 0.5) < 0.012)
        darken(sp, cracks, 0.6)
        # sketch lines left by a painter
        for k in range(3):
            yy = top + 40 + k * 22
            sp.put(sp.rect(x0 + 40, yy, 60 + k * 18, 1), hexrgb('#8f8577'))
    sp.put(sp.rect(x0 + 14, top + 12, x1 - x0 - 28, 2), STONE[2])
    # base plinth
    sp.put(sp.rect(x0 - 4, bot - 10, x1 - x0 + 8, 12), quant(0.55 + hgrad(sp, x0, x1, 0.1, -0.1), STONE, dith))
    # weeds at the foot
    shrub_row(sp, x0, x0 + 40, bot + 2, 4, hmax=18)
    shrub_row(sp, x1 - 30, x1, bot + 2, 5, hmax=16)
    outline(sp, BRICK[0] * 0.8, width=2)
    return sp


def LEAF_DARK_():
    from kit import LEAF_DARK
    return LEAF_DARK


def notice_board(W=124, H=118):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 6, 52, 8)
    for px in (14, W - 22):
        sp.put(sp.rect(px, 30, 9, H - 34), quant(hgrad(sp, px, px + 9, 0.8, 0.3), WOOD))
    bm = sp.rect(8, 28, W - 16, 58)
    sp.put(bm, WOOD[2])
    cork = sp.rect(13, 33, W - 26, 48)
    sp.put(cork, quant(0.55 + (noise(H, W, 2, 3) - 0.5) * 0.4, ramp('#7a5434', '#9a6c44', '#b88654', '#d2a06a'), dith))
    rng = np.random.default_rng(4)
    papers = [(18, 37, 28, 22, '#f4ecd4'), (50, 36, 24, 30, '#fde2a0'), (78, 38, 26, 20, '#cfe6f2'), (24, 62, 22, 16, '#f7c6cf'),
              (76, 60, 28, 18, '#f4ecd4')]
    for x, y, w, h, c in papers:
        sp.put(sp.rect(x + 2, y + 2, w, h), hexrgb('#5a3a22'))
        sp.put(sp.rect(x, y, w, h), hexrgb(c))
        for k in range(h // 5):
            sp.put(sp.rect(x + 3, y + 5 + k * 5, w - 6 - rng.integers(0, 8), 1), hexrgb('#8a8076'))
        sp.put(sp.ellipse(x + w / 2, y + 2, 2, 2), hexrgb(['#d34a4a', '#3d6fd3', '#e1b12c'][x % 3]))
    # cat poster with an orange cat doodle
    sp.put(sp.ellipse(36, 70, 5, 4), hexrgb('#e6893a'))
    # little gable roof
    roof = sp.poly([(2, 30), (W - 2, 30), (W - 14, 14), (14, 14)])
    tile_roof(sp, roof, TERRA, 14, 30, 12, 8, 3, scallop=False)
    sp.put(sp.rect(2, 28, W - 4, 4), TERRA[0])
    outline(sp, WOOD[0], width=2)
    return sp


def mailbox(W=44, H=84, R=None):
    R = R if R is not None else ramp('#5a1418', '#7d1f24', '#a12d30', '#c4433f', '#de6a5e')
    sp = Sprite(W, H)
    ground_shadow(sp, W / 2, H - 4, 16, 5)
    sp.put(sp.rect(W / 2 - 3, 40, 6, H - 44), METAL[2])
    body = sp.rect(6, 12, W - 12, 32) | sp.ellipse(W / 2, 14, W / 2 - 6, 10)
    sp.put(body, quant(hgrad(sp, 6, W - 6, 0.85, 0.25), R))
    sp.put(sp.rect(10, 22, W - 20, 3), R[0])
    sp.put(sp.rect(W - 9, 4, 3, 18), METAL[3])
    sp.put(sp.rect(W - 9, 4, 10, 6), hexrgb('#e9c35a'))
    outline(sp, R[0] * 0.7, width=1)
    return sp


def old_mailbox(W=58, H=102):
    R = ramp('#1f3428', '#2c4a38', '#3c6249', '#527a5c', '#6e9473')
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 4, 22, 6)
    body = sp.rect(8, 22, W - 16, H - 30) | sp.ellipse(W / 2, 22, W / 2 - 8, 12)
    sp.put(body, quant(hgrad(sp, 8, W - 8, 0.8, 0.25) + (noise(H, W, 3, 2) - 0.5) * 0.2, R, dith))
    rust = body & (noise(H, W, 4, 9) > 0.72)
    sp.rgb[rust] = sp.rgb[rust] * 0.4 + np.array([150, 80, 40]) * 0.6
    sp.put(sp.rect(14, 40, W - 28, 5), R[0])
    sp.put(sp.rect(4, H - 12, W - 8, 8), quant(hgrad(sp, 4, W - 4, 0.7, 0.3), R))
    sp.put(sp.rect(16, 54, W - 32, 14), hexrgb('#d9cfa8'))
    sp.put(text_mask(sp, 'POS', W / 2, 61, 10), R[1])
    outline(sp, R[0] * 0.7, width=1)
    return sp


def bicycle(W=96, H=64):
    sp = Sprite(W, H)
    ground_shadow(sp, W / 2, H - 4, 44, 5)
    frame = hexrgb('#3d8aa0')
    for wx in (20, W - 20):
        ring = sp.ellipse(wx, H - 20, 17, 17) & ~sp.ellipse(wx, H - 20, 13, 13)
        sp.put(ring, hexrgb('#22262c'))
        for a in np.linspace(0, np.pi, 6, endpoint=False):
            for t in np.linspace(-13, 13, 26):
                sp.put(sp.ellipse(wx + np.cos(a) * t, H - 20 + np.sin(a) * t, 0.6, 0.6), METAL[5])
        sp.put(sp.ellipse(wx, H - 20, 3, 3), METAL[4])
    def bar(a, b, wdt=2.2, c=frame):
        for t in np.linspace(0, 1, 40):
            sp.put(sp.ellipse(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, wdt, wdt), c)
    by = H - 20
    bar((20, by), (42, by - 2)); bar((42, by - 2), (W - 26, by - 26)); bar((20, by), (36, by - 26))
    bar((36, by - 26), (W - 26, by - 26)); bar((42, by - 2), (36, by - 30)); bar((W - 20, by), (W - 26, by - 34))
    sp.put(sp.rect(28, by - 34, 16, 5), hexrgb('#5a3a26'))
    bar((W - 32, by - 36), (W - 16, by - 36), 2, METAL[2])
    # front basket with books
    bk = sp.rect(W - 22, by - 44, 22, 14)
    sp.put(bk, quant(0.5 + (((sp.xx + sp.yy) % 4) < 2) * 0.2, WOOD))
    sp.put(sp.rect(W - 19, by - 50, 6, 8), hexrgb('#c4433f'))
    sp.put(sp.rect(W - 12, by - 48, 7, 6), hexrgb('#3d608e'))
    outline(sp, hexrgb('#1a1d22'), inner=False, width=1)
    return sp


def vending(W=64, H=120):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 4, 30, 6)
    body = sp.rect(4, 6, W - 8, H - 12)
    sp.put(body, quant(hgrad(sp, 4, W - 4, 0.85, 0.35), ramp('#7a1f24', '#a12d30', '#c4433f', '#de6a5e', '#f09a88'), dith))
    win = sp.rect(9, 14, W - 26, 62)
    sp.put(win, quant(vgrad(sp, 14, 76, 0.9, 0.55), ramp('#7b8f9a', '#a9c1cc', '#d6e8ee', '#f4fbfc')))
    cols = ['#3d8aa0', '#e1b12c', '#4f8a47', '#d34a4a', '#7865bb']
    for r in range(4):
        for c in range(3):
            x = 12 + c * 11; y = 18 + r * 15
            sp.put(sp.rect(x, y, 7, 11), hexrgb(cols[(r + c) % 5]))
            sp.put(sp.rect(x + 1, y + 1, 2, 9), hexrgb('#ffffff'), 0.9)
        sp.put(sp.rect(10, 30 + r * 15, W - 28, 2), METAL[3])
    sp.put(sp.rect(W - 15, 18, 7, 22), METAL[2])
    for k in range(4):
        sp.put(sp.rect(W - 14, 20 + k * 5, 5, 3), hexrgb('#ffe39a'))
    sp.put(sp.rect(12, 86, W - 24, 12), hexrgb('#1c2128'))
    sp.put(sp.rect(6, 6, W - 12, 4), hexrgb('#f09a88'))
    glow(sp, W / 2 - 4, 44, 46, hexrgb('#e8f6ff'), 0.18)
    outline(sp, hexrgb('#4a1418'), width=2)
    return sp


def glow(sp, cx, cy, r, col, strength=0.5):
    d = np.sqrt((sp.xx - cx) ** 2 + (sp.yy - cy) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    c = np.asarray(col, np.float32)
    keep = sp.a > 0.5
    sp.rgb = np.where(keep[..., None], np.clip(sp.rgb + c * a[..., None] * 0.5, 0, 255), np.where((a > sp.a)[..., None], c, sp.rgb))
    sp.a = np.where(keep, sp.a, np.maximum(sp.a, a))


def signpost(arrows, W=132, H=116):
    """arrows: list of (label, direction) with direction -1 (left) or +1 (right)."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 22, 6)
    sp.put(sp.rect(cx - 5, 8, 10, H - 12), quant(hgrad(sp, cx - 5, cx + 5, 0.85, 0.3), WOOD))
    sp.put(sp.ellipse(cx, 8, 7, 5), WOOD[4])
    for i, (label, d) in enumerate(arrows):
        y = 18 + i * 28
        x0 = cx - 54 if d < 0 else cx - 12
        x1 = cx + 12 if d < 0 else cx + 54
        tip = x0 - 12 if d < 0 else x1 + 12
        board = sp.poly([(x0, y), (x1, y), (x1, y + 22), (x0, y + 22), (tip, y + 11)] if d > 0 else
                        [(x1, y), (x0, y), (tip, y + 11), (x0, y + 22), (x1, y + 22)])
        if d > 0:
            board = sp.poly([(x0, y), (x1, y), (tip, y + 11), (x1, y + 22), (x0, y + 22)])
        sp.put(board, quant(0.62 + vgrad(sp, y, y + 22, 0.15, -0.15) + (((sp.yy - y) % 7) < 1) * -0.1, WOOD, dith))
        sp.put(text_mask(sp, label, (x0 + x1) / 2, y + 11, 11), hexrgb('#3a2418'))
        sp.put(sp.ellipse(cx, y + 11, 2, 2), METAL[2])
    outline(sp, WOOD[0], width=1)
    return sp


def banner_pole(W=104, H=210):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = 18
    ground_shadow(sp, cx + 10, H - 5, 22, 6)
    sp.put(sp.rect(cx - 4, 10, 8, H - 14), quant(hgrad(sp, cx - 4, cx + 4, 0.85, 0.3), METAL))
    sp.put(sp.ellipse(cx, 8, 7, 7), GOLD[3])
    sp.put(sp.rect(cx, 22, 78, 5), METAL[3])
    flag = sp.poly([(cx + 8, 27), (cx + 74, 27), (cx + 74, 150), (cx + 41, 134), (cx + 8, 150)])
    wave = np.sin(sp.yy * 0.07) * 0.08
    sp.put(flag, quant(0.62 + hgrad(sp, cx + 8, cx + 74, 0.15, -0.2) + wave, ramp('#7a2a1a', '#a33d22', '#c95a2c', '#e57d3e', '#f4a462'), dith))
    sp.put(sp.rect(cx + 8, 27, 66, 6), GOLD[3])
    # cup emblem
    ex, ey = cx + 41, 78
    sp.put(sp.ellipse(ex, ey, 20, 20), CREAM[4])
    sp.put(sp.rect(ex - 10, ey - 6, 18, 15), hexrgb('#7a4426'))
    sp.put(sp.ellipse(ex + 9, ey + 1, 5, 5) & ~sp.ellipse(ex + 9, ey + 1, 2.5, 2.5), hexrgb('#7a4426'))
    sp.put(sp.rect(ex - 6, ey - 16, 2, 7) | sp.rect(ex + 1, ey - 18, 2, 8), CREAM[1])
    sp.put(text_mask(sp, 'KAFE', ex, 112, 12), CREAM[5])
    sp.put(sp.rect(cx - 8, H - 10, 16, 6), METAL[2])
    outline(sp, hexrgb('#3a1410'), width=1)
    return sp


def lamp_gold(W=76, H=150):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 18, 5)
    sp.put(sp.rect(cx - 10, H - 18, 20, 14), quant(hgrad(sp, cx - 10, cx + 10, 0.8, 0.3), METAL, dith))
    sp.put(sp.rect(cx - 3, 46, 6, H - 60), quant(hgrad(sp, cx - 3, cx + 3, 0.9, 0.3), METAL))
    for yy in (70, H - 30):
        sp.put(sp.ellipse(cx, yy, 6, 3), GOLD[3])
    # lantern cage
    cage = sp.poly([(cx - 15, 18), (cx + 15, 18), (cx + 11, 48), (cx - 11, 48)])
    sp.put(cage, quant(vgrad(sp, 18, 48, 1.0, 0.7), ramp('#d98a2c', '#f5b44a', '#ffd776', '#fff0b8', '#fffbe6')))
    sp.put(sp.rect(cx - 1, 18, 2, 30) | sp.rect(cx - 15, 32, 30, 2), GOLD[1])
    sp.put(sp.poly([(cx - 19, 18), (cx + 19, 18), (cx + 8, 6), (cx - 8, 6)]), quant(hgrad(sp, cx - 19, cx + 19, 0.9, 0.3), GOLD))
    sp.put(sp.ellipse(cx, 4, 4, 4), GOLD[4])
    sp.put(sp.rect(cx - 13, 47, 26, 4), GOLD[2])
    glow(sp, cx, 33, 36, hexrgb('#ffd37a'), 0.45)
    outline(sp, METAL[0], width=1)
    return sp


def garden_plot(W=152, H=82):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    bed = sp.rect(6, 10, W - 12, H - 18)
    sp.put(sp.rect(2, 6, W - 4, H - 10), quant(hgrad(sp, 2, W, 0.8, 0.4), WOOD, dith))
    soil = quant(0.45 + (((sp.yy - 14) % 16) < 6) * 0.2 + (noise(H, W, 2, 5) - 0.5) * 0.3,
                 ramp('#2c1d14', '#3f2a1c', '#57392a', '#6f4b36', '#87604a'), dith)
    sp.put(bed, soil)
    rng = np.random.default_rng(12)
    for r in range(4):
        y = 18 + r * 16
        for k in range(8):
            x = 16 + k * 17 + rng.integers(-2, 3)
            if r % 2 == 0:   # leafy greens
                for a in range(5):
                    ang = a * 1.25
                    sp.put(sp.ellipse(x + np.cos(ang) * 4, y - 3 + np.sin(ang) * 2.5, 4, 3), LEAF[3 + (a % 3)])
            else:            # carrots / tomatoes
                sp.put(sp.ellipse(x, y - 4, 2.5, 5), LEAF[4])
                sp.put(sp.ellipse(x + 3, y - 1, 2.6, 2.6), hexrgb('#d94a3a' if k % 2 else '#ee8a2e'))
    sp.put(sp.rect(W - 26, 0, 4, 30), WOOD[2])
    sp.put(sp.rect(W - 36, 2, 24, 12), hexrgb('#f4ecd4'))
    outline(sp, WOOD[0], width=1)
    return sp


def flower_buckets(palette=0, W=152, H=94):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 6, 70, 8)
    sp.put(sp.rect(4, H - 22, W - 8, 16), quant(hgrad(sp, 4, W, 0.75, 0.35), WOOD, dith))
    rng = np.random.default_rng(palette * 7 + 3)
    sets = [(0, 1, 2), (4, 3, 0), (2, 1, 4)][palette]
    for i, bx in enumerate((28, 64, 100, 128)):
        bw = 26 if i != 3 else 20
        b = sp.poly([(bx - bw / 2, H - 52), (bx + bw / 2, H - 52), (bx + bw / 2 - 4, H - 22), (bx - bw / 2 + 4, H - 22)])
        sp.put(b, quant(hgrad(sp, bx - bw / 2, bx + bw / 2, 0.9, 0.3), METAL, dith))
        sp.put(sp.rect(bx - bw / 2 - 1, H - 54, bw + 2, 4), METAL[5])
        F = FLOWERS[sets[i % 3]]
        for k in range(26):
            a = rng.uniform(np.pi * 1.0, np.pi * 2.0)
            r = rng.uniform(2, 16)
            x = bx + np.cos(a) * r
            y = H - 58 + np.sin(a) * r * 1.1
            sp.put(sp.ellipse(x, y + 4, 3.5, 3), LEAF[rng.integers(2, 5)])
            sp.put(sp.ellipse(x, y, 3.6, 3.4), F[rng.integers(1, 4)])
            sp.rgb[int(np.clip(y - 1, 0, H - 1)), int(np.clip(x - 1, 0, W - 1))] = F[3]
    sp.put(sp.rect(W - 46, H - 40, 34, 14), hexrgb('#243028'))
    sp.put(text_mask(sp, 'BUNGA', W - 29, H - 33, 8), hexrgb('#e8e2cf'))
    outline(sp, WOOD[0], width=1)
    return sp


def column_stone(W=88, H=210):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 6, 36, 8)
    sp.put(sp.rect(cx - 34, H - 26, 68, 20), quant(hgrad(sp, cx - 34, cx + 34, 0.8, 0.3), STONE, dith))
    sp.put(sp.rect(cx - 30, H - 34, 60, 9), STONE[4])
    shaft = sp.rect(cx - 22, 34, 44, H - 68)
    flute = (np.sin((sp.xx - cx) * 0.9) * 0.5 + 0.5) * 0.15
    sp.put(shaft, quant(hgrad(sp, cx - 22, cx + 22, 0.9, 0.25) + flute + (noise(H, W, 3, 4) - 0.5) * 0.1, STONE, dith))
    sp.put(sp.rect(cx - 30, 24, 60, 12), STONE[4])
    sp.put(sp.rect(cx - 36, 12, 72, 13), quant(hgrad(sp, cx - 36, cx + 36, 0.9, 0.35), STONE, dith))
    sp.put(sp.rect(cx - 36, 12, 72, 2), STONE[6])
    # ivy wrapping up the shaft
    rng = np.random.default_rng(8)
    for k in range(120):
        t = k / 120
        y = H - 40 - t * (H - 80)
        x = cx + np.sin(t * 9) * 20
        sp.put(sp.ellipse(x + rng.normal(0, 3), y + rng.normal(0, 3), 4.5, 3.6), LEAF[rng.integers(1, 6)])
        if k % 11 == 0:
            sp.put(sp.ellipse(x + 3, y - 2, 2.4, 2.4), FLOWERS[3][2])
    outline(sp, STONE[0], width=2)
    return sp


# ----------------------------------------------------------------------------- fences along roads

def railing_iron(W=196, H=72):
    """Wrought-iron railing segment (96 world wide + overlap) for canal banks and terraces."""
    sp = Sprite(W, H)
    iron = ramp('#15181d', '#22272e', '#323941', '#46505a', '#5e6a75')
    ground_shadow(sp, W / 2, H - 4, W / 2, 5, 0.25)
    for x in (4, W - 12):                                  # stone-capped posts
        sp.put(sp.rect(x, 18, 10, H - 24), quant(hgrad(sp, x, x + 10, 0.85, 0.3), iron))
        sp.put(sp.ellipse(x + 5, 16, 6, 6), GOLD[3])
    sp.put(sp.rect(4, 22, W - 8, 4), iron[3])              # top rail
    sp.put(sp.rect(4, 22, W - 8, 1), iron[4])
    sp.put(sp.rect(4, H - 16, W - 8, 4), iron[2])          # bottom rail
    for x in range(16, W - 14, 10):                        # bars with little spear tips
        sp.put(sp.rect(x, 22, 3, H - 36), iron[2])
        sp.put(sp.poly([(x - 1, 22), (x + 4, 22), (x + 1.5, 15)]), iron[3])
    for x in range(26, W - 20, 40):                        # scroll rings
        sp.put(sp.ellipse(x, 40, 7, 7) & ~sp.ellipse(x, 40, 4.5, 4.5), iron[3])
    outline(sp, hexrgb('#0c0e11'), inner=False, width=1)
    return sp


def fence_picket(W=196, H=70, seed=0):
    """Low white picket fence segment (96 world wide) for the edge of streets and gardens."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 4, W / 2, 6, 0.28)
    rng = np.random.default_rng(seed)
    for y in (30, H - 22):
        sp.put(sp.rect(0, y, W, 7), quant(vgrad(sp, y, y + 7, 0.8, 0.45), TRIM, dith))
    for i, x in enumerate(range(3, W - 8, 14)):
        h = rng.integers(0, 3)
        top = 14 + h
        pk = sp.rect(x, top + 6, 10, H - 10 - top - 6) | sp.poly([(x, top + 7), (x + 10, top + 7), (x + 5, top)])
        sp.put(pk, quant(hgrad(sp, x, x + 10, 0.95, 0.5) + (noise(H, W, 3, seed + i) - 0.5) * 0.12, TRIM, dith))
        darken(sp, pk & (sp.yy > H - 16), 0.85)
    # a few vines and flowers growing through
    for k in range(14):
        x = rng.uniform(0, W); y = rng.uniform(H - 22, H - 8)
        sp.put(sp.ellipse(x, y, 5, 4), LEAF[rng.integers(2, 6)])
        if k % 4 == 0:
            sp.put(sp.ellipse(x, y - 3, 2.4, 2.4), FLOWERS[k % 5][2])
    outline(sp, TRIM[0] * 0.8, width=1)
    return sp


# ----------------------------------------------------------------------------- town street

SHOP_STYLES = {
    'florist': dict(wall='plaster', wallR=ramp('#7a6a6e', '#9c8a8e', '#bba6aa', '#d6c2c4', '#e8d8d8', '#f4ecea', '#fdf8f6'),
                    awning=('#4f8a47', '#f1e6d3'), sign='TOKO BUNGA', signR=SHUTTER_GREEN, roof=GREEN_ROOF),
    'bakery': dict(wall='brick', wallR=BRICK, awning=('#c95a2c', '#f4ecd4'), sign='TOKO ROTI', signR=SHOP_WOOD, roof=TERRA),
    'mart': dict(wall='siding', wallR=ramp('#3a4a3a', '#4a5e48', '#5d7458', '#728a6a', '#8aa180', '#a6b99a', '#c4d3b8'),
                 awning=('#3d6fd3', '#eef0f2'), sign='WARUNG 24', signR=ramp('#1f2a4a', '#2b3a63', '#3a4e7e', '#4c6597', '#6382b0'), roof=SLATE),
    'arcade': dict(wall='plaster', wallR=ramp('#3b2c6a', '#4d3a85', '#6a52a8', '#8a72cf', '#a894e0', '#c6b8f0', '#e4dcfc'),
                   awning=('#e0627a', '#2b2350'), sign='ARCADE', signR=ramp('#140f2a', '#1f1840', '#2b2366', '#41389a', '#6a5fd0'), roof=SLATE),
    'books': dict(wall='siding', wallR=ramp('#5a3a22', '#704a2c', '#8a5c36', '#a37045', '#bb875a', '#d1a275', '#e4c098'),
                  awning=('#7a2a1a', '#e8dcbb'), sign='BUKU', signR=SHOP_WOOD, roof=TERRA),
}


def shopfront(kind='florist', W=440, H=520):
    """Two-storey town shop: shop window + door + striped awning + sign below, flat with balcony
    windows above, parapet roof with a water tank / AC units. Door at the horizontal centre."""
    st = SHOP_STYLES[kind]
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    bot = H - 4
    x0, x1 = 12, W - 12
    ground_shadow(sp, cx, bot - 2, W / 2 - 4, 10, 0.35)
    top = 92
    wm = sp.rect(x0, top, x1 - x0, bot - top)
    if st['wall'] == 'brick':
        bricks(sp, wm, st['wallR'], x0, top, 24, 11, 3)
    elif st['wall'] == 'siding':
        clapboard(sp, wm, st['wallR'], x0, top, 10, 4)
    else:
        plaster(sp, wm, st['wallR'], 6, 0.68)
    # parapet + roof edge
    sp.put(sp.rect(x0 - 6, top - 14, x1 - x0 + 12, 16), quant(vgrad(sp, top - 14, top + 2, 0.85, 0.45), STONE, dith))
    sp.put(sp.rect(x0 - 6, top - 14, x1 - x0 + 12, 2), STONE[6])
    roof = sp.rect(x0 + 4, 20, x1 - x0 - 8, top - 34)
    sp.put(roof, quant(0.45 + (noise(H, W, 6, 2) - 0.5) * 0.15, st['roof'], dith))
    sp.put(sp.rect(x0 + 4, 20, x1 - x0 - 8, 3), st['roof'][-1])
    # roof clutter: water tank, AC units, antenna
    tx = x1 - 90
    sp.put(sp.rect(tx, 8, 54, 44), quant(hgrad(sp, tx, tx + 54, 0.9, 0.35), ramp('#2c5a7a', '#3c7194', '#4f8aae', '#6aa4c4', '#90c0da')))
    sp.put(sp.ellipse(tx + 27, 8, 27, 7), hexrgb('#90c0da'))
    for ax in (x0 + 30, x0 + 74):
        sp.put(sp.rect(ax, 36, 34, 22), quant(hgrad(sp, ax, ax + 34, 0.9, 0.4), METAL))
        sp.put(sp.ellipse(ax + 17, 47, 8, 8), METAL[1])
    sp.put(sp.rect(cx, 0, 3, 40), METAL[2])
    # upper floor: two windows with flower boxes, one with a small balcony rail
    for i, wx in enumerate((x0 + 46, x1 - 46 - 86)):
        window(sp, wx, top + 34, 86, 76, TRIM, ('cream', 'rose', 'teal')[i % 3], box=(i == 0), panes=(2, 2))
        if i == 1:
            for k in range(9):
                sp.put(sp.rect(wx - 6 + k * 12, top + 108, 3, 24), METAL[2])
            sp.put(sp.rect(wx - 8, top + 106, 104, 4), METAL[3])
            sp.put(sp.rect(wx - 8, top + 130, 104, 4), METAL[1])
    # sign band
    sy = top + 150
    sp.put(sp.rect(x0, sy, x1 - x0, 46), st['signR'][1])
    sm = sp.rect(x0 + 24, sy + 5, x1 - x0 - 48, 36)
    sp.put(sm, quant(vgrad(sp, sy, sy + 46, 0.75, 0.4), st['signR'], dith))
    tm = text_mask(sp, st['sign'], cx, sy + 23, 26)
    sp.put(np.roll(np.roll(tm, 2, 0), 2, 1), st['signR'][0])
    sp.put(tm, quant(vgrad(sp, sy + 8, sy + 38, 0.95, 0.55), GOLD if kind != 'arcade' else ramp('#7a2a5a', '#c4467e', '#ee7aa8', '#ffb6d4', '#fff0f6')))
    if kind == 'arcade':
        glow(sp, cx, sy + 23, 120, hexrgb('#ff8ad0'), 0.25)
    # awning
    ay0, ay1 = sy + 48, sy + 92
    aw = sp.poly([(x0 - 10, ay1), (x1 + 10, ay1), (x1, ay0), (x0, ay0)])
    stripe = (((sp.xx - x0) // 24) % 2 == 0)
    a0 = quant(vgrad(sp, ay0, ay1, 0.85, 0.45), ramp_from_hex(st['awning'][0]))
    a1 = quant(vgrad(sp, ay0, ay1, 0.85, 0.45), ramp_from_hex(st['awning'][1]))
    sp.put(aw, np.where(stripe[..., None], a0, a1))
    for xx in range(int(x0 - 10), int(x1 + 10), 24):
        sp.put(sp.ellipse(xx + 12, ay1, 12, 8) & (sp.yy >= ay1), a0 if ((xx - x0) // 24) % 2 == 0 else a1)
    darken(sp, sp.rect(x0, ay1 + 8, x1 - x0, 16) & wm, 0.72)
    # shop window + door
    dw, dh = 78, 126
    door(sp, cx, bot - 8, dw, dh, SHOP_WOOD, TRIM, glass=True, double=(kind in ('mart', 'arcade')))
    for wx, ww in ((x0 + 18, cx - dw / 2 - 30 - x0 - 18), (cx + dw / 2 + 30, x1 - 18 - (cx + dw / 2 + 30))):
        sp.put(sp.rect(wx - 6, ay1 + 18, ww + 12, bot - 30 - ay1 - 18 + 6), SHOP_WOOD[1])
        window(sp, wx, ay1 + 24, ww, bot - 44 - ay1 - 24, SHOP_WOOD, curtain=None, box=False,
               lit=(kind in ('bakery', 'arcade', 'mart')), panes=(2, 1))
        sp.put(sp.rect(wx - 6, bot - 22, ww + 12, 14), quant(hgrad(sp, wx, wx + ww, 0.7, 0.35), SHOP_WOOD))
    # threshold step
    sp.put(sp.rect(cx - dw / 2 - 12, bot - 8, dw + 24, 8), STONE[4])
    # kind-specific goods outside
    rng = np.random.default_rng(len(kind))
    if kind == 'florist':
        for i, bx in enumerate((x0 + 30, x0 + 64, x1 - 64, x1 - 30)):
            potted_plant(sp, bx, bot - 2, 1.2, i)
    elif kind == 'bakery':
        sp.put(sp.rect(x1 - 70, bot - 60, 40, 56), hexrgb('#243028'))
        for k in range(5):
            sp.put(sp.rect(x1 - 64, bot - 54 + k * 9, 20 + (k * 7) % 9, 2), hexrgb('#e8e2cf'))
    elif kind == 'mart':
        for k, bx in enumerate((x1 - 64, x1 - 34)):
            sp.put(sp.rect(bx - 12, bot - 58, 26, 54), hexrgb(['#c4433f', '#3d6fd3'][k]))
            sp.put(sp.rect(bx - 8, bot - 52, 18, 24), hexrgb('#e8f6ff'))
    elif kind == 'arcade':
        for k in range(10):
            x = x0 + 10 + k * (x1 - x0 - 20) / 9
            sp.put(sp.ellipse(x, sy - 4, 4, 4), hexrgb(['#ff8ad0', '#8af0ff', '#fff08a'][k % 3]))
    outline(sp, st['roof'][0] * 0.8, width=2)
    return sp


def ramp_from_hex(h):
    c = hexrgb(h)
    return np.array([c * 0.55, c * 0.72, c * 0.88, c, np.minimum(c * 1.12 + 12, 255)], np.float32)


def car(color='#c4433f', W=232, H=124, facing=1):
    """Parked compact car seen from the street side (3/4 top-down)."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    R = ramp_from_hex(color)
    ground_shadow(sp, W / 2, H - 10, W / 2 - 8, 14, 0.45)
    body = sp.poly([(10, H - 30), (W - 10, H - 30), (W - 6, H - 62), (W - 40, H - 70), (W - 70, H - 108), (70, H - 110), (44, H - 72), (8, H - 64)])
    sp.put(body, quant(vgrad(sp, H - 110, H - 28, 0.95, 0.4) + hgrad(sp, 0, W, 0.05, -0.08), R, dith))
    glass = sp.poly([(78, H - 104), (W - 76, H - 104), (W - 50, H - 72), (52, H - 72)])
    sp.put(glass, quant(vgrad(sp, H - 104, H - 72, 0.85, 0.35), ramp('#20354a', '#2c4c66', '#3f6a86', '#5e8ea8', '#8fb8cc', '#c4e0ea')))
    sp.put(sp.rect(W / 2 - 3, H - 104, 6, 32), R[1])
    diag = sp.xx + (sp.yy - H) * 0.8
    lighten(sp, glass & ((diag % 70) < 10), 0.3, (220, 240, 250))
    sp.put(sp.rect(12, H - 46, W - 24, 3), R[1])                       # door line
    sp.put(sp.rect(W / 2 - 1, H - 70, 2, 40), R[1])
    for hx in (W / 2 - 30, W / 2 + 24):
        sp.put(sp.rect(hx, H - 58, 12, 3), METAL[4])
    lx = W - 16 if facing > 0 else 10
    sp.put(sp.rect(lx, H - 58, 8, 10), hexrgb('#fff2c0'))
    sp.put(sp.rect(W - 18 - lx + 10 if facing > 0 else W - 18, H - 58, 8, 10), hexrgb('#e04040'))
    sp.put(sp.rect(8, H - 34, W - 16, 8), METAL[2])                    # bumper line
    for wx in (52, W - 52):
        sp.put(sp.ellipse(wx, H - 26, 20, 18), hexrgb('#1a1d22'))
        sp.put(sp.ellipse(wx, H - 26, 10, 9), METAL[4])
        sp.put(sp.ellipse(wx, H - 26, 4, 4), METAL[2])
    outline(sp, R[0] * 0.6, width=2)
    return sp


def bus_shelter(W=220, H=200):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 8, W / 2 - 4, 12, 0.38)
    for x in (14, W - 22):
        sp.put(sp.rect(x, 40, 8, H - 46), quant(hgrad(sp, x, x + 8, 0.9, 0.35), METAL))
    back = sp.rect(22, 54, W - 44, H - 100)
    sp.put(back, quant(vgrad(sp, 54, H - 46, 0.85, 0.6), ramp('#7b8f9a', '#a9c1cc', '#d6e8ee', '#f4fbfc')), 0.75)
    sp.put(sp.rect(30, 62, 60, 80), hexrgb('#f4ecd4'))                  # poster / route map
    for k in range(6):
        sp.put(sp.rect(36, 70 + k * 11, 44 - (k * 7) % 15, 3), hexrgb(['#3d6fd3', '#c4433f', '#4f8a47'][k % 3]))
    roof = sp.poly([(0, 42), (W, 42), (W - 10, 20), (10, 20)])
    sp.put(roof, quant(vgrad(sp, 20, 42, 0.9, 0.5), ramp('#1f5a4a', '#2b7360', '#3c8c76', '#55a68e', '#78c0a8')))
    sp.put(sp.rect(0, 40, W, 6), METAL[2])
    sp.put(sp.rect(W / 2 - 40, 26, 80, 12), hexrgb('#f4ecd4'))
    sp.put(text_mask(sp, 'HALTE', W / 2, 32, 10), hexrgb('#1f5a4a'))
    bench_y = H - 58
    sp.put(sp.rect(30, bench_y, W - 60, 10), quant(hgrad(sp, 30, W - 30, 0.85, 0.4), WOOD))
    for x in (40, W - 48):
        sp.put(sp.rect(x, bench_y + 10, 6, 40), METAL[2])
    outline(sp, METAL[0], width=1)
    return sp


def kiosk(W=180, H=190):
    """Rini's little street kiosk: wooden booth with goods, striped canopy."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 8, W / 2 - 4, 12, 0.38)
    booth = sp.rect(14, 80, W - 28, H - 88)
    sp.put(booth, quant(hgrad(sp, 14, W - 14, 0.8, 0.35) + (((sp.xx - 14) % 18) < 2) * -0.2, WOOD, dith))
    sp.put(sp.rect(10, 104, W - 20, 10), WOOD[4])
    rng = np.random.default_rng(9)
    for k in range(12):
        x = 22 + (k % 6) * 24; y = 88 + (k // 6) * 8
        sp.put(sp.rect(x, y, 14, 12), hexrgb(['#e1b12c', '#c4433f', '#3d8aa0', '#4f8a47', '#f4ecd4', '#ee8a2e'][k % 6]))
    for x in (16, W - 22):
        sp.put(sp.rect(x, 30, 6, 52), WOOD[2])
    can = sp.poly([(0, 82), (W, 82), (W - 12, 26), (12, 26)])
    stripe = ((sp.xx // 20) % 2 == 0)
    sp.put(can, np.where(stripe[..., None], quant(vgrad(sp, 26, 82, 0.9, 0.5), ramp_from_hex('#e1b12c')),
                         quant(vgrad(sp, 26, 82, 0.9, 0.5), CREAM)))
    sp.put(sp.rect(W / 2 - 44, 6, 88, 22), WOOD[1])
    sp.put(text_mask(sp, 'KIOS RINI', W / 2, 17, 11), CREAM[5])
    outline(sp, WOOD[0], width=1)
    return sp


def flower_stall(W=200, H=150):
    sp = Sprite(W, H)
    ground_shadow(sp, W / 2, H - 6, W / 2 - 4, 10, 0.35)
    sp.put(sp.rect(10, H - 60, W - 20, 50), quant(hgrad(sp, 10, W - 10, 0.85, 0.4), WOOD))
    for i in range(4):
        sub = flower_buckets(i % 3, 152, 94).image()
    rng = np.random.default_rng(3)
    for k in range(70):
        x = rng.uniform(18, W - 18); y = rng.uniform(H - 92, H - 58)
        F = FLOWERS[rng.integers(0, 5)]
        sp.put(sp.ellipse(x, y + 5, 4, 3), LEAF[rng.integers(2, 5)])
        sp.put(sp.ellipse(x, y, 4, 3.6), F[rng.integers(1, 4)])
    for x in (12, W - 18):
        sp.put(sp.rect(x, 24, 6, H - 70), WOOD[2])
    can = sp.poly([(0, 40), (W, 40), (W - 10, 10), (10, 10)])
    sp.put(can, quant(vgrad(sp, 10, 40, 0.9, 0.5), ramp_from_hex('#4f8a47')))
    outline(sp, WOOD[0], width=1)
    return sp


# ----------------------------------------------------------------------------- residential

HOUSE_VARIANTS = {
    'pink': ('arland', ramp('#8a5a66', '#a8707c', '#c48a95', '#d9a4ae', '#e8bec6', '#f4d8dd', '#fcecef'), TERRA, '3'),
    'mint': ('arland', ramp('#4a6a5a', '#5c8270', '#719a86', '#88b29c', '#a2c8b2', '#bedcca', '#dcefe4'), SLATE, '5'),
    'butter': ('sofia', ramp('#8a6a3a', '#a8844c', '#c4a060', '#d8b878', '#e8cf96', '#f2e2b6', '#faf0d8'), GREEN_ROOF, '11'),
    'violet': ('arland', ramp('#4f4866', '#625a80', '#786f9a', '#9088b2', '#aaa3c8', '#c6c0dc', '#e2def0'), TERRA, '8'),
    'redbrick': ('sofia', None, SLATE, '2'),
}


def house_variant(name, W=600, H=500):
    """Same carefully drawn house builder with another wall/roof palette and house number."""
    base, wall, roof, no = HOUSE_VARIANTS[name]
    g = globals()
    keep = (g['SIDING_BLUE'], g['BRICK'], g['SLATE'], g['TERRA'])
    try:
        if base == 'arland':
            g['SIDING_BLUE'] = wall if wall is not None else keep[0]
            g['SLATE'] = roof
        else:
            if wall is not None:
                g['BRICK'] = wall
            g['TERRA'] = roof
        _HOUSE_NO[0] = no
        return house(base, W, H)
    finally:
        g['SIDING_BLUE'], g['BRICK'], g['SLATE'], g['TERRA'] = keep
        _HOUSE_NO[0] = None


def library(W=600, H=480):
    """City library: pale stone civic building, portico with four columns and a pediment, tall arched
    windows, big double door at the exact centre, wide steps."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    bot = H - 4
    x0, x1 = 20, W - 20
    SANDST = ramp('#8c7f6a', '#a89a82', '#c2b59c', '#d6cab2', '#e6dcc6', '#f2ead9', '#fbf6ec')
    ground_shadow(sp, cx, bot - 4, W / 2 - 10, 16, 0.4)
    top = 150
    wm = sp.rect(x0, top, x1 - x0, bot - 30 - top)
    sp.put(wm, quant(0.62 + (noise(H, W, 7, 4) - 0.5) * 0.12, SANDST, dith))
    for yy in range(top + 18, bot - 30, 22):                    # ashlar courses
        sp.put(sp.rect(x0, yy, x1 - x0, 2) & wm, SANDST[2])
        off = 0 if (yy // 22) % 2 else 22
        for xx in range(x0 + off, x1, 44):
            sp.put(sp.rect(xx, yy - 20, 2, 20) & wm, SANDST[2])
    # plinth
    sp.put(sp.rect(x0 - 6, bot - 34, x1 - x0 + 12, 20), quant(vgrad(sp, bot - 34, bot - 14, 0.6, 0.35), STONE, dith))
    # roof: low slate hip behind a cornice
    rm = sp.poly([(x0 - 14, top + 4), (x1 + 14, top + 4), (x1 - 40, 56), (x0 + 40, 56)])
    tile_roof(sp, rm, SLATE, 56, top + 4, 22, 14, seed=7, moss=0.15, scallop=False)
    darken(sp, rm & (sp.xx > cx), 0.94)
    sp.put(sp.rect(x0 - 14, top - 2, x1 - x0 + 28, 14), quant(vgrad(sp, top - 2, top + 12, 0.95, 0.55), SANDST))
    sp.put(sp.rect(x0 - 14, top + 10, x1 - x0 + 28, 3), SANDST[1])
    # side wings: two tall arched windows each
    for wx in (x0 + 26, x0 + 104, x1 - 26 - 56, x1 - 104 - 56):
        window(sp, wx, top + 44, 56, 120, SANDST, 'cream', box=False, arch=True, lit=True, panes=(2, 3))
    # portico
    px0, px1 = cx - 130, cx + 130
    sp.put(sp.rect(px0, top + 30, px1 - px0, bot - 34 - top - 30), quant(vgrad(sp, top, bot, 0.5, 0.35), SANDST))
    ped = sp.poly([(px0 - 14, top + 34), (px1 + 14, top + 34), (cx, top - 34)])
    sp.put(ped, quant(vgrad(sp, top - 34, top + 34, 0.9, 0.55), SANDST, dith))
    sp.put(sp.poly([(px0 + 14, top + 26), (px1 - 14, top + 26), (cx, top - 16)]), SANDST[3])
    sp.put(sp.ellipse(cx, top + 8, 14, 14), GOLD[3]); sp.put(sp.ellipse(cx, top + 8, 9, 9), GOLD[1])
    sp.put(sp.rect(px0 - 14, top + 32, px1 - px0 + 28, 6), SANDST[1])
    # sign
    sp.put(sp.rect(px0 + 6, top + 42, px1 - px0 - 12, 30), hexrgb('#2f3b52'))
    sp.put(text_mask(sp, 'PERPUSTAKAAN', cx, top + 57, 19), GOLD[4])
    # door + lit fanlight
    door(sp, cx, bot - 34, 96, 150, ramp('#3a2418', '#53331f', '#6d4428', '#875633', '#a06a42'), SANDST, glass=True, arch=True, double=True)
    # columns
    for k in range(4):
        colx = px0 + 14 + k * (px1 - px0 - 28) / 3
        cm = sp.rect(colx - 11, top + 76, 22, bot - 34 - top - 76)
        sp.put(cm, quant(hgrad(sp, colx - 11, colx + 11, 0.95, 0.4), SANDST))
        for f in (-5, 1, 7):
            sp.put(sp.rect(colx + f - 1, top + 80, 1, bot - 34 - top - 84), SANDST[2])
        sp.put(sp.rect(colx - 15, top + 72, 30, 8), SANDST[5])
        sp.put(sp.rect(colx - 15, bot - 42, 30, 8), SANDST[4])
    # steps
    for i in range(3):
        sw = 300 - i * 26
        sy = bot - 14 + i * -8 + 8
        st = sp.rect(cx - sw / 2, bot - 12 - i * 8, sw, 9)
        sp.put(st, quant(0.68 - i * 0.05 + hgrad(sp, cx - sw / 2, cx + sw / 2, 0.08, -0.12), STONE, dith))
        sp.put(sp.rect(cx - sw / 2, bot - 12 - i * 8, sw, 2), STONE[6])
    # book return box + banners
    sp.put(sp.rect(x1 - 70, bot - 74, 34, 44), hexrgb('#3d6fd3'))
    sp.put(sp.rect(x1 - 66, bot - 66, 26, 4), hexrgb('#1f2a4a'))
    for bx, col in ((px0 - 34, '#c4433f'), (px1 + 22, '#3d8a5a')):
        sp.put(sp.rect(bx + 5, top + 40, 2, 120), METAL[2])
        sp.put(sp.poly([(bx, top + 48), (bx + 14, top + 48), (bx + 14, top + 128), (bx + 7, top + 120), (bx, top + 128)]), hexrgb(col))
    potted_plant(sp, px0 + 2, bot - 14, 1.2, 1)
    potted_plant(sp, px1 - 2, bot - 14, 1.2, 3)
    outline(sp, SANDST[0] * 0.7, width=2)
    return sp


# ----------------------------------------------------------------------------- lakeside

def fishing_hut(W=300, H=260):
    """Weathered plank fishing hut on short stilts, tin roof, net and floats on the wall, lantern."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    bot = H - 4
    x0, x1 = 34, W - 34
    ground_shadow(sp, cx, bot - 4, W / 2 - 20, 12, 0.4)
    for px in (x0 + 8, cx - 4, x1 - 16):                          # stilts
        sp.put(sp.rect(px, bot - 30, 10, 28), quant(hgrad(sp, px, px + 10, 0.7, 0.3), WOOD))
    sp.put(sp.rect(x0 - 10, bot - 36, x1 - x0 + 20, 10), quant(vgrad(sp, bot - 36, bot - 26, 0.8, 0.4), WOOD))
    top = 104
    wm = sp.rect(x0, top, x1 - x0, bot - 36 - top)
    sp.put(wm, quant(0.55 + (((sp.xx - x0) % 16) < 2) * -0.25 + (noise(H, W, 5, 2) - 0.5) * 0.08 + vgrad(sp, top, bot, 0.05, -0.1),
                     ramp('#3d3226', '#54463a', '#6b5c4c', '#857462', '#a08e78', '#bba98f'), dith))
    window(sp, x0 + 22, top + 26, 56, 46, WOOD, 'cream', box=False, lit=True, panes=(2, 1))
    door(sp, x1 - 52, bot - 36, 52, 92, ramp('#2e3a3a', '#3e4e4e', '#516464', '#667a7a', '#7e9494'), WOOD, glass=False)
    # net + floats
    nm = sp.rect(cx - 30, top + 20, 60, 56)
    sp.put(nm & ((((sp.xx - sp.yy) % 8) == 0) | (((sp.xx + sp.yy) % 8) == 0)), hexrgb('#c9bfa4'))
    for k in range(4):
        sp.put(sp.ellipse(cx - 24 + k * 16, top + 80, 5, 5), hexrgb(['#e04a3a', '#f4ecd4'][k % 2]))
    # tin roof
    rm = sp.poly([(x0 - 22, top + 6), (x1 + 22, top + 6), (x1 + 6, 28), (x0 - 6, 28)])
    ribs = ((sp.xx // 10) % 2 == 0)
    tin = ramp('#4a5560', '#5e6a76', '#76838e', '#909ca6', '#aeb8c0', '#ccd4da')
    sp.put(rm, quant(vgrad(sp, 28, top + 6, 0.85, 0.45) + ribs * 0.1, tin, dith))
    rust = rm & (noise(H, W, 7, 9) > 0.86) & (sp.yy > top - 20)
    sp.put(rust, hexrgb('#8a4a2a'))
    sp.put(sp.rect(x0 - 22, top + 4, x1 - x0 + 44, 5), tin[0])
    darken(sp, sp.rect(x0, top + 8, x1 - x0, 16) & wm, 0.7)
    wall_lamp(sp, x1 - 62, top + 30)
    # sign
    sp.put(sp.rect(x0 + 18, top - 4, 92, 18), hexrgb('#e8dcbb'))
    sp.put(text_mask(sp, 'UMPAN', x0 + 64, top + 5, 11), hexrgb('#2f5c7a'))
    # oar + bucket
    sp.put(sp.poly([(x1 + 6, bot - 40), (x1 + 12, bot - 40), (x1 + 26, bot - 120), (x1 + 20, bot - 120)]), WOOD[3])
    sp.put(sp.rect(x0 - 26, bot - 30, 22, 24), METAL[2]); sp.put(sp.rect(x0 - 26, bot - 30, 22, 3), METAL[4])
    outline(sp, WOOD[0], width=2)
    return sp


def telescope(W=80, H=130):
    sp = Sprite(W, H)
    cx = W / 2
    ground_shadow(sp, cx, H - 6, 24, 6)
    for a in (-1, 0, 1):                                           # tripod
        sp.put(sp.poly([(cx - 2, 64), (cx + 2, 64), (cx + a * 26 + 2, H - 6), (cx + a * 26 - 2, H - 6)]), METAL[1 + abs(a)])
    tube = sp.poly([(cx - 30, 58), (cx + 26, 30), (cx + 32, 40), (cx - 24, 68)])
    sp.put(tube, quant(vgrad(sp, 28, 70, 0.95, 0.35), ramp('#5a3a10', '#8a5c18', '#b98424', '#dcae3c', '#f2d36c')))
    sp.put(sp.ellipse(cx + 29, 35, 6, 8), hexrgb('#9fd0e8'))
    sp.put(sp.rect(cx - 8, 60, 16, 8), METAL[3])
    outline(sp, METAL[0], width=1)
    return sp


def pier_post(W=36, H=84, rope=True):
    sp = Sprite(W, H)
    cx = W / 2
    sp.put(sp.rect(cx - 8, 8, 16, H - 12), quant(hgrad(sp, cx - 8, cx + 8, 0.8, 0.3), WOOD))
    sp.put(sp.ellipse(cx, 9, 8, 4), WOOD[4])
    if rope:
        sp.put(sp.rect(cx - 10, 26, 20, 4), hexrgb('#c9b48a'))
        sp.put(sp.rect(cx - 10, 32, 20, 3), hexrgb('#a8946a'))
    outline(sp, WOOD[0], width=1)
    return sp


def lifebuoy_post(W=60, H=120):
    sp = Sprite(W, H)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 14, 4)
    sp.put(sp.rect(cx - 4, 10, 8, H - 14), quant(hgrad(sp, cx - 4, cx + 4, 0.8, 0.3), WOOD))
    ring = sp.ellipse(cx, 46, 22, 22) & ~sp.ellipse(cx, 46, 11, 11)
    ang = np.arctan2(sp.yy - 46, sp.xx - cx)
    sp.put(ring, np.where(((ang * 2 / np.pi).astype(int) % 2 == 0)[..., None], hexrgb('#e04a3a') * np.ones(3), hexrgb('#f4f0e6') * np.ones(3)))
    outline(sp, WOOD[0], width=1)
    return sp


# ----------------------------------------------------------------------------- hilltop

def observatory(W=480, H=560):
    """Hilltop observatory: round sandstone drum on a wide plinth, copper-teal dome with the shutter
    open and a brass telescope peeking out, warm arched windows, double door up a short flight of
    steps, little star weathervane, potted plants and two lamps."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    bot = H - 4
    SANDST = ramp('#7d705c', '#9a8c74', '#b5a78c', '#ccc0a4', '#ded4bb', '#eee7d3', '#faf6ec')
    DOME = ramp('#163a3e', '#1f5054', '#2b686a', '#3c8382', '#559e98', '#78b9ae', '#a3d4c6')
    ground_shadow(sp, cx, bot - 6, W / 2 - 14, 20, 0.42)
    # plinth / terrace
    pm = sp.rect(24, bot - 58, W - 48, 44)
    sp.put(pm, quant(0.5 + vgrad(sp, bot - 58, bot - 14, 0.2, -0.15) + (noise(H, W, 6, 3) - 0.5) * 0.1, STONE, dith))
    for xx in range(24, W - 24, 40):
        sp.put(sp.rect(xx, bot - 58, 2, 44) & pm, STONE[1])
    sp.put(sp.rect(20, bot - 62, W - 40, 6), STONE[5])
    # drum (cylinder: horizontal shading for roundness)
    dx0, dx1, dtop = 86, W - 86, 214
    dm = sp.rect(dx0, dtop, dx1 - dx0, bot - 62 - dtop)
    u = (sp.xx - cx) / ((dx1 - dx0) / 2)
    shade = 0.78 - 0.32 * np.clip(u + 0.35, -1, 1) ** 2 - 0.12 * (u > 0.2)
    sp.put(dm, quant(shade + (noise(H, W, 7, 4) - 0.5) * 0.08, SANDST, dith))
    for yy in range(dtop + 20, bot - 62, 22):                    # ashlar courses
        sp.put(sp.rect(dx0, yy, dx1 - dx0, 2) & dm, SANDST[1])
        off = 0 if (yy // 22) % 2 else 18
        for xx in range(dx0 + off, dx1, 36):
            sp.put(sp.rect(xx, yy - 20, 2, 20) & dm, SANDST[1])
    # cornice
    sp.put(sp.rect(dx0 - 12, dtop - 10, dx1 - dx0 + 24, 14), quant(vgrad(sp, dtop - 10, dtop + 4, 0.95, 0.5), SANDST))
    sp.put(sp.rect(dx0 - 12, dtop + 3, dx1 - dx0 + 24, 3), SANDST[0])
    # dome
    r = (dx1 - dx0) / 2 + 6
    dome = sp.ellipse(cx, dtop - 8, r, r * 0.92) & (sp.yy < dtop - 6)
    sh = sphere_shade(sp, cx, dtop - 8, r, r * 0.92)
    sp.put(dome, quant(np.clip(sh, 0, 1) * 0.85 + 0.1, DOME, dith))
    for k in range(-3, 4):                                          # copper ribs
        rib = dome & (np.abs(sp.xx - (cx + k * r / 3.6 * np.sqrt(np.clip(1 - ((sp.yy - dtop + 8) / (r * 0.92)) ** 2, 0, 1)))) < 1.2)
        sp.put(rib, DOME[1])
    slit = dome & (np.abs(sp.xx - (cx + 18)) < 15) & (sp.yy > dtop - r * 0.92 + 6)
    sp.put(slit, hexrgb('#141a2a'))
    sp.put(slit & (sp.yy % 9 < 1), hexrgb('#22304a'))
    tube = sp.poly([(cx + 8, dtop - 46), (cx + 74, dtop - 126), (cx + 88, dtop - 112), (cx + 24, dtop - 34)])
    sp.put(tube, quant(vgrad(sp, dtop - 126, dtop - 34, 0.95, 0.35), GOLD))
    sp.put(sp.ellipse(cx + 81, dtop - 119, 9, 9), hexrgb('#9fd0e8'))
    sp.put(sp.ellipse(cx + 81, dtop - 119, 4, 4), hexrgb('#e8f6ff'))
    # finial + star vane
    sp.put(sp.rect(cx - 2, dtop - 8 - r * 0.92 - 30, 4, 32), METAL[3])
    st = []
    for i in range(10):
        a = -np.pi / 2 + i * np.pi / 5
        rr = 13 if i % 2 == 0 else 5.5
        st.append((cx + rr * np.cos(a), dtop - 8 - r * 0.92 - 40 + rr * np.sin(a)))
    sp.put(sp.poly(st), GOLD[4])
    # windows (lit, arched) and door
    for wx in (dx0 + 18, dx1 - 18 - 44):
        window(sp, wx, dtop + 40, 44, 96, SANDST, 'cream', box=False, arch=True, lit=True, panes=(2, 3))
    window(sp, cx - 18, dtop + 22, 36, 44, SANDST, 'cream', box=False, arch=True, lit=True, panes=(1, 2))
    door(sp, cx, bot - 62, 84, 128, ramp('#2a1c2e', '#3d2943', '#523858', '#6a4a70', '#845f8a'), SANDST, glass=True, arch=True, double=True)
    sp.put(sp.rect(cx - 52, bot - 206, 104, 22), hexrgb('#2f3b52'))
    sp.put(text_mask(sp, 'OBSERVATORIUM', cx, bot - 195, 12), GOLD[4])
    # steps
    for i in range(3):
        sw = 150 - i * 20
        st_ = sp.rect(cx - sw / 2, bot - 18 - i * 14, sw, 15)
        sp.put(st_, quant(0.66 - i * 0.06 + hgrad(sp, cx - sw / 2, cx + sw / 2, 0.08, -0.12), STONE, dith))
        sp.put(sp.rect(cx - sw / 2, bot - 18 - i * 14, sw, 2), STONE[6])
    # lamps, plants
    for lx in (cx - 110, cx + 110):
        sp.put(sp.rect(lx - 3, bot - 160, 6, 100), METAL[1])
        sp.put(sp.rect(lx - 10, bot - 182, 20, 24), METAL[2])
        sp.put(sp.rect(lx - 7, bot - 178, 14, 16), hexrgb('#ffd98a'))
        sp.put(sp.poly([(lx - 13, bot - 182), (lx + 13, bot - 182), (lx, bot - 194)]), METAL[3])
    potted_plant(sp, 46, bot - 60, 1.3, 2)
    potted_plant(sp, W - 46, bot - 60, 1.3, 5)
    outline(sp, SANDST[0] * 0.65, width=2)
    return sp
