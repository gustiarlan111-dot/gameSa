"""V8.3: pack the Arland/Sofia GLB renders (tests/charrender/render_sheets.tscn) into the game's sheets.

Each raw frame (384x576, 4x supersampled) is scaled to the character's old on-screen height, aligned
on the same foot line, alpha-hardened (the game draws sprites with alpha cut), lightly posterized and
given the kit's 2-texel coloured outline, then packed at @2x (96x144 per frame):
  assets/characters/<c>/idle_8dir_v53@2x.png   12 x 8
  assets/characters/<c>/walk_8dir_v53@2x.png   24 x 8
  assets/characters/<c>/run_8dir_v53@2x.png    16 x 8 (U3b)
  assets/characters/<c>/poses_v53@2x.png        8 x 21 (dir down/left/right/up x 2 frames; rows 16-20
                                                       are the U3b emotions)
  --couple (tests/charrender/render_couple.tscn, 640x576 raw, both characters at Arland's scale):
  assets/characters/couple/hand_walk@2x.png    12 x 4 (160x144 frames; dirs down/left/right/up)
  assets/characters/couple/hand_idle@2x.png     2 x 4
  assets/characters/couple/hug@2x.png           2 x 4
Actor prefers @2x sheets, so the old 1x art stays in place untouched (delete the @2x files to go back).
Usage: python3 tools/char_sheets.py <charframes dir>
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
FW, FH = 96, 144
HEIGHT = {'arland': 134, 'sofia': 126}          # @2x px, same as the old sprites (67 / 63 at 1x)
FOOT = 141                                      # foot line in the frame, like the old sheets
OUTLINE = {'arland': (34, 26, 38), 'sofia': (36, 30, 44)}


def bbox(a):
    ys, xs = np.nonzero(a > 128)
    return ys.min(), ys.max(), xs.min(), xs.max()


def frame(im, scale, foot_raw, cx_raw, col, fit=False, FW=FW):
    w, h = im.size
    im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    out = np.zeros((FH, FW, 4), np.float32)
    ox = int(round(FW / 2 - cx_raw * scale))
    if fit:                                   # poses that lean (side views) slide back inside the frame
        xs = np.nonzero((a[..., 3] > 110).any(0))[0]
        if len(xs):
            lo, hi = xs[0] + ox, xs[-1] + ox
            if lo < 5:                        # 2 px outline + 3 px air
                ox += 5 - lo
            elif hi > FW - 6:
                ox -= hi - (FW - 6)
    oy = int(round(FOOT - foot_raw * scale))
    ys, xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    ty, tx = ys + oy, xs + ox
    ok = (ty >= 0) & (ty < FH) & (tx >= 0) & (tx < FW)
    out[ty[ok], tx[ok]] = a[ok]
    alpha = out[..., 3] > 110
    rgb = out[..., :3]
    rgb = np.round(rgb / 8.0) * 8.0                              # light posterize, keeps gradients
    m = alpha
    ring = ndimage.binary_dilation(m, iterations=2) & ~m
    res = np.zeros((FH, FW, 4), np.uint8)
    res[m, :3] = np.clip(rgb[m], 0, 255)
    res[m, 3] = 255
    res[ring, :3] = col
    res[ring, 3] = 255
    edge = m & ~ndimage.binary_erosion(m, iterations=1)          # darker rim on the inside edge
    res[edge, :3] = (res[edge, :3] * 0.78).astype(np.uint8)
    return Image.fromarray(res, 'RGBA')


def main(src):
    src = Path(src)
    for c in ('arland', 'sofia'):
        ref = np.asarray(Image.open(src / ('%s_idle_0_00.png' % c)))[..., 3]
        y0, y1, x0, x1 = bbox(ref)
        scale = HEIGHT[c] / (y1 - y0 + 1)
        foot, cx = y1, (x0 + x1) / 2
        col = OUTLINE[c]
        for kind, cols in (('idle', 12), ('walk', 24), ('run', 16)):
            sheet = Image.new('RGBA', (FW * cols, FH * 8), (0, 0, 0, 0))
            for r in range(8):
                for f in range(cols):
                    im = Image.open(src / ('%s_%s_%d_%02d.png' % (c, kind, r, f))).convert('RGBA')
                    sheet.paste(frame(im, scale, foot, cx, col), (f * FW, r * FH))
            out = ROOT / 'assets/characters' / c / ('%s_8dir_v53@2x.png' % kind)
            sheet.save(out, optimize=True)
            print(out.relative_to(ROOT), sheet.size)
        npose = 0
        while (src / ('%s_pose_%02d_0_0.png' % (c, npose))).exists():
            npose += 1
        sheet = Image.new('RGBA', (FW * 8, FH * npose), (0, 0, 0, 0))
        for p in range(npose):
            for d in range(4):
                for f in range(2):
                    im = Image.open(src / ('%s_pose_%02d_%d_%d.png' % (c, p, d, f))).convert('RGBA')
                    sheet.paste(frame(im, scale, foot, cx, col, fit=True), ((d * 2 + f) * FW, p * FH))
        out = ROOT / 'assets/characters' / c / 'poses_v53@2x.png'
        sheet.save(out, optimize=True)
        print(out.relative_to(ROOT), sheet.size)


def couple(src):
    """Pair sheets, both characters in one frame at Arland's scale and foot line (Sofia was scaled in the render)."""
    src = Path(src)
    ref = np.asarray(Image.open(src / 'arland_idle_0_00.png'))[..., 3]
    y0, y1, x0, x1 = bbox(ref)
    scale = HEIGHT['arland'] / (y1 - y0 + 1)
    foot = y1
    cfw = 160
    out_dir = ROOT / 'assets/characters/couple'
    out_dir.mkdir(parents=True, exist_ok=True)
    for kind, cols in (('hand_walk', 12), ('hand_idle', 2), ('hug', 2)):
        sheet = Image.new('RGBA', (cfw * cols, FH * 4), (0, 0, 0, 0))
        for d in range(4):
            for f in range(cols):
                im = Image.open(src / ('couple_%s_%d_%02d.png' % (kind, d, f))).convert('RGBA')
                sheet.paste(frame(im, scale, foot, im.size[0] / 2, OUTLINE['arland'], FW=cfw), (f * cfw, d * FH))
        out = out_dir / ('%s@2x.png' % kind)
        sheet.save(out, optimize=True)
        print(out.relative_to(ROOT), sheet.size)


if __name__ == '__main__':
    if '--couple' in sys.argv:
        couple(sys.argv[sys.argv.index('--couple') + 1])
    else:
        main(sys.argv[1])
