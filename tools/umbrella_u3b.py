"""U3b: umbrella sprites for characters walking in the rain (assets/fx/umbrella_<n>.png).
Pixel-art canopy seen from the HD-2D camera: a dome with scalloped rim, ribs, a tip and the top of
the handle. Bottom-centre of the image sits on the character's head (Actor._place_umbrella).
Usage: python3 tools/umbrella_u3b.py
"""
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / 'assets/fx'
PAL = [('#c94a5a', '#e8788a', '#f6b3be'), ('#3f6fb5', '#6e98d6', '#a9c6ee'),
       ('#e0a83a', '#f2c867', '#fbe3a3'), ('#4f8a5e', '#78b285', '#b2d9b9')]


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32)


def umbrella(pal, W=96, H=72):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, 44.0
    img = np.zeros((H, W, 4), np.float32)
    dark, mid, light = (hexrgb(c) for c in pal)
    # dome: upper half-ellipse, rim scalloped between 8 ribs
    ang = np.arctan2(yy - cy, xx - cx)
    k = 8
    scal = 3.2 * np.abs(np.sin((xx - cx) / (W * 0.46) * np.pi * k / 2))
    dome = (((xx - cx) / 45) ** 2 + ((yy - cy) / 36) ** 2 <= 1) & (yy <= cy + 4 - scal)
    shade = np.clip(0.55 - (xx - cx) / 90 + (cy - yy) / 120, 0, 1)
    col = np.where((shade > 0.62)[..., None], light, np.where((shade > 0.38)[..., None], mid, dark))
    rib = (np.abs(((np.arctan2(yy - cy + 30, xx - cx) + np.pi) * k / np.pi) % 2 - 1) < 0.08) & dome
    img[dome, :3] = col[dome]
    img[rib, :3] = dark * 0.85
    img[dome, 3] = 255
    # tip and handle stub
    img[2:8, int(cx) - 1:int(cx) + 2, :3] = (60, 52, 48); img[2:8, int(cx) - 1:int(cx) + 2, 3] = 255
    img[int(cy) - 2:H - 2, int(cx) - 1:int(cx) + 1, :3] = (70, 58, 52); img[int(cy) - 2:H - 2, int(cx) - 1:int(cx) + 1, 3] = 255
    # dark outline
    a = img[..., 3] > 0
    from scipy import ndimage
    ring = ndimage.binary_dilation(a, iterations=1) & ~a
    img[ring, :3] = dark * 0.55; img[ring, 3] = 255
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')


if __name__ == '__main__':
    for i, p in enumerate(PAL):
        umbrella(p).save(OUT / ('umbrella_%d.png' % i), optimize=True)
        print('umbrella_%d.png' % i)
