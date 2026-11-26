"""V8.6 props for the Jalan Kota lower square (Alun-alun Bawah), drawn from code with the v6 kit rules
(2 texels per world unit, top-left light, coloured outlines, limited ramps, ordered dither).

  balustrade()       stone balustrade segment (96 world wide + overlap) for terrace edges
  balustrade_post()  square pier with a stone urn of flowers, ends a balustrade run at stairs
  pergola()          timber pergola with wisteria, a walk-through shade over a bench
  stair_planter()    tall stone planter with a clipped bay tree, flanks the bottom of a stair

Every builder returns a Sprite whose bottom-centre is the prop's foot point on the map.
Registered in tools/kit_extra.py (hd_balustrade, hd_balustrade_post, hd_pergola, hd_stair_planter).
"""
import numpy as np
from kit import Sprite, quant, bayer, outline, noise, hexrgb, ramp, STONE, LEAF, WOOD
from landmarks import CREAM, ground_shadow, hgrad, vgrad

LIME = ramp('#5d574c', '#7c7568', '#9a9384', '#b5ae9e', '#cdc6b6', '#e1dbcc', '#f2ede2')
WIST = ramp('#4a2f6e', '#6a4596', '#8a63bb', '#a985d6', '#c7a9ea', '#e3d3f6')


def balustrade(W=196, H=74):
    """Cap rail on turned balusters over a plinth; reads as a low stone parapet at terrace edges."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 4, W / 2, 5, 0.25)
    n = noise(H, W, 3, 7)
    sp.put(sp.rect(0, H - 18, W, 12), quant(vgrad(sp, H - 18, H - 6, 0.75, 0.35) + (n - 0.5) * 0.1, LIME, dith))
    sp.put(sp.rect(0, H - 18, W, 2), LIME[5])
    for x in range(8, W - 6, 14):                           # balusters: urn-shaped, lit from the left
        cx = x + 4
        prof = np.abs(sp.xx - cx)
        t = (sp.yy - 26) / max(1, H - 18 - 26)
        r = 3.2 + 2.4 * np.sin(np.clip(t, 0, 1) * np.pi * 1.15) ** 2
        m = (prof <= r) & (sp.yy >= 26) & (sp.yy < H - 18)
        sh = hgrad(sp, cx - 5, cx + 5, 0.92, 0.3) + (n - 0.5) * 0.08
        sp.put(m, quant(sh, LIME, dith))
    sp.put(sp.rect(0, 14, W, 13), quant(vgrad(sp, 14, 27, 0.95, 0.45) + (n - 0.5) * 0.1, LIME, dith))   # cap rail
    sp.put(sp.rect(0, 14, W, 2), LIME[6])
    sp.put(sp.rect(0, 25, W, 2), LIME[1])
    rng = np.random.default_rng(3)
    for _ in range(9):                                      # lichen / moss on the rail and plinth
        x, y = rng.uniform(4, W - 8), rng.choice([18.0, H - 14.0])
        sp.put(sp.ellipse(x, y, rng.uniform(2, 5), 1.6) & (sp.a > 0.5), LEAF[rng.integers(2, 4)])
    outline(sp, hexrgb('#4a453c'), inner=False, width=1)
    return sp


def balustrade_post(W=60, H=150, seed=0):
    """Square pier with a moulded cap and a stone urn of trailing flowers."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    n = noise(H, W, 3, 11 + seed)
    ground_shadow(sp, cx, H - 5, 26, 6)
    sp.put(sp.rect(cx - 20, H - 18, 40, 13), quant(hgrad(sp, cx - 20, cx + 20, 0.8, 0.3), LIME, dith))
    sp.put(sp.rect(cx - 15, 66, 30, H - 84), quant(hgrad(sp, cx - 15, cx + 15, 0.9, 0.3) + (n - 0.5) * 0.12, LIME, dith))
    sp.put(sp.rect(cx - 11, 76, 22, H - 104) & ~sp.rect(cx - 9, 78, 18, H - 108), LIME[2])   # recessed panel
    sp.put(sp.rect(cx - 19, 56, 38, 11), quant(vgrad(sp, 56, 67, 0.95, 0.5), LIME, dith))
    sp.put(sp.rect(cx - 19, 56, 38, 2), LIME[6])
    # urn
    t = (sp.yy - 30) / 26
    r = 7 + 9 * np.sin(np.clip(t, 0, 1) * np.pi * 0.9)
    urn = (np.abs(sp.xx - cx) <= r) & (sp.yy >= 30) & (sp.yy < 56)
    sp.put(urn, quant(hgrad(sp, cx - 16, cx + 16, 0.9, 0.25), CREAM, dith))
    sp.put(sp.rect(cx - 15, 28, 30, 4), CREAM[5])
    rng = np.random.default_rng(seed)
    pal = [ramp('#8a2f4e', '#c4507a', '#ec8fb0', '#ffd0e0'), ramp('#8a5a10', '#d49a24', '#f5cf5a', '#fff0b0'),
           ramp('#3e2a6a', '#7454b0', '#a98ae0', '#e0d0fb')][seed % 3]
    for _ in range(46):                                     # foliage dome + blooms
        a, d = rng.uniform(0, np.pi), rng.uniform(0, 1)
        x, y = cx + np.cos(a) * 18 * d, 28 - np.sin(a) * 16 * d
        sp.put(sp.ellipse(x, y, 3.6, 3), LEAF[rng.integers(2, 6)])
    for _ in range(22):
        x, y = cx + rng.normal(0, 9), 22 + rng.normal(0, 6)
        sp.put(sp.ellipse(x, y, 2.4, 2.2), pal[rng.integers(1, 4)])
    for k in range(4):                                      # trailing stems over the rim
        x = cx + (-13, -6, 7, 13)[k]
        ln = rng.uniform(10, 24)
        sp.put(sp.rect(x, 30, 2, ln), LEAF[2])
        sp.put(sp.ellipse(x + 1, 30 + ln, 2.4, 2.2), pal[2])
    outline(sp, hexrgb('#3c382f'), width=2)
    return sp


def pergola(W=300, H=260, seed=4):
    """Timber pergola, four posts and crossed rafters, draped in wisteria; walk-through."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 10, W / 2 - 10, 14, 0.22)
    beam = ramp('#3a2416', '#563620', '#734a2c', '#8f5f3a', '#aa7a4e', '#c6976a')
    for x in (22, W - 36):                                  # front posts (back posts are hidden behind)
        sp.put(sp.rect(x, 70, 14, H - 82), quant(hgrad(sp, x, x + 14, 0.85, 0.3), beam, dith))
        sp.put(sp.rect(x - 3, H - 16, 20, 6), LIME[3])
    for x in (58, W - 72):
        sp.put(sp.rect(x, 62, 10, H - 112), quant(hgrad(sp, x, x + 10, 0.6, 0.2), beam, dith))
    sp.put(sp.rect(6, 56, W - 12, 14), quant(vgrad(sp, 56, 70, 0.9, 0.4), beam, dith))     # front beam
    sp.put(sp.rect(6, 56, W - 12, 2), beam[5])
    for x in range(14, W - 10, 22):                         # rafters, ends cut at an angle
        sp.put(sp.poly([(x, 40), (x + 9, 40), (x + 9, 58), (x, 62)]), beam[3])
        sp.put(sp.rect(x, 40, 9, 2), beam[5])
    rng = np.random.default_rng(seed)
    n = noise(H, W, 6, seed)
    for _ in range(420):                                    # leaf canopy over the rafters
        x, y = rng.uniform(4, W - 4), rng.uniform(26, 70)
        sp.put(sp.ellipse(x, y, rng.uniform(3, 6), rng.uniform(2.5, 4)), LEAF[rng.integers(2, 6)])
    for k in range(14):                                     # hanging racemes of wisteria
        x = 12 + k * (W - 24) / 13 + rng.uniform(-6, 6)
        ln = rng.uniform(26, 70) if 1 < k < 12 else rng.uniform(40, 110)
        for j in range(int(ln / 3)):
            t = j / max(1, ln / 3)
            y = 62 + j * 3
            r = 5.5 * (1 - t) + 1.5
            sp.put(sp.ellipse(x + np.sin(j * 0.7) * 1.2, y, r, 2.4), WIST[min(5, 1 + int((1 - t) * 3 + n[int(min(H - 1, y)), int(min(W - 1, x))] * 2))])
    outline(sp, hexrgb('#22160f'), inner=False, width=1)
    return sp


def stair_planter(W=84, H=160, seed=2):
    """Square stone planter with a clipped bay ball tree, flanks the foot of a staircase."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 34, 7)
    sp.put(sp.rect(cx - 28, H - 44, 56, 38), quant(hgrad(sp, cx - 28, cx + 28, 0.9, 0.3) + (noise(H, W, 3, seed) - 0.5) * 0.1, LIME, dith))
    sp.put(sp.rect(cx - 31, H - 50, 62, 8), LIME[5])
    sp.put(sp.rect(cx - 31, H - 50, 62, 2), LIME[6])
    sp.put(sp.rect(cx - 2, 62, 5, H - 110), WOOD[2] if len(WOOD) > 2 else hexrgb('#6b4a30'))
    rng = np.random.default_rng(seed)
    ball = sp.ellipse(cx, 44, 30, 32)
    for _ in range(360):
        a, d = rng.uniform(0, 2 * np.pi), np.sqrt(rng.random())
        x, y = cx + np.cos(a) * 28 * d, 44 + np.sin(a) * 30 * d
        lit = 0.55 - 0.35 * (np.cos(a) * d * 0.7 + np.sin(a) * d * 0.7)
        sp.put(sp.ellipse(x, y, 3.4, 3), LEAF[int(np.clip(lit * 6, 1, 5))])
    sp.put(ball & (sp.a < 0.5), LEAF[2])
    outline(sp, hexrgb('#2c3a24'), width=2)
    return sp
