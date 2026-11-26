"""V8.4: dialogue portraits for Arland & Sofia from their GLB busts (tests/charrender/render_portrait.tscn).

The model has one face (a soft smile), so the other expressions are painted over it at the base
resolution (88x110, pixel art), then doubled to 176x220 like the old portraits: closed happy eyes,
open laugh, blush, worried / sad brows, tears, a sweat drop, wide surprised eyes, hearts.
Output: assets/characters/<c>/portraits/<expression>.png (old art moved to portraits_v7/, kept out
of the APK). Usage: python3 tools/portraits.py <portraitframes dir> [--sheet out.png]
"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BW, BH = 88, 110
BG = (254, 245, 241)
BORDER = {'arland': (158, 149, 204), 'sofia': (231, 151, 184)}
# feature anchors measured on the base render (x, y in base pixels)
FACE = {
    # eye_r: drawn eye shape; cover: area painted over before drawing (whole eye incl. lashes)
    'arland': dict(eyes=[(32, 61), (56, 61)], eye_r=(5, 4), cover=(6, 5), mouth=(43, 73), mouth_w=8, brow_y=51,
                   cheeks=[(24, 68), (63, 68)], glasses=True),
    'sofia': dict(eyes=[(27.5, 55.5), (55.5, 55.5)], eye_r=(6, 6), cover=(7.5, 8), mouth=(42, 67), mouth_w=10, brow_y=46,
                  cheeks=[(21, 64), (62, 64)], glasses=False),
}
INK = (52, 34, 44)
LIP = (178, 84, 96)
MOUTH_IN = (122, 42, 56)
TONGUE = (226, 128, 140)
BLUSH = (238, 132, 150)
TEAR = (150, 200, 246)
HEART = (236, 92, 128)
EXPR = ['normal', 'tersenyum', 'senang', 'tertawa', 'malu', 'kaget', 'sedih', 'khawatir', 'serius', 'pikir', 'lega', 'jatuh_cinta']


class Face:
    """Two passes: features to remove are collected in a mask and healed together with OpenCV
    inpainting (the skin's own shading continues across them, no flat patches); then the new
    eyes, brows, mouth, blush and effects are drawn on top."""

    def __init__(self, img, c):
        self.im = img.copy()
        self.f = FACE[c]
        self.mask = Image.new('L', img.size, 0)
        self.md = ImageDraw.Draw(self.mask)
        self.ops = []

    # ---- pass 1: what to remove
    def _cover_ell(self, x, y, rx, ry):
        self.md.ellipse((x - rx, y - ry, x + rx, y + ry), fill=255)

    def _cover_rect(self, x0, y0, x1, y1):
        self.md.rectangle((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), fill=255)

    # ---- pass 2 helpers (run after healing)
    def px(self, x, y, col):
        self.d.point((int(round(x)), int(round(y))), fill=col + (255,))

    def ell(self, cx, cy, rx, ry, col):
        self.d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=col + (255,))

    def heal_and_draw(self):
        m = np.asarray(self.mask) > 0
        if m.any():
            import cv2
            a = np.asarray(self.im).copy()
            rgb = np.ascontiguousarray(a[..., :3])
            fixed = cv2.inpaint(rgb, m.astype(np.uint8) * 255, 4, cv2.INPAINT_TELEA)
            a[..., :3] = np.where(m[..., None], fixed, a[..., :3])
            self.im = Image.fromarray(a, 'RGBA')
        self.d = ImageDraw.Draw(self.im)
        for op in self.ops:
            op()
        return self.im

    # ---- features
    def happy_eyes(self):                        # ^ ^ closed and smiling
        rx_, ry_ = self.f['cover']
        for i, (x, y) in enumerate(self.f['eyes']):
            self._cover_ell(x, y, rx_, ry_)
            def op(i=i, x=x, y=y):
                rx = self.f['eye_r'][0]
                pts = [(x + k, y + 1 - (rx - abs(k)) * 0.6) for k in np.linspace(-rx, rx, 9)]
                self.d.line(pts, fill=INK + (255,), width=2, joint='curve')
                if not self.f['glasses']:
                    self.px(x - rx - 1 if i == 0 else x + rx + 1, y - 1, INK)
            self.ops.append(op)

    def soft_eyes(self):                         # relaxed closed: gentle downward arcs
        rx_, ry_ = self.f['cover']
        for x, y in self.f['eyes']:
            self._cover_ell(x, y, rx_, ry_)
            def op(x=x, y=y):
                rx = self.f['eye_r'][0]
                pts = [(x + k, y + (rx - abs(k)) * 0.35) for k in np.linspace(-rx, rx, 9)]
                self.d.line(pts, fill=INK + (255,), width=2, joint='curve')
            self.ops.append(op)

    def half_eyes(self, down=True):              # upper lid lowered over the eye
        rx_, ry_ = self.f['cover']
        for x, y in self.f['eyes']:
            top = y - (0 if down else 1.5)
            self.md.chord((x - rx_, y - ry_, x + rx_, y + ry_), 180, 360, fill=255)
            self._cover_rect(x - rx_, y - 1, x + rx_, top)
            def op(x=x, top=top):
                rx = self.f['eye_r'][0]
                self.d.line((x - rx - 1, top, x + rx + 1, top), fill=INK + (255,), width=2)
            self.ops.append(op)

    def brows(self, kind):                       # 'sad', 'worry' (inner end up), 'serious'
        if self.f['glasses'] and kind == 'serious':
            return
        by = self.f['brow_y']
        for i, (x, y) in enumerate(self.f['eyes']):
            out = -1 if i == 0 else 1
            if not self.f['glasses']:
                self._cover_rect(x - 7, by - 3, x + 7, by + 1)
            a, b = {'sad': (-1.2, 1.4), 'worry': (-2.0, 0.6)}.get(kind, (0.6, 0.6))
            def op(x=x, out=out, a=a, b=b):
                self.d.line(((x + 5 * out, by + b), (x - 4 * out, by + a)), fill=(70, 44, 40, 255), width=2)
            self.ops.append(op)

    def mouth(self, kind):
        x, y = self.f['mouth']
        w = self.f['mouth_w']
        self._cover_ell(x, y, w / 2 + 1, 2.4)
        def op():
            if kind == 'smile':
                for k in range(-w // 2 + 1, w // 2):
                    self.px(x + k, y - 0.5 + (1 - (k / (w / 2)) ** 2) * 1.4, LIP)
            elif kind == 'grin':
                self.d.chord((x - w / 2, y - 2.5, x + w / 2, y + 3.5), 0, 180, fill=MOUTH_IN + (255,))
                self.d.line((x - w / 2 + 1, y + 0.5, x + w / 2 - 1, y + 0.5), fill=(250, 246, 240, 255))
                self.ell(x, y + 2.2, w / 4, 1.0, TONGUE)
            elif kind == 'laugh':
                self.d.chord((x - w / 2 - 1, y - 3, x + w / 2 + 1, y + 5), 0, 180, fill=MOUTH_IN + (255,))
                self.ell(x, y + 3.2, w / 3, 1.4, TONGUE)
            elif kind == 'o':
                self.d.ellipse((x - 1.8, y - 1, x + 1.8, y + 2.6), fill=MOUTH_IN + (255,))
            elif kind == 'frown':
                for k in range(-w // 2 + 2, w // 2 - 1):
                    self.px(x + k, y + 1.2 - (1 - (k / (w / 2)) ** 2) * 1.3, LIP)
            elif kind == 'flat':
                self.d.line((x - w / 2 + 2, y + 0.5, x + w / 2 - 2, y + 0.5), fill=LIP + (255,))
            elif kind == 'wavy':
                for k in range(-w // 2 + 1, w // 2):
                    self.px(x + k, y + 0.5 + (0.6 if k % 2 else -0.4), LIP)
            elif kind == 'side':
                for k in range(0, w // 2):
                    self.px(x + k, y + 0.5 - k * 0.15, LIP)
        self.ops.append(op)

    def blush(self, strong=False):
        def op():
            layer = Image.new('RGBA', self.im.size, (0, 0, 0, 0))
            dl = ImageDraw.Draw(layer)
            for cx, cy in self.f['cheeks']:
                dl.ellipse((cx - 4, cy - 2, cx + 4, cy + 2), fill=BLUSH + (150 if strong else 100,))
            self.im.alpha_composite(layer)
            self.d = ImageDraw.Draw(self.im)
            if strong:
                for cx, cy in self.f['cheeks']:
                    for k in (-2, 0, 2):
                        self.px(cx + k, cy - 1, (222, 96, 120)); self.px(cx + k + 1, cy, (222, 96, 120))
        self.ops.append(op)

    def tear(self, i=0):
        x, y = self.f['eyes'][i]
        rx, ry = self.f['eye_r']
        def op():
            for k in range(4):
                self.px(x - rx + 2, y + ry + k, TEAR)
            self.ell(x - rx + 2, y + ry + 4, 1, 1.4, TEAR)
        self.ops.append(op)

    def sweat(self):
        x, y = self.f['eyes'][1]
        sx, sy = x + 12, y - 12
        def op():
            self.d.polygon([(sx, sy - 3), (sx - 2, sy + 1), (sx + 2, sy + 1)], fill=TEAR + (255,))
            self.ell(sx, sy + 1.5, 2, 2, TEAR)
            self.px(sx - 1, sy, (240, 250, 255))
        self.ops.append(op)

    def heart(self, x, y, s=1.0, col=HEART):
        def op():
            self.ell(x - 1.5 * s, y, 1.8 * s, 1.8 * s, col)
            self.ell(x + 1.5 * s, y, 1.8 * s, 1.8 * s, col)
            self.d.polygon([(x - 3.2 * s, y + 0.6 * s), (x + 3.2 * s, y + 0.6 * s), (x, y + 4 * s)], fill=col + (255,))
        self.ops.append(op)

    def sparkle(self, x, y, col=(255, 214, 120)):
        def op():
            for k in range(-2, 3):
                self.px(x + k, y, col); self.px(x, y + k, col)
        self.ops.append(op)


def paint(base, c, e):
    f = Face(base, c)
    if e == 'tersenyum':
        f.mouth('smile'); f.blush()
    elif e == 'senang':
        f.happy_eyes(); f.mouth('grin'); f.blush()
    elif e == 'tertawa':
        f.happy_eyes(); f.mouth('laugh'); f.blush(); f.sparkle(76, 22); f.sparkle(10, 30)
    elif e == 'malu':
        f.half_eyes(); f.mouth('wavy'); f.blush(strong=True)
    elif e == 'kaget':                           # keep the real eyes; brows up, small 'o', a spark of surprise
        f.brows('worry'); f.mouth('o'); f.sparkle(77, 18, (255, 196, 90)); f.sparkle(70, 12, (255, 196, 90))
    elif e == 'sedih':
        f.half_eyes(); f.brows('sad'); f.mouth('frown'); f.tear(0)
    elif e == 'khawatir':
        f.brows('worry'); f.mouth('wavy'); f.sweat()
    elif e == 'serius':
        f.half_eyes(down=False); f.brows('serious'); f.mouth('flat')
    elif e == 'pikir':
        f.brows('worry'); f.mouth('side'); f.sparkle(76, 24, (190, 190, 230))
    elif e == 'lega':
        f.soft_eyes(); f.mouth('smile'); f.blush()
    elif e == 'jatuh_cinta':
        f.happy_eyes(); f.mouth('smile'); f.blush(strong=True); f.heart(76, 20); f.heart(12, 28, 0.8)
    return f.heal_and_draw()


def finish(img, c):
    """Pixel-art pass at base size, then 2x nearest onto the plate with the old border colour."""
    a = np.asarray(img).astype(np.float32)
    rgb = np.round(a[..., :3] / 6.0) * 6.0
    m = a[..., 3] > 120
    from scipy import ndimage
    ring = ndimage.binary_dilation(m, iterations=1) & ~m
    out = np.zeros((BH, BW, 4), np.uint8)
    out[..., :3] = BG
    out[..., 3] = 255
    out[m, :3] = np.clip(rgb[m], 0, 255)
    out[ring, :3] = (40, 30, 48)
    im = Image.fromarray(out, 'RGBA').resize((BW * 2, BH * 2), Image.NEAREST)
    d = ImageDraw.Draw(im)
    d.rectangle((1, 1, BW * 2 - 2, BH * 2 - 2), outline=BORDER[c] + (255,), width=2)
    for x, y in ((6, 6), (BW * 2 - 7, 6)):
        for k in (-2, -1, 0, 1, 2):
            d.point((x + k, y), fill=BORDER[c] + (255,))
            d.point((x, y + k), fill=BORDER[c] + (255,))
    return im


def main(src, sheet=None):
    src = Path(src)
    shots = []
    for c in ('arland', 'sofia'):
        base = Image.open(src / ('%s_0.png' % c)).convert('RGBA').resize((BW, BH), Image.LANCZOS)
        pdir = ROOT / 'assets/characters' / c / 'portraits'
        old = ROOT / 'assets/characters' / c / 'portraits_v7'
        if not old.exists():                       # keep the hand-drawn V7 set, once
            old.mkdir()
            for f in pdir.glob('*.png'):
                shutil.copy2(f, old / f.name)
        for e in EXPR:
            im = finish(paint(base, c, e), c)
            im.save(pdir / ('%s.png' % e), optimize=True)
            shots.append(im)
        print(c, len(EXPR), 'portraits')
    if sheet:
        s = Image.new('RGBA', (BW * 2 * len(EXPR), BH * 2 * 2), (0, 0, 0, 255))
        for i, im in enumerate(shots):
            s.paste(im, ((i % len(EXPR)) * BW * 2, (i // len(EXPR)) * BH * 2))
        s.save(sheet)


if __name__ == '__main__':
    a = sys.argv[1:]
    sh = a[a.index('--sheet') + 1] if '--sheet' in a else None
    main(a[0], sh)
