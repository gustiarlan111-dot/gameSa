"""Retaining-wall faces and stone stairs for maps with a V8 height layer (assets/data/elevation.json).

Same drawing as the Plaza generator (tools/worldgen/plaza_hd.py `_face`/`_stairs`), but the walls,
keep-clear rects and stairs entries go into a Terrace accumulator instead of module globals, so any
generator can use it. The face is painted in the oblique view: the upper ground ends at y0, the
wall face covers y0..y0+h, the lower ground starts at y0+h.
"""
import json
import numpy as np
from hdmap import K, STONE
from paint import rgb


class Terrace:
    def __init__(self):
        self.walls = []     # collision rects (faces, stair cheeks)
        self.clear = []     # rects around stairs that must stay free of props
        self.stairs = []    # maps.json "stairs" entries for tools/maptool.py

    def face(self, m, c, x0, x1, y0, h, salt, collide=True):
        """Retaining wall seen from the south: coping, cut-stone face darkening downward, contact shadow."""
        face = m.rect(x0, y0, x1 - x0, h)
        c.put(face, c.bricks(('#8d877b', '#999285', '#a49d90', '#afa89b'), 46, 20, '#5f5a51', salt=salt), STONE)
        t = np.clip((c.yy / K - y0) / h, 0, 1)
        c.img[face] *= (1.0 - 0.38 * t[face])[:, None]
        cop = m.rect(x0 - 2, y0 - 7, x1 - x0 + 4, 8)
        c.put(cop, c.bricks(('#cfc8ba', '#d8d2c5', '#e1dbcf'), 64, 16, '#9a9386', salt=salt + 1), STONE)
        c.img[m.rect(x0 - 2, y0 - 7, x1 - x0 + 4, 1.5)] = rgb('#f1ece2')
        c.img[m.rect(x0, y0 + 1, x1 - x0, 2)] *= 0.6
        sh = m.rect(x0, y0 + h, x1 - x0, 12)
        tt = np.clip((c.yy / K - (y0 + h)) / 12, 0, 1)
        c.img[sh] *= (0.55 + 0.45 * tt[sh])[:, None]
        rng = np.random.default_rng(salt)
        for _ in range(int((x1 - x0) / 9)):                                 # ivy / grass hanging over
            x = rng.uniform(x0, x1)
            ln = rng.uniform(3, h * (0.8 if rng.random() < 0.2 else 0.35))
            col = rgb(('#3b7040', '#4f8a47', '#2b5537')[rng.integers(0, 3)])
            c.img[m.rect(x, y0 - 2, 2.5, ln)] = col
            if rng.random() < 0.15:
                c.img[m.ellipse(x + 1, y0 + ln, 2, 1.6)] = rgb('#f3b8c8')
        if collide:
            self.walls.append([int(x0), int(y0 - 3), int(x1 - x0), int(h + 3)])

    def run(self, m, c, x0, x1, y0, h, cuts, salt):
        """A wall face from x0 to x1 broken by southward stairs at cuts [(x, w), ...]."""
        xa = x0
        for i, (sx, sw) in enumerate(sorted(cuts) + [(x1, 0)]):
            if sx > xa:
                self.face(m, c, xa, sx - (8 if sw else 0), y0, h, salt + i)
            if sw:
                self.stairs_south(m, c, sx, y0, sw, h, salt + 20 + i)
            xa = sx + sw + 8

    def stairs_south(self, m, c, x0, y0, w, h, salt):
        """Stone stairs descending southward, cheek walls on both sides (collision)."""
        n = max(3, int(round(h / 7)))
        self.stairs.append(dict(id='st%d' % len(self.stairs), rect=[int(x0), int(y0), int(w), int(h)], dir='down'))
        tex_t = c.bricks(('#ddd6c8', '#e5dfd2', '#ece7dc'), 52, 18, '#a8a092', salt=salt)
        for i in range(n):
            a = y0 + i * h / n
            tread, riser = m.rect(x0, a, w, h / n * 0.58), m.rect(x0, a + h / n * 0.58, w, h / n * 0.42 + 0.5)
            c.put(tread, tex_t, STONE)
            c.put(riser, tex_t, STONE)
            c.img[riser] *= 0.62 + 0.04 * i
        for cx_ in (x0 - 8, x0 + w):
            c.img[m.rect(cx_, y0 - 7, 8, h + 7)] = rgb('#8d877b')
            c.img[m.rect(cx_, y0 - 7, 8, 2)] = rgb('#e1dbcf')
            c.img[m.rect(cx_ + 6, y0 - 5, 2, h + 5)] *= 0.7
            self.walls.append([int(cx_), int(y0 - 2), 8, int(h + 2)])
        self.clear.append((x0 - 8, y0 - 30, w + 16, h + 60))

    def hits(self, p, P, extra=()):
        """True when a prop's foot box overlaps a wall or a stairs keep-clear rect."""
        d = P[p['type']]
        fx0, fy0 = p['x'] - d.get('cw', 0) / 2, p['y'] - max(d.get('ch', 0), 6)
        fw, fh = max(d.get('cw', 0), 6), max(d.get('ch', 0), 6)
        for x, y, w, h in list(self.walls) + [list(r) for r in self.clear] + list(extra):
            if fx0 < x + w and x < fx0 + fw and fy0 < y + h and y < fy0 + fh:
                return True
        return False


def elev_dump(E):
    """elevation.json layout: one primitive per line, areas in file order (same as the hand-kept file)."""
    out = ['{', '  "_doc": %s,' % json.dumps(E['_doc'], ensure_ascii=False), '  "areas": {']
    names = list(E['areas'])
    for i, n in enumerate(names):
        prims = E['areas'][n]
        out.append('    %s: [' % json.dumps(n))
        out += ['      %s%s' % (json.dumps(q, ensure_ascii=False), ',' if j < len(prims) - 1 else '') for j, q in enumerate(prims)]
        out.append('    ]%s' % (',' if i < len(names) - 1 else ''))
    out += ['  }', '}']
    return '\n'.join(out) + '\n'


def write_elevation(A, area, prims):
    """Replace one area's height layer in assets/data/elevation.json."""
    ep = A / 'data/elevation.json'
    E = json.loads(ep.read_text(encoding='utf-8'))
    E['areas'][area] = prims
    ep.write_text(elev_dump(E), encoding='utf-8')
    print('elevation.json:', area, len(prims), 'primitives')
