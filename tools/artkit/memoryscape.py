"""V8.8 landmarks for three story dream maps, drawn from code with the v6 kit rules (2 texels per world
unit, top-left light, coloured outlines, limited ramps, ordered dither). Bottom-centre = foot point.

Memory Garden (prologue, "The Beginning of Us"):
  memory_gate()      the "Gerbang pulang": two pillars holding a giant open book whose pages glow
  memory_book()      a lectern with the shared memory book: a flower on one page, a star on the other
  shard_pedestal()   small stone plinth under each of the three light shards
Arsip Memudar (chapter 5, the archive where unspoken sentences turn to fog):
  archive_shelf()    a tall archive shelf whose top dissolves into mist
  archive_desk()     the archive desk with the envelope "Untuk Sari" that was never sent
  card_catalog()     library card catalogue (the echo of the library card)
  paper_pile()       a little drift of loose pages and bound files
Kenangan Gazebo (chapter 6, Taman Kota forty years ago):
  poster_column()    an old advertising column with faded posters
  lamp_old()         a cast-iron gas lamp of that time (replaces the modern park lamps there)

Registered in tools/kit_extra.py; placed by tools/worldgen/dream_hd.py.
"""
import numpy as np
from kit import Sprite, quant, bayer, outline, noise, hexrgb, ramp, STONE, LEAF, WOOD
from landmarks import GOLD, CREAM, ground_shadow, glow, hgrad, vgrad
from dreamscape import MOONSTONE, STARLIGHT, PEARL, _star

PAGE = ramp('#9c8f78', '#bfb299', '#d9cdb4', '#ece2cb', '#f8f1e0', '#fffaf0')
INK = hexrgb('#4a3a5e')
PETAL = ramp('#8a2f5e', '#c4508a', '#e88ab4', '#ffc8de')
OAK = ramp('#2e1c12', '#45291a', '#5e3a24', '#7a4e31', '#956441', '#b07e55')
FOG = hexrgb('#d8d6e6')
IRON = ramp('#14171c', '#20252c', '#2e353e', '#414a55', '#5a6572')


def _open_book(sp, cx, top, w, h, dith, flower=True, star=True, glow_col=None):
    """Open book seen from the front-top: two curved pages meeting at a spine."""
    for side in (-1, 1):
        x0 = cx if side > 0 else cx - w / 2
        pts = [(cx, top + 6), (cx + side * w * 0.25, top - 2), (cx + side * w / 2, top + 2),
               (cx + side * w / 2, top + h), (cx + side * w * 0.25, top + h - 6), (cx, top + h + 2)]
        pg = sp.poly(pts)
        sh = hgrad(sp, cx - w / 2, cx + w / 2, 0.95, 0.55) if side < 0 else hgrad(sp, cx, cx + w / 2, 0.7, 0.92)
        sp.put(pg, quant(sh, PAGE, dith))
        for k in range(4 if not (flower if side < 0 else star) else 2):        # ruled lines
            y = top + h * (0.62 + k * 0.1)
            sp.put(sp.rect(x0 + w * 0.08, y, w * 0.34, 1.2) & pg, PAGE[1])
    sp.put(sp.rect(cx - 1, top + 4, 2, h - 2), PAGE[0])                          # spine
    if flower:
        fx, fy = cx - w * 0.25, top + h * 0.34
        for k in range(5):
            a = k * 2 * np.pi / 5 - np.pi / 2
            sp.put(sp.ellipse(fx + np.cos(a) * w * 0.05, fy + np.sin(a) * w * 0.05, w * 0.045, w * 0.04), PETAL[2])
        sp.put(sp.ellipse(fx, fy, w * 0.025, w * 0.025), GOLD[4])
        sp.put(sp.rect(fx - 0.6, fy + w * 0.06, 1.5, h * 0.22), LEAF[3])
    if star:
        sp.put(_star(sp, cx + w * 0.25, top + h * 0.36, w * 0.09, w * 0.04), GOLD[4])
    if glow_col is not None:
        glow(sp, cx, top + h / 2, w * 0.7, glow_col, 0.35)


def memory_gate(W=360, H=330):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    for px in (cx - 132, cx + 132):                                 # pillars
        ground_shadow(sp, px, H - 8, 32, 8)
        sp.put(sp.rect(px - 26, H - 32, 52, 26), quant(hgrad(sp, px - 26, px + 26, 0.85, 0.3), MOONSTONE, dith))
        sp.put(sp.rect(px - 26, H - 32, 52, 2), MOONSTONE[6])
        sp.put(sp.rect(px - 18, 150, 36, H - 182), quant(hgrad(sp, px - 18, px + 18, 0.95, 0.3) + (noise(H, W, 3, int(px)) - 0.5) * 0.1, MOONSTONE, dith))
        sp.put(sp.rect(px - 24, 138, 48, 14), quant(vgrad(sp, 138, 152, 0.95, 0.45), MOONSTONE, dith))
        rng = np.random.default_rng(int(px))
        for _ in range(60):                                         # climbing flowering vine
            t = rng.random()
            y = H - 40 - t * (H - 200)
            x = px + np.sin(t * 11 + px) * 16
            sp.put(sp.ellipse(x, y, 4, 3.2), LEAF[rng.integers(2, 6)])
            if rng.random() < 0.25:
                sp.put(sp.ellipse(x + 2, y - 1, 2.2, 2.2), PETAL[rng.integers(1, 4)])
    # the giant open book, standing on the pillars, pages glowing: flower (Sofia) and star (Arland)
    _open_book(sp, cx, 38, 300, 104, dith, glow_col=hexrgb('#fff2c8'))
    sp.put(sp.rect(cx - 150, 140, 300, 6), quant(hgrad(sp, cx - 150, cx + 150, 0.9, 0.4), OAK, dith))  # cover edge
    for k in range(7):                                              # light motes rising from the pages
        x = cx - 110 + k * 37
        sp.put(sp.ellipse(x, 22 - (k % 3) * 7, 2.4, 2.4), STARLIGHT[4])
        glow(sp, x, 22 - (k % 3) * 7, 10, hexrgb('#fff3c0'), 0.45)
    # a soft curtain of light between the pillars: the way home
    curtain = sp.rect(cx - 112, 150, 224, H - 182)
    t = (sp.yy - 150) / (H - 182)
    a = (0.22 + 0.12 * np.sin(sp.xx * 0.09)) * (1 - np.clip(t, 0, 1) * 0.7)
    free = curtain & (sp.a < 0.5)
    sp.rgb[free] = hexrgb('#fff1cf')
    sp.a[free] = np.maximum(sp.a[free], a[free])
    outline(sp, hexrgb('#1e1a33'), width=2)
    return sp


def memory_book(W=120, H=150):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 6, 36, 7)
    sp.put(sp.rect(cx - 30, H - 20, 60, 14), quant(hgrad(sp, cx - 30, cx + 30, 0.85, 0.3), MOONSTONE, dith))
    sp.put(sp.poly([(cx - 12, H - 20), (cx + 12, H - 20), (cx + 8, 70), (cx - 8, 70)]),
           quant(hgrad(sp, cx - 12, cx + 12, 0.95, 0.3), MOONSTONE, dith))
    sp.put(sp.poly([(cx - 46, 74), (cx + 46, 74), (cx + 40, 56), (cx - 40, 56)]), quant(hgrad(sp, cx - 46, cx + 46, 0.9, 0.35), OAK, dith))
    _open_book(sp, cx, 22, 96, 38, dith, glow_col=hexrgb('#fff0c4'))
    outline(sp, hexrgb('#1e1a33'), width=2)
    return sp


def shard_pedestal(W=80, H=60):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 30, 6)
    sp.put(sp.poly([(cx - 30, H - 8), (cx + 30, H - 8), (cx + 22, H - 30), (cx - 22, H - 30)]),
           quant(hgrad(sp, cx - 30, cx + 30, 0.9, 0.3) + (noise(H, W, 3, 5) - 0.5) * 0.1, MOONSTONE, dith))
    sp.put(sp.ellipse(cx, H - 30, 22, 6), MOONSTONE[5])
    ring = sp.ellipse(cx, H - 30, 16, 4) & ~sp.ellipse(cx, H - 30, 12, 2.8)
    sp.put(ring, STARLIGHT[3])
    glow(sp, cx, H - 32, 30, hexrgb('#e8ecff'), 0.35)
    outline(sp, hexrgb('#1e1a33'), width=1)
    return sp


def archive_shelf(W=150, H=300, seed=0):
    """Tall shelf of files and bound ledgers; the upper part fades into fog."""
    sp = Sprite(W, H)
    dith = bayer(H, W)
    rng = np.random.default_rng(seed)
    ground_shadow(sp, W / 2, H - 6, W / 2 - 4, 8, 0.3)
    x0, x1 = 8, W - 8
    sp.put(sp.rect(x0, 10, x1 - x0, H - 18), quant(hgrad(sp, x0, x1, 0.55, 0.2), OAK, dith))
    for x in (x0, x1 - 10):
        sp.put(sp.rect(x, 10, 10, H - 18), quant(hgrad(sp, x, x + 10, 0.95, 0.5), OAK, dith))
    spines = [('#6e4a6a', '#8a6086'), ('#44607a', '#5c7c98'), ('#7a6a48', '#9a8a62'), ('#5a7058', '#748c70'),
              ('#8a5a4a', '#a8735f'), ('#d8cfb8', '#ece4cf')]
    for y in range(28, H - 20, 40):                                 # shelf boards with files and ledgers
        sp.put(sp.rect(x0 + 10, y + 32, x1 - x0 - 20, 5), OAK[4])
        x = x0 + 12
        while x < x1 - 14:
            bw = rng.integers(5, 11)
            bh = rng.integers(20, 31)
            lo, hi = spines[rng.integers(0, len(spines))]
            b = sp.rect(x, y + 32 - bh, bw, bh)
            sp.put(b, hexrgb(hi))
            sp.put(sp.rect(x + bw - 2, y + 32 - bh, 2, bh), hexrgb(lo))
            if rng.random() < 0.4:
                sp.put(sp.rect(x + 1, y + 32 - bh + 5, bw - 2, 2), GOLD[3])
            x += bw + (1 if rng.random() < 0.85 else rng.integers(4, 12))
    # fog: the top dissolves, loose pages drift out of it
    t = np.clip((sp.yy - 10) / (H * 0.55), 0, 1)
    fade = (1 - t) ** 1.6 * 0.85
    m = sp.a > 0.5
    sp.rgb[m] = sp.rgb[m] * (1 - fade[m, None]) + np.asarray(FOG) * fade[m, None]
    n = noise(H, W, 7, seed + 3)
    sp.a[m] = 1.0 - np.clip(fade[m] * 1.15 + (n[m] - 0.5) * 0.5, 0, 0.94)    # the top thins out into the fog
    for _ in range(5):
        px, py = rng.uniform(12, W - 20), rng.uniform(0, H * 0.35)
        sp.put(sp.poly([(px, py), (px + 9, py + 2), (px + 8, py + 13), (px - 1, py + 11)]), PAGE[4], 0.85)
    return sp


def archive_desk(W=200, H=150):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 6, W / 2 - 8, 9, 0.3)
    for x in (16, W - 28):                                          # legs
        sp.put(sp.rect(x, 74, 12, H - 82), quant(hgrad(sp, x, x + 12, 0.8, 0.3), OAK, dith))
    sp.put(sp.rect(14, 74, W - 28, 30), quant(hgrad(sp, 14, W - 14, 0.75, 0.35), OAK, dith))     # drawers
    for x in (30, W / 2 + 10):
        sp.put(sp.rect(x, 82, W / 2 - 40, 14) & ~sp.rect(x + 2, 84, W / 2 - 44, 10), OAK[1])
        sp.put(sp.ellipse(x + (W / 2 - 40) / 2, 89, 2.5, 2.5), GOLD[3])
    sp.put(sp.poly([(6, 74), (W - 6, 74), (W - 14, 56), (14, 56)]), quant(hgrad(sp, 6, W - 6, 0.95, 0.5), OAK, dith))  # top
    sp.put(sp.rect(30, 44, 36, 14), hexrgb('#d8cfb8')); sp.put(sp.rect(32, 36, 32, 10), hexrgb('#c4b89c'))   # file stack
    sp.put(sp.rect(150, 30, 4, 28), IRON[3]); sp.put(sp.ellipse(152, 28, 12, 7), GOLD[3])                   # lamp
    glow(sp, 152, 38, 34, hexrgb('#ffdf9a'), 0.35)
    # the envelope "Untuk Sari", alone in the middle of the desk
    env = sp.poly([(84, 66), (128, 64), (130, 50), (86, 52)])
    sp.put(env, PAGE[5])
    sp.put(sp.poly([(86, 52), (130, 50), (108, 60)]), PAGE[3])
    sp.put(sp.ellipse(108, 60, 3.2, 3.2), hexrgb('#b8343a'))
    for k in range(3):                                              # handwriting on the envelope ("Untuk Sari")
        sp.put(sp.rect(94 + k * 3, 56 - k * 0.3, 2 + (k == 1) * 10, 1.2), INK)
    outline(sp, hexrgb('#24180f'), width=2)
    return sp


def card_catalog(W=110, H=150):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    ground_shadow(sp, W / 2, H - 6, W / 2 - 4, 7, 0.3)
    sp.put(sp.rect(10, 20, W - 20, H - 30), quant(hgrad(sp, 10, W - 10, 0.8, 0.35), OAK, dith))
    sp.put(sp.rect(6, 14, W - 12, 8), OAK[5])
    for r in range(5):
        for c in range(3):
            x, y = 16 + c * 27, 28 + r * 22
            sp.put(sp.rect(x, y, 23, 18), quant(vgrad(sp, y, y + 18, 0.8, 0.45), OAK, dith))
            sp.put(sp.rect(x + 7, y + 4, 9, 4), PAGE[4])
            sp.put(sp.ellipse(x + 11.5, y + 12, 2, 2), GOLD[3])
    # one drawer pulled open with a card sticking up
    sp.put(sp.rect(43, 72, 23, 14), OAK[2]); sp.put(sp.rect(47, 62, 15, 12), PAGE[5])
    sp.put(sp.rect(49, 65, 11, 1), INK); sp.put(sp.rect(49, 68, 8, 1), INK)
    outline(sp, hexrgb('#24180f'), width=2)
    return sp


def paper_pile(W=80, H=46, seed=3):
    sp = Sprite(W, H)
    rng = np.random.default_rng(seed)
    ground_shadow(sp, W / 2, H - 5, W / 2 - 6, 5, 0.25)
    for k in range(5):                                              # bound files
        y = H - 10 - k * 5
        x = 14 + rng.uniform(-4, 4)
        sp.put(sp.rect(x, y, 34, 5), hexrgb(('#6e4a6a', '#44607a', '#7a6a48', '#d8cfb8', '#5a7058')[k]))
        sp.put(sp.rect(x, y, 34, 1), hexrgb('#f0e8d6'))
    for _ in range(6):                                              # loose pages
        px, py = rng.uniform(4, W - 18), rng.uniform(H - 18, H - 8)
        a = rng.uniform(-0.5, 0.5)
        pts = [(px + np.cos(a) * dx - np.sin(a) * dy, py + np.sin(a) * dx + np.cos(a) * dy) for dx, dy in ((0, 0), (14, 0), (14, 9), (0, 9))]
        sp.put(sp.poly(pts), PAGE[rng.integers(3, 6)])
    outline(sp, hexrgb('#3a3128'), inner=False, width=1)
    return sp


def poster_column(W=90, H=230):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 6, 32, 7)
    sp.put(sp.rect(cx - 28, H - 22, 56, 16), quant(hgrad(sp, cx - 28, cx + 28, 0.8, 0.3), IRON, dith))
    body = sp.rect(cx - 24, 40, 48, H - 62)
    sp.put(body, quant(hgrad(sp, cx - 24, cx + 24, 0.9, 0.3), CREAM, dith))
    posters = [('#c9a66b', '#7a3a2a'), ('#a8b8a0', '#2e4a3a'), ('#d8b8a0', '#6a2a3a'), ('#b8b0c8', '#3a3a6a')]
    for k, (bg, ink) in enumerate(posters):                         # faded, slightly sepia posters
        y = 50 + k * 40
        x = cx - 22 + (k % 2) * 6
        pw = 30 + (k % 2) * 8
        p = sp.rect(x, y, pw, 34) & body
        sh = hgrad(sp, cx - 24, cx + 24, 1.0, 0.75)
        sp.rgb[p] = np.asarray(hexrgb(bg)) * sh[p, None]
        sp.put(sp.rect(x + 3, y + 4, pw - 6, 3) & p, hexrgb(ink))
        sp.put(sp.rect(x + 3, y + 10, pw - 12, 12) & p, hexrgb(ink) * 0.6 + np.asarray(hexrgb(bg)) * 0.4)
        sp.put(sp.rect(x + pw - 7, y + 26, 5, 6) & p, PAGE[4])      # torn corner
    sp.put(sp.rect(cx - 30, 30, 60, 12), quant(vgrad(sp, 30, 42, 0.9, 0.4), IRON, dith))
    sp.put(sp.ellipse(cx, 28, 26, 10) & (sp.yy < 30), quant(hgrad(sp, cx - 26, cx + 26, 0.9, 0.35), IRON, dith))
    sp.put(sp.ellipse(cx, 14, 5, 5), GOLD[3]); sp.put(sp.rect(cx - 1, 16, 2, 8), IRON[3])
    outline(sp, hexrgb('#14171c'), width=2)
    return sp


def lamp_old(W=70, H=170):
    sp = Sprite(W, H)
    dith = bayer(H, W)
    cx = W / 2
    ground_shadow(sp, cx, H - 5, 18, 5)
    sp.put(sp.poly([(cx - 14, H - 6), (cx + 14, H - 6), (cx + 6, H - 30), (cx - 6, H - 30)]), quant(hgrad(sp, cx - 14, cx + 14, 0.85, 0.3), IRON, dith))
    sp.put(sp.rect(cx - 3.5, 56, 7, H - 86), quant(hgrad(sp, cx - 4, cx + 4, 0.9, 0.3), IRON, dith))
    for y in (H - 70, 90):                                          # collars
        sp.put(sp.rect(cx - 6, y, 12, 5), IRON[3])
    sp.put(sp.rect(cx - 16, 50, 32, 4), IRON[2])                    # ladder bar
    glass = sp.poly([(cx - 13, 20), (cx + 13, 20), (cx + 9, 48), (cx - 9, 48)])
    sp.put(glass, hexrgb('#ffd98a'))
    sp.put(glass & (sp.xx < cx - 4), hexrgb('#ffeab8'))
    for x in (cx - 13, cx - 1, cx + 11):
        sp.put(sp.rect(x, 20, 2, 28) & glass, IRON[1])
    sp.put(sp.poly([(cx - 17, 21), (cx + 17, 21), (cx, 6)]), quant(hgrad(sp, cx - 17, cx + 17, 0.9, 0.3), IRON, dith))
    sp.put(sp.ellipse(cx, 5, 3, 3), IRON[4])
    sp.put(sp.rect(cx - 10, 48, 20, 4), IRON[2])
    glow(sp, cx, 34, 34, hexrgb('#ffcf7a'), 0.4)
    outline(sp, hexrgb('#0c0e11'), width=1)
    return sp
