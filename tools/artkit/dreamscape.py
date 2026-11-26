"""V8.2 landmarks for the dream maps, drawn from code with the v6 kit rules (2 texels per world unit,
top-left light, coloured outlines, limited ramps, ordered dither). Bottom-centre = foot point.

  star_lantern_post()  Memory Bridge: slim stone post with a star-shaped lantern (bridge rails, paths)
  star_gate()          Memory Bridge: constellation gate at the arrival plaza (walk-through)
  hall_tomorrow()      Hall of Tomorrow: the "Balai Hari Esok" itself, behind its three arches
  rain_pavilion()      Rain Garden: open pavilion with a glass roof and rain chains (walk-through)

Registered in tools/kit_extra.py; placed by tools/worldgen/dream_hd.py.
"""
import numpy as np
from kit import Sprite, quant, bayer, outline, noise, hexrgb, ramp, STONE, METAL, LEAF, WOOD
from landmarks import GOLD, SLATE, CREAM, ground_shadow, glow, hgrad, vgrad

MOONSTONE = ramp('#3e3a5e', '#514c74', '#67628a', '#7f7aa2', '#9893b8', '#b4b0cf', '#d2cfe6')
STARLIGHT = ramp('#6a7bd0', '#8ea0ea', '#b4c4f8', '#d8e2ff', '#f4f7ff')
PEARL = ramp('#6d6a86', '#8a87a2', '#a9a6be', '#c6c4d8', '#e0def0', '#f3f2fa', '#ffffff')
LILAC_ROOF = ramp('#2b2346', '#3a2f5e', '#4c3f78', '#615290', '#7a69a8', '#9787c2', '#b7aad8')
GLASS = ramp('#3d5f6e', '#4f7a88', '#6697a3', '#83b4bd', '#a8d0d6', '#d0eaee')
COPPER = ramp('#2c3d36', '#3b5248', '#4f6b5c', '#678772', '#82a38b', '#a2bfa6')


def _star(sp, cx, cy, r_out, r_in, n=5, rot=-np.pi / 2):
    pts = []
    for k in range(n * 2):
        r = r_out if k % 2 == 0 else r_in
        a = rot + k * np.pi / n
        pts.append((cx + np.cos(a) * r, cy + np.sin(a) * r))
    return sp.poly(pts)


def star_lantern_post(W=72, H=176):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 18, 5)
    sp.put(sp.rect(cx - 13, H - 20, 26, 16), quant(hgrad(sp, cx - 13, cx + 13, 0.85, 0.3), MOONSTONE, dith))
    sp.put(sp.rect(cx - 13, H - 20, 26, 2), MOONSTONE[6])
    sp.put(sp.rect(cx - 6, 64, 12, H - 82), quant(hgrad(sp, cx - 6, cx + 6, 0.95, 0.35) + (noise(H, W, 3, 4) - 0.5) * 0.1, MOONSTONE, dith))
    for y in (78, H - 36):
        sp.put(sp.rect(cx - 9, y, 18, 5), MOONSTONE[5])
    # crescent bracket and the star lantern
    ring = sp.ellipse(cx, 44, 24, 24) & ~sp.ellipse(cx + 7, 40, 21, 21) & (sp.yy < 62)
    sp.put(ring, quant(hgrad(sp, cx - 24, cx + 24, 1.0, 0.45), GOLD, dith))
    star = _star(sp, cx, 40, 17, 7.5)
    sp.put(star, quant(np.clip(1.0 - np.hypot(sp.xx - cx + 3, sp.yy - 37) / 20, 0, 1) * 0.6 + 0.4, STARLIGHT, dith))
    sp.put(_star(sp, cx, 40, 7, 3), STARLIGHT[4])
    glow(sp, cx, 40, 34, hexrgb('#b9c8ff'), 0.5)
    for k, (dx, dy) in enumerate(((-20, 12), (19, 6), (-12, -10), (14, -16))):   # tiny orbiting sparks
        sp.put(sp.ellipse(cx + dx, 40 + dy, 1.6, 1.6), STARLIGHT[4])
    outline(sp, hexrgb('#1e1a33'), width=1)
    return sp


def star_gate(W=300, H=300):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    for px in (cx - 112, cx + 112):                                # two pillars
        ground_shadow(sp, px, H - 8, 30, 7)
        sp.put(sp.rect(px - 26, H - 30, 52, 24), quant(hgrad(sp, px - 26, px + 26, 0.85, 0.3), MOONSTONE, dith))
        sp.put(sp.rect(px - 26, H - 30, 52, 2), MOONSTONE[6])
        shaft = sp.rect(px - 18, 86, 36, H - 116)
        bands = (((sp.yy.astype(int) - 86) % 34) < 3) * -0.18
        sp.put(shaft, quant(hgrad(sp, px - 18, px + 18, 0.95, 0.3) + bands + (noise(H, W, 3, int(px)) - 0.5) * 0.1, MOONSTONE, dith))
        for k in range(3):                                         # carved constellation dots
            y = 120 + k * 52
            for j, (dx, dy) in enumerate(((-6, 0), (5, 10), (-2, 22), (7, 30))):
                sp.put(sp.ellipse(px + dx, y + dy, 2.2, 2.2), STARLIGHT[3])
            for (a, b) in (((-6, 0), (5, 10)), ((5, 10), (-2, 22)), ((-2, 22), (7, 30))):
                for t in np.linspace(0, 1, 12):
                    sp.rgb[int(y + a[1] + (b[1] - a[1]) * t), int(px + a[0] + (b[0] - a[0]) * t)] = STARLIGHT[1]
    # lintel: arched beam with a crescent and five stars (the five constellations)
    beam = sp.poly([(cx - 150, 92), (cx + 150, 92), (cx + 140, 70), (cx - 140, 70)])
    sp.put(beam, quant(hgrad(sp, cx - 150, cx + 150, 0.95, 0.35), MOONSTONE, dith))
    sp.put(sp.rect(cx - 150, 90, 300, 4), MOONSTONE[1])
    arch = sp.ellipse(cx, 96, 108, 52) & ~sp.ellipse(cx, 100, 96, 44) & (sp.yy < 96)
    sp.put(arch, quant(hgrad(sp, cx - 108, cx + 108, 1.0, 0.4), GOLD, dith))
    moon = sp.ellipse(cx, 36, 26, 26) & ~sp.ellipse(cx + 11, 30, 22, 22)
    sp.put(moon, quant(np.full((H, W), 0.85), PEARL))
    glow(sp, cx, 36, 50, hexrgb('#dfe6ff'), 0.25)
    for k, x in enumerate(np.linspace(cx - 120, cx + 120, 5)):
        y = 80 - (0 if k in (0, 4) else 10 if k in (1, 3) else 14)
        sp.put(_star(sp, x, y, 9, 4), STARLIGHT[4])
        glow(sp, x, y, 16, hexrgb('#b9c8ff'), 0.4)
    outline(sp, hexrgb('#1e1a33'), width=2)
    return sp


def hall_tomorrow(W=720, H=600):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 10, 340, 18, 0.35)
    # three broad steps
    for i, (hw, y0) in enumerate([(330, H - 30), (310, H - 52), (290, H - 74)]):
        sp.put(sp.rect(cx - hw, y0, hw * 2, 22), quant(hgrad(sp, cx - hw, cx + hw, 0.9, 0.35) + (noise(H, W, 3, 7 + i) - 0.5) * 0.08, PEARL, dith))
        sp.put(sp.rect(cx - hw, y0, hw * 2, 2), PEARL[6])
    # back wall, warm light from the open hall
    wall = sp.rect(cx - 260, 210, 520, H - 284)
    sp.put(wall, quant(vgrad(sp, 210, H - 74, 0.55, 0.85) + (noise(H, W, 4, 3) - 0.5) * 0.08, CREAM, dith))
    for k, dx in enumerate((-150, 0, 150)):                         # three tall doors: three futures
        dw, top = (86, 286) if dx == 0 else (72, 306)
        door = sp.rect(cx + dx - dw / 2, top, dw, H - 74 - top) | sp.ellipse(cx + dx, top, dw / 2, dw / 2)
        sp.put(door, quant(vgrad(sp, top - dw / 2, H - 74, 1.0, 0.65), ramp('#d98a2c', '#f5b44a', '#ffd776', '#fff0b8', '#fffbe6'), dith))
        sp.put(sp.ellipse(cx + dx, top, dw / 2 + 7, dw / 2 + 7) & ~sp.ellipse(cx + dx, top, dw / 2, dw / 2) & (sp.yy < top), GOLD[3])
        glow(sp, cx + dx, (top + H - 74) / 2, 90, hexrgb('#ffe2a0'), 0.18)
        sym = [(lambda m: _star(sp, cx + dx, top - 2, 12, 5)), (lambda m: sp.ellipse(cx + dx, top - 2, 11, 11) & ~sp.ellipse(cx + dx + 5, top - 5, 9, 9)),
               (lambda m: sp.ellipse(cx + dx - 6, top - 2, 7, 7) | sp.ellipse(cx + dx + 6, top - 2, 7, 7))][k](None)
        sp.put(sym, GOLD[5])
    # colonnade: six columns
    for k in range(6):
        x = cx - 250 + k * 100
        col = sp.rect(x - 15, 196, 30, H - 270)
        flute = (np.sin((sp.xx - x) * 0.8) * 0.5 + 0.5) * 0.14
        sp.put(col, quant(hgrad(sp, x - 15, x + 15, 1.0, 0.3) + flute, PEARL, dith))
        sp.put(sp.rect(x - 22, 186, 44, 12), PEARL[5])
        sp.put(sp.rect(x - 22, H - 86, 44, 12), PEARL[4])
        if k in (0, 5):                                            # wisteria on the end columns
            rng = np.random.default_rng(k + 3)
            for j in range(90):
                yy = 200 + rng.uniform(0, 160)
                sp.put(sp.ellipse(x + rng.normal(0, 10), yy, 4, 5), ramp('#5c44a0', '#8a72cf', '#bfaef0')[rng.integers(0, 3)])
                if j % 3 == 0:
                    sp.put(sp.ellipse(x + rng.normal(0, 12), yy - 4, 4, 3), LEAF[rng.integers(2, 5)])
    # entablature + pediment with a sun rising over the horizon
    sp.put(sp.rect(cx - 290, 160, 580, 30), quant(hgrad(sp, cx - 290, cx + 290, 0.95, 0.4), PEARL, dith))
    sp.put(sp.rect(cx - 290, 160, 580, 3), PEARL[6])
    sp.put(sp.rect(cx - 290, 186, 580, 4), PEARL[1])
    ped = sp.poly([(cx - 300, 162), (cx + 300, 162), (cx, 60)])
    sp.put(ped, quant(hgrad(sp, cx - 300, cx + 300, 0.95, 0.3), PEARL, dith))
    inner = sp.poly([(cx - 250, 152), (cx + 250, 152), (cx, 78)])
    sp.put(inner, quant(vgrad(sp, 78, 152, 0.7, 0.45), PEARL, dith))
    sun = sp.ellipse(cx, 150, 46, 46) & (sp.yy < 150)
    sp.put(sun, quant(vgrad(sp, 104, 150, 1.0, 0.6), GOLD, dith))
    for k in range(9):
        a = np.pi + (k + 0.5) * np.pi / 9
        for t in np.linspace(52, 74, 10):
            sp.put(sp.ellipse(cx + np.cos(a) * t, 150 + np.sin(a) * t, 1.6, 1.6), GOLD[4])
    # roof ridge
    roof = sp.poly([(cx - 312, 166), (cx + 312, 166), (cx + 4, 52), (cx - 4, 52)]) & ~ped
    sp.put(sp.poly([(cx - 312, 166), (cx - 300, 162), (cx, 60), (cx, 50)]), LILAC_ROOF[4])
    sp.put(sp.poly([(cx + 312, 166), (cx + 300, 162), (cx, 60), (cx, 50)]), LILAC_ROOF[2])
    sp.put(sp.ellipse(cx, 50, 9, 9), GOLD[4])
    sp.put(sp.poly([(cx, 14), (cx + 6, 42), (cx - 6, 42)]), GOLD[5])
    outline(sp, hexrgb('#2a2440'), width=2)
    return sp


def rain_pavilion(W=360, H=380):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 12, 160, 14, 0.3)
    sp.put(sp.ellipse(cx, H - 22, 150, 20), quant(hgrad(sp, cx - 150, cx + 150, 0.85, 0.35), STONE, dith))
    sp.put(sp.ellipse(cx, H - 26, 146, 17), STONE[5])
    # four slim copper posts (front pair lower on the picture)
    for px, top, bot in ((cx - 118, 150, H - 40), (cx + 118, 150, H - 40), (cx - 74, 142, H - 52), (cx + 74, 142, H - 52)):
        sp.put(sp.rect(px - 6, top, 12, bot - top), quant(hgrad(sp, px - 6, px + 6, 0.95, 0.3), COPPER, dith))
        sp.put(sp.rect(px - 9, bot - 8, 18, 8), COPPER[2])
    # rain chains: little cups strung from the roof corners
    for px in (cx - 140, cx + 140):
        for y in range(150, H - 44, 14):
            sp.put(sp.ellipse(px, y, 4, 5) & ~sp.ellipse(px, y - 2, 2.5, 3), COPPER[4])
        sp.put(sp.ellipse(px, H - 38, 12, 6), STONE[2])
        sp.put(sp.ellipse(px, H - 39, 9, 4), hexrgb('#46699a'))
    # hanging lantern in the middle
    sp.put(sp.rect(cx - 1, 140, 2, 70), METAL[2])
    lan = sp.ellipse(cx, 226, 15, 20)
    sp.put(lan, quant(vgrad(sp, 206, 246, 1.0, 0.6), ramp('#d98a2c', '#f5b44a', '#ffd776', '#fff0b8', '#fffbe6'), dith))
    sp.put(sp.rect(cx - 9, 204, 18, 4) | sp.rect(cx - 9, 244, 18, 4), COPPER[2])
    glow(sp, cx, 226, 70, hexrgb('#ffd37a'), 0.35)
    # roof: copper frame, glass panes catching the sky, a curled finial
    roof = sp.poly([(cx - 164, 156), (cx + 164, 156), (cx + 92, 66), (cx - 92, 66)])
    sp.put(roof, quant(hgrad(sp, cx - 164, cx + 164, 1.0, 0.35) + (vgrad(sp, 66, 156, 0.0, 0.2) - 0.1), GLASS, dith))
    for k in range(-4, 5):                                          # mullions
        x0, x1 = cx + k * 41, cx + k * 23
        for t in np.linspace(0, 1, 60):
            sp.put(sp.ellipse(x0 + (x1 - x0) * t, 156 - 90 * t, 1.4, 1.4), COPPER[3])
    for y in (96, 126):
        w = 92 + (y - 66) / 90 * 72
        sp.put(sp.rect(cx - w, y, w * 2, 3), COPPER[3])
    sp.put(sp.rect(cx - 168, 154, 336, 8), quant(hgrad(sp, cx - 168, cx + 168, 0.95, 0.35), COPPER, dith))
    sp.put(sp.poly([(cx - 96, 68), (cx + 96, 68), (cx + 60, 40), (cx - 60, 40)]), quant(hgrad(sp, cx - 96, cx + 96, 0.95, 0.35), COPPER, dith))
    sp.put(sp.ellipse(cx, 30, 10, 12) & ~sp.ellipse(cx + 4, 28, 6, 8), COPPER[5])
    rng = np.random.default_rng(4)
    for k in range(22):                                              # raindrops beading on the glass
        x = rng.uniform(cx - 140, cx + 140)
        y = rng.uniform(80, 150)
        if roof[int(y), int(x)]:
            sp.put(sp.ellipse(x, y, 1.6, 2.2), GLASS[5])
    for k in range(70):                                              # ivy creeping up the back posts
        t = k / 70
        for px in (cx - 118, cx + 118):
            sp.put(sp.ellipse(px + np.sin(t * 9 + px) * 6, H - 44 - t * 180, 4.5, 3.5), LEAF[rng.integers(1, 6)])
    outline(sp, hexrgb('#1a2a26'), width=2)
    return sp


if __name__ == '__main__':
    import sys
    from pathlib import Path
    out = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp')
    for n, f in (('star_lantern_post', star_lantern_post), ('star_gate', star_gate), ('hall_tomorrow', hall_tomorrow),
                 ('rain_pavilion', rain_pavilion)):
        f().save(out / ('%s.png' % n))
        print(n)
