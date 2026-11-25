"""Normal maps for the HD props (2.5D lighting in Godot). For every props/hd/*@2x.png writes
props/hd/n/<name>_n.png: height = bevel from the silhouette (wider, dome-like for foliage) plus a little
luminance relief, normals from its gradient. Run after drawing new props:
    python3 tools/normals.py [names...]
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'assets/props/hd'
OUT = SRC / 'n'
FOLIAGE = ('tree', 'bush', 'shrub', 'flowers', 'fern', 'grass', 'reeds', 'willow', 'hedge', 'lily', 'mushroom')


def blur(a, r):
    return gaussian_filter(a.astype(np.float32), r)


def normal_map(im, foliage):
    a = np.asarray(im, np.float32)
    alpha = a[..., 3] / 255.0
    lum = (a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11) / 255.0
    inside = (alpha > 0.5).astype(np.float32)
    cap = 14.0 if foliage else 5.0
    d = distance_transform_edt(inside)
    h = np.minimum(d, cap) / cap
    h = blur(h, 1.0)
    h = np.sqrt(np.clip(h, 0, 1)) if foliage else h
    h = h * (2.2 if foliage else 1.0) + blur(lum, 1.2) * (1.2 if foliage else 0.6)
    gx = np.zeros_like(h); gy = np.zeros_like(h)
    gx[:, 1:-1] = (h[:, 2:] - h[:, :-2]) * 0.5
    gy[1:-1, :] = (h[2:, :] - h[:-2, :]) * 0.5
    k = 3.0
    n = np.stack([-gx * k, gy * k, np.ones_like(h)], -1)   # Godot: +y up in normal map (green = up)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    rgb = ((n * 0.5 + 0.5) * 255).astype(np.uint8)
    out = np.dstack([rgb, (alpha * 255).astype(np.uint8)])
    return Image.fromarray(out, 'RGBA')


def main():
    OUT.mkdir(exist_ok=True)
    names = sys.argv[1:]
    files = sorted(SRC.glob('*@2x.png'))
    if names:
        files = [f for f in files if any(f.name.startswith(n + '@') for n in names)]
    for f in files:
        im = Image.open(f).convert('RGBA')
        foliage = any(t in f.name for t in FOLIAGE) and 'planter' not in f.name
        normal_map(im, foliage).save(OUT / f.name.replace('@2x.png', '_n.png'), optimize=True)
    print(len(files), 'normal maps ->', OUT)


if __name__ == '__main__':
    main()
