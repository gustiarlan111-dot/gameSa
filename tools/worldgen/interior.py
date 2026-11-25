"""HD interior kit: paints whole rooms (shell + furniture) in the classic 3/4 view at 2 texels per
world unit, from code only (no pasted pictures). Rooms are drawn flat because indoors the game looks
straight down on the floor picture; tall furniture blocks walking over its whole drawn rect, so a
character can never stand "behind" something that is painted on the floor.

Room scripts (tools/worldgen/rooms_hd.py) call shell() once and then furniture helpers; every helper
takes world coordinates and returns the rect that should block walking (or None for flat things).
Light comes from the top-left, outlines are darker hue-shifted rims (no pure black), like the
outdoor kit in tools/artkit.
"""
import numpy as np
from paint import rgb, hash2
from ground import noise

K = 2


def mix(a, b, t):
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


def col(c):
    return rgb(c) if isinstance(c, str) else np.asarray(c, np.float32)


def shade(c, k):
    """k < 1 darkens towards a cool purple-brown, k > 1 lightens towards warm cream."""
    c = col(c)
    if k < 1:
        return mix(c, mix(c * 0.45, rgb('#2a1c2e'), 0.35), 1 - k)
    return mix(c, rgb('#fff4e0'), min(1.0, k - 1))


class Room:
    def __init__(self, m, seed=0):
        self.m = m
        self.c = m.c
        self.img = m.c.img
        self.rng = np.random.default_rng(seed)
        self.block = []                    # world rects that stop walking
        self.seed = seed

    # ------------------------------------------------------------------ primitives (world units)
    def R(self, x, y, w, h):
        c = self.c
        return (c.xx >= x * K) & (c.xx < (x + w) * K) & (c.yy >= y * K) & (c.yy < (y + h) * K)

    def E(self, cx, cy, rx, ry):
        c = self.c
        return ((c.xx - cx * K) / (rx * K)) ** 2 + ((c.yy - cy * K) / (ry * K)) ** 2 < 1

    def fill(self, mask, c, a=1.0):
        c = col(c)
        if a >= 1:
            self.img[mask] = c
        else:
            self.img[mask] = self.img[mask] * (1 - a) + c * a

    def rect(self, x, y, w, h, c, a=1.0):
        self.fill(self.R(x, y, w, h), c, a)

    def vgrad(self, x, y, w, h, top, bot):
        m = self.R(x, y, w, h)
        t = np.clip((self.c.yy[m] / K - y) / max(1, h), 0, 1)[:, None]
        self.img[m] = mix(col(top), col(bot), t)

    def outline(self, mask, c, inner=None):
        """1-texel rim around a mask (outside), optional inner highlight on the top edge."""
        up = np.roll(mask, 1, 0); dn = np.roll(mask, -1, 0); lf = np.roll(mask, 1, 1); rt = np.roll(mask, -1, 1)
        rim = (up | dn | lf | rt) & ~mask
        self.img[rim] = col(c)
        if inner is not None:
            top = mask & ~np.roll(mask, 1, 0)
            self.img[top] = col(inner)

    def darken(self, mask, k):
        self.img[mask] *= k

    def drop(self, x, y, w, h, k=0.7, dx=4, dy=3):
        """Soft contact shadow below-right of a footprint (light from the top-left)."""
        m = self.R(x + dx, y + h - 2, w, dy + 3) | self.R(x + w, y + 6, dx, h - 4)
        self.img[m] *= k

    def box(self, x, y, w, d, h, top, front, rim=None, light=True):
        """3/4-view block: top face (w x d) above the front face (w x h). Returns its full rect."""
        self.drop(x, y, w, d + h)
        self.rect(x, y, w, d, top)
        self.vgrad(x, y + d, w, h, shade(front, 1.02), shade(front, 0.86))
        m = self.R(x, y, w, d + h)
        self.outline(m, rim if rim is not None else shade(front, 0.45))
        if light:
            self.rect(x, y, w, 1, shade(top, 1.25))
            self.rect(x, y + d, w, 1, shade(front, 0.62))
        return [x, y, w, d + h]

    def dots(self, mask, cols, n, size=1):
        ys, xs = np.nonzero(mask[::K, ::K])
        if len(ys) == 0:
            return
        for i in self.rng.integers(0, len(ys), n):
            y, x = ys[i] * K, xs[i] * K
            self.img[y:y + size * K, x:x + size * K] = col(cols[self.rng.integers(0, len(cols))])

    def planks(self, pal, ph=11):
        c = self.c
        p = np.stack([col(x) for x in pal])
        X, Y = c.xx // K, c.yy // K
        row = Y // ph
        seg_len = 70 + (hash2(row, 0, self.seed) * 70).astype(int)
        off = (hash2(row, 1, self.seed) * 90).astype(int)
        seg = (X + off) // seg_len
        k = np.clip((hash2(row, seg, self.seed + 2) * (len(p) - 1)).round().astype(int), 0, len(p) - 1)
        img = p[k].copy()
        grain = noise(c.h, c.w, 7, self.seed + 3)
        streak = noise(c.h, c.w, 3, self.seed + 4)
        img *= (0.95 + 0.07 * grain + 0.03 * (streak > 0.6))[..., None]
        ly = c.yy % (ph * K); lx = (X + off) % seg_len
        seam = (ly == 0)
        img[seam] = img[seam] * 0.7
        img[ly == 1] = np.clip(img[ly == 1] * 1.06, 0, 255)
        end = (lx == 0) & (c.xx % K == 0)
        img[end] = img[end] * 0.75
        return img

    # ------------------------------------------------------------------ room shell
    def shell(self, W, H, floor='planks', wall='#f1d9cf', wainscot='#d99a9a', trim='#fbeee4',
              floor_pal=None, door=(274, 52), wall_h=96, side=24, pattern='stripe', bottom=424):
        """Back wall band (top), side walls, floor, bottom wall with a door gap. Returns the walls."""
        c = self.c
        self.img[:] = rgb('#140f1a')
        fx, fy, fw, fh = side, wall_h, W - 2 * side, bottom - wall_h
        # floor
        if floor == 'planks':
            pal = floor_pal or ('#b07f57', '#b98a60', '#c29468', '#ca9e72')
            fl = self.planks(pal, ph=11)
        elif floor == 'tiles':
            a, b = floor_pal or ('#e9e2d6', '#d8cfc0')
            fl = c.tiles(a, b, size=32, grout='#b9ad9b', salt=4)
        elif floor == 'checker':
            a, b = floor_pal or ('#2f2a44', '#3c3658')
            fl = c.tiles(a, b, size=40, grout='#1e1a2c', salt=5)
        else:
            a, b = floor_pal or ('#7a7f8c', '#6c717e')
            fl = c.tiles(a, b, size=48, grout='#4f5360', salt=6)
        fm = self.R(fx, fy, fw, fh)
        self.img[fm] = fl[fm]
        c.mat[fm] = 5 if floor == 'planks' else 3
        # light pool from the windows and soft corner occlusion
        yy, xx = c.yy / K, c.xx / K
        dist = np.minimum.reduce([xx - fx, yy - fy, fx + fw - xx, fy + fh - yy])
        ao = np.clip(dist / 22.0, 0, 1) * 0.22 + 0.78
        self.img[fm] *= ao[fm][:, None]
        # back wall
        wy = 10
        self.rect(0, 0, W, wy, '#2a2030')
        self.vgrad(side, wy, W - 2 * side, wall_h - wy, shade(wall, 1.06), shade(wall, 0.94))
        wm = self.R(side, wy, W - 2 * side, wall_h - wy - 30)
        if pattern == 'stripe':
            sm = wm & (((c.xx // K) // 10) % 2 == 0)
            self.img[sm] *= 0.95
        elif pattern == 'dots':
            sm = wm & ((c.xx // K) % 16 == 4) & ((c.yy // K) % 16 == 6)
            self.img[sm] = shade(wall, 0.82)
        elif pattern == 'brick':
            bm = self.c.bricks(('#9e6649', '#a96f4f', '#b37a57', '#8f5b41'), bw=28, bh=12, mortar='#6e4a3a', salt=7)
            self.img[wm] = bm[wm]
        elif pattern == 'stars':
            sm = wm & (hash2(c.xx // 6, c.yy // 6, 3) > 0.985)
            self.img[sm] = rgb('#f6e7a8')
        # wainscot + chair rail + skirting
        self.vgrad(side, wall_h - 30, W - 2 * side, 26, shade(wainscot, 1.04), shade(wainscot, 0.9))
        pm = self.R(side, wall_h - 28, W - 2 * side, 22) & (((c.xx // K) - side) % 36 < 2)
        self.img[pm] = shade(wainscot, 0.75)
        self.rect(side, wall_h - 31, W - 2 * side, 3, trim)
        self.rect(side, wall_h - 31, W - 2 * side, 1, shade(trim, 1.2))
        self.rect(side, wall_h - 4, W - 2 * side, 4, shade(wainscot, 0.6))
        self.rect(side, wy, W - 2 * side, 3, shade(trim, 0.85))
        # floor shadow under the back wall
        self.darken(self.R(fx, fy, fw, 8), 0.72)
        self.darken(self.R(fx, fy + 8, fw, 6), 0.86)
        # side walls (seen from above: thick tops) and the bottom wall
        for x in (0, W - side):
            self.rect(x, 0, side, bottom, '#3a2c3c')
            self.rect(x + (side - 6 if x == 0 else 0), wy, 6, bottom - wy, '#5a4658')
        self.rect(0, bottom, W, H - bottom, '#3a2c3c')
        self.rect(0, bottom, W, 4, '#5a4658')
        dx, dw = door
        self.rect(dx, bottom - 2, dw, H - bottom + 2, fl[int((bottom - 10) * K), int((dx + 10) * K)])
        dm = self.R(dx, bottom - 2, dw, H - bottom + 2)
        self.img[dm] = fl[dm] * 0.8
        self.rect(dx - 3, bottom, 3, H - bottom, '#6b5464'); self.rect(dx + dw, bottom, 3, H - bottom, '#6b5464')
        c.mat[dm] = c.mat[fm].max() if fm.any() else 5
        walls = [[0, 0, W, wall_h], [0, wall_h, side, bottom - wall_h], [W - side, wall_h, side, bottom - wall_h],
                 [0, bottom, dx, H - bottom], [dx + dw, bottom, W - dx - dw, H - bottom]]
        self.block += walls
        return walls

    # ------------------------------------------------------------------ wall decor (on the back wall)
    def window(self, x, y, w, h, curtain='#f4c6cf', sky=('#9fd3f0', '#e8f4fb'), lit=False, sill_plant=False):
        self.rect(x - 4, y - 4, w + 8, h + 8, '#fbf3ea')
        self.outline(self.R(x - 4, y - 4, w + 8, h + 8), '#9b8478')
        if lit:
            self.vgrad(x, y, w, h, '#1b2550', '#3a3f78')
            self.dots(self.R(x, y, w, h * 0.6), ['#fff6c8', '#dfe8ff'], max(3, w * h // 220))
        else:
            self.vgrad(x, y, w, h, sky[0], sky[1])
            self.rect(x + 4, y + h * 0.55, w * 0.5, h * 0.25, '#bfe2c0', 0.6)
        self.rect(x + w / 2 - 1, y, 2, h, '#fbf3ea'); self.rect(x, y + h / 2 - 1, w, 2, '#fbf3ea')
        self.rect(x + 2, y + 2, 3, h * 0.35, '#ffffff', 0.5)
        self.rect(x - 8, y + h + 2, w + 16, 5, '#efe1d2'); self.rect(x - 8, y + h + 6, w + 16, 2, '#b89c88')
        # curtains with folds
        cw = max(10, w * 0.28)
        for cx in (x - 8, x + w + 8 - cw):
            m = self.R(cx, y - 8, cw, h + 10)
            self.fill(m, curtain)
            folds = m & (((self.c.xx // K) - int(cx)) % 6 < 2)
            self.img[folds] = shade(curtain, 0.86)
            self.outline(m, shade(curtain, 0.55))
            self.rect(cx + 2, y + h * 0.55, cw - 4, 3, shade(curtain, 0.7))
        self.rect(x - 12, y - 10, w + 24, 3, '#a57a52')
        if sill_plant:
            self.pot(x + w - 12, y + h + 4, 0.55)
        if not lit:   # sunlight falling onto the floor below, slanting to the right
            fy = 98
            yy, xx = self.c.yy / K, self.c.xx / K
            t = (yy - fy) / 90.0
            lm = (t >= 0) & (t <= 1) & (xx > x - 4 + t * 30) & (xx < x + w + 4 + t * 46)
            k = (np.sin(np.clip(t[lm], 0, 1) * np.pi) * 0.16)[:, None]
            self.img[lm] = self.img[lm] * (1 - k) + rgb('#fff3d0') * k

    def frame(self, x, y, w, h, art=0, wood='#b08a5a'):
        self.rect(x, y, w, h, wood)
        self.outline(self.R(x, y, w, h), shade(wood, 0.5))
        ix, iy, iw, ih = x + 2, y + 2, w - 4, h - 4
        pals = [('#bfe3f4', '#7fbf7a', '#f5a3b5'), ('#f6d6a8', '#e58a6a', '#6f8fc4'), ('#cfc6f2', '#8f7ad0', '#f4e3a0'),
                ('#ffe3ec', '#e48aa8', '#8cc77c'), ('#203058', '#f2e6a0', '#6a7ac8')]
        a, b, cc = pals[art % len(pals)]
        self.vgrad(ix, iy, iw, ih, a, shade(a, 0.9))
        self.rect(ix, iy + ih * 0.62, iw, ih * 0.38, b)
        self.fill(self.E(ix + iw * 0.35, iy + ih * 0.45, iw * 0.16, ih * 0.16), cc)
        self.rect(ix, iy, 1, ih, '#ffffff', 0.35)

    def poster(self, x, y, w, h, base='#f4e7d0', accent='#e07a8f', art=0):
        self.rect(x, y, w, h, base)
        self.outline(self.R(x, y, w, h), shade(base, 0.55))
        self.fill(self.E(x + w / 2, y + h * 0.42, w * 0.3, w * 0.3), accent)
        for i in range(3):
            self.rect(x + 4, y + h - 12 + i * 3, w - 8 - i * 6, 1, shade(base, 0.6))
        self.rect(x + w / 2 - 1, y - 2, 2, 2, '#d04a4a')

    def clock(self, cx, cy, r=9, rim='#8c5a3a'):
        self.fill(self.E(cx, cy, r, r), rim)
        self.fill(self.E(cx, cy, r - 2, r - 2), '#fbf4e6')
        self.rect(cx - 0.5, cy - r + 4, 1, r - 4, '#3a2c2c'); self.rect(cx, cy - 0.5, r - 4, 1, '#3a2c2c')

    def wall_shelf(self, x, y, w, items=('book', 'plant', 'jar')):
        self.rect(x, y, w, 3, '#b48a5e'); self.rect(x, y + 3, w, 2, '#6e4a30')
        px = x + 3
        for i, it in enumerate(items):
            if it == 'book':
                for j in range(4):
                    h = 9 + (j * 3) % 5
                    self.rect(px, y - h, 3, h, ['#c45a5a', '#5a7ac4', '#e0b04a', '#6aa86a'][j])
                    px += 3.5
            elif it == 'plant':
                self.pot(px + 6, y, 0.45); px += 14
            elif it == 'jar':
                self.rect(px, y - 8, 7, 8, '#cfe6ee', 0.85); self.rect(px, y - 9, 7, 2, '#b07a4a'); px += 10
            elif it == 'plush':
                self.plush(px + 6, y, 0.5); px += 14
            px += 4

    def string_lights(self, x0, x1, y, sag=8, n=12, colors=('#ffd98a', '#ffb3c6', '#bfe3ff')):
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            yy = y + sag * 4 * t * (1 - t)
            self.rect(x, yy, 1.5, 1, '#5a4a40')
            if i % 1 == 0 and 0 < i < n:
                self.fill(self.E(x, yy + 2.5, 2.2, 2.2), colors[i % len(colors)])
                g = self.E(x, yy + 2.5, 6, 5)
                self.img[g] = self.img[g] * 0.9 + col(colors[i % len(colors)]) * 0.1

    def hanging_plant(self, x, y, drop=30):
        self.rect(x, y, 1, drop - 8, '#8a6a4a')
        self.box(x - 6, y + drop - 10, 12, 3, 7, '#c8774a', '#b0603a', light=False)
        self.leaves(x, y + drop - 10, 13, 8, n=30, trail=16)

    # ------------------------------------------------------------------ greenery
    def leaves(self, cx, cy, rx, ry, n=40, trail=0, pal=('#2f6a3a', '#3f8045', '#55994f', '#74b45f', '#9bcd78')):
        m = self.E(cx, cy, rx, ry)
        self.fill(m, pal[1])
        ys, xs = np.nonzero(m[::K, ::K])
        for i in self.rng.integers(0, max(1, len(ys)), n):
            if not len(ys):
                break
            y, x = ys[i], xs[i]
            k = 2 + (y < cy - ry * 0.3) * 1 + (x < cx) * 1
            self.fill(self.E(x, y, 2.6, 2.0), pal[min(4, k)])
        self.outline(m, '#1e3f2a')
        for t in range(int(trail)):
            for s in (-1, 1):
                xx = cx + s * (rx * 0.6) + np.sin(t * 0.7) * 1.5
                self.rect(xx, cy + t, 2, 2, pal[2 + (t % 2)])

    def pot(self, cx, bot, s=1.0, pot='#c8774a', kind='leafy'):
        w, h = 16 * s, 12 * s
        self.drop(cx - w / 2, bot - h, w, h, 0.75)
        m = self.R(cx - w / 2, bot - h, w, h) & ~(self.R(cx - w / 2, bot - h * 0.4, 1.5 * s, h) | self.R(cx + w / 2 - 1.5 * s, bot - h * 0.4, 1.5 * s, h))
        self.fill(m, pot)
        self.rect(cx - w / 2, bot - h, w, 3 * s, shade(pot, 1.15))
        self.outline(m, shade(pot, 0.45))
        if kind == 'leafy':
            self.leaves(cx, bot - h - 9 * s, 13 * s, 11 * s, n=int(50 * s))
        elif kind == 'tall':
            for i in range(7):
                a = -1.2 + i * 0.4
                for t in range(int(26 * s)):
                    self.rect(cx + np.sin(a) * t * 0.5, bot - h - t, 2.5, 2, ['#3f8045', '#55994f', '#74b45f'][i % 3])
        elif kind == 'flower':
            self.leaves(cx, bot - h - 6 * s, 11 * s, 8 * s, n=int(30 * s))
            self.dots(self.E(cx, bot - h - 8 * s, 10 * s, 7 * s), ['#f2a0b8', '#ffffff', '#f6d36a'], int(14 * s), 2)

    # ------------------------------------------------------------------ soft things
    def rug(self, cx, cy, rx, ry, a='#e7a2a8', b='#f6d2cf', round_=True, fringe=True):
        if round_:
            outer = self.E(cx, cy, rx, ry)
            self.fill(outer, a)
            r = np.sqrt(((self.c.xx / K - cx) / rx) ** 2 + ((self.c.yy / K - cy) / ry) ** 2)
            self.img[outer & (r < 0.86)] = col(b)
            self.img[outer & (r < 0.6)] = mix(col(a), col(b), 0.55)
            self.img[outer & (r < 0.3)] = col(b)
            braid = outer & ((r * 26).astype(int) % 2 == 0) & (((self.c.xx // K) + (self.c.yy // K)) % 3 == 0)
            self.img[braid] = self.img[braid] * 0.93
            self.img[outer & (r > 0.92)] = shade(a, 0.85)
            self.outline(outer, shade(a, 0.55))
        else:
            x, y, w, h = cx - rx, cy - ry, 2 * rx, 2 * ry
            m = self.R(x, y, w, h)
            self.fill(m, a)
            inner = self.R(x + 5, y + 5, w - 10, h - 10)
            self.fill(inner, b)
            diam = inner & ((np.abs(((self.c.xx // K) - int(cx)) % 18 - 9) + np.abs(((self.c.yy // K) - int(cy)) % 18 - 9)) < 4)
            self.img[diam] = col(a)
            self.outline(m, shade(a, 0.55))
            if fringe:
                fm = (self.R(x - 3, y, 3, h) | self.R(x + w, y, 3, h)) & ((self.c.yy // K) % 3 == 0)
                self.img[fm] = shade(b, 0.95)

    def cushion(self, cx, cy, s=1.0, c='#f4b6c2'):
        m = self.E(cx, cy, 9 * s, 6 * s)
        self.drop(cx - 9 * s, cy - 6 * s, 18 * s, 12 * s, 0.8, 2, 2)
        self.fill(m, c)
        self.fill(self.E(cx - 2 * s, cy - 2 * s, 5 * s, 2.5 * s), shade(c, 1.2))
        self.outline(m, shade(c, 0.5))
        self.rect(cx - 0.5, cy - 1, 1, 2, shade(c, 0.6))

    def plush(self, cx, bot, s=1.0, c='#d9a477'):
        self.drop(cx - 7 * s, bot - 14 * s, 14 * s, 14 * s, 0.8, 2, 2)
        body = self.E(cx, bot - 5 * s, 6 * s, 5 * s)
        head = self.E(cx, bot - 12 * s, 5.5 * s, 4.8 * s)
        ears = self.E(cx - 4 * s, bot - 16 * s, 2 * s, 2 * s) | self.E(cx + 4 * s, bot - 16 * s, 2 * s, 2 * s)
        m = body | head | ears
        self.fill(m, c)
        self.fill(self.E(cx, bot - 10.5 * s, 2.5 * s, 1.6 * s), shade(c, 1.3))
        self.rect(cx - 2.5 * s, bot - 13 * s, 1, 1, '#2a1c1c'); self.rect(cx + 2 * s, bot - 13 * s, 1, 1, '#2a1c1c')
        self.outline(m, shade(c, 0.45))

    def slippers(self, x, y, c='#f6c2cf'):
        for dx in (0, 7):
            m = self.E(x + dx, y, 3, 5)
            self.fill(m, c); self.fill(self.E(x + dx, y - 1.5, 2.2, 2), '#ffffff')
            self.outline(m, shade(c, 0.5))

    def basket(self, x, y, w=22, h=18, c='#c9a46a', laundry=True):
        r = self.box(x, y, w, 5, h - 5, shade(c, 0.6), c)
        wv = self.R(x, y + 5, w, h - 5) & (((self.c.xx // K) + (self.c.yy // K)) % 4 == 0)
        self.img[wv] = shade(c, 0.8)
        if laundry:
            self.fill(self.E(x + w / 2, y + 3, w * 0.4, 4), '#9fc3e6')
            self.fill(self.E(x + w * 0.35, y + 2, w * 0.2, 3), '#f4b6c2')
        return r

    # ------------------------------------------------------------------ furniture
    def bed(self, x, y, w=72, h=118, blanket='#f0a7b4', sheet='#fbefe9', frame='#c48a5a', pattern='quilt'):
        self.drop(x, y, w, h, 0.65, 6, 5)
        # headboard
        hb = self.R(x, y, w, 22)
        self.vgrad(x, y, w, 22, shade(frame, 1.1), shade(frame, 0.9))
        self.rect(x, y, w, 2, shade(frame, 1.3))
        for px in range(int(x + 8), int(x + w - 4), 12):
            self.rect(px, y + 6, 3, 13, shade(frame, 0.8))
        self.outline(hb, shade(frame, 0.45))
        # mattress + pillows
        self.rect(x + 3, y + 18, w - 6, h - 26, sheet)
        for i, px in enumerate((x + 7, x + w / 2 + 2)):
            pm = self.R(px, y + 22, w / 2 - 9, 16)
            self.fill(pm, '#ffffff' if i else '#fff6f0')
            self.rect(px + 2, y + 24, w / 2 - 13, 3, '#ffffff')
            self.outline(pm, '#cdb8b2')
        # blanket
        by = y + 44
        bm = self.R(x + 1, by, w - 2, h - 52)
        self.fill(bm, blanket)
        if pattern == 'quilt':
            q = bm & (((((self.c.xx // K) - int(x)) // 12) + (((self.c.yy // K) - by) // 12)) % 2 == 0)
            self.img[q] = shade(blanket, 1.12)
            st = bm & ((((self.c.xx // K) - int(x)) % 12 == 0) | (((self.c.yy // K) - by) % 12 == 0))
            self.img[st] = shade(blanket, 0.85)
        elif pattern == 'stripes':
            st = bm & ((((self.c.yy // K) - by) // 7) % 2 == 0)
            self.img[st] = shade(blanket, 0.82)
        self.rect(x + 1, by, w - 2, 6, sheet); self.rect(x + 1, by + 6, w - 2, 1, shade(blanket, 0.7))
        self.rect(x + 1, by + h - 54, w - 2, 2, shade(blanket, 0.65))
        # foot board front face
        self.vgrad(x, y + h - 8, w, 8, shade(frame, 1.0), shade(frame, 0.8))
        self.outline(self.R(x, y, w, h), shade(frame, 0.42))
        return [x, y, w, h]

    def nightstand(self, x, y, w=26, lamp=True, c='#c9935f'):
        r = self.box(x, y + 14, w, 10, 18, shade(c, 1.1), c)
        self.rect(x + 4, y + 29, w - 8, 1, shade(c, 0.6)); self.rect(x + w / 2 - 2, y + 31, 4, 2, '#e6c27a')
        if lamp:
            self.rect(x + w / 2 - 1, y + 6, 2, 12, '#7a6a5a')
            m = self.R(x + w / 2 - 7, y - 2, 14, 10) & ~self.R(x + w / 2 - 7, y - 2, 2, 3) & ~self.R(x + w / 2 + 5, y - 2, 2, 3)
            self.fill(m, '#fbe2b0'); self.outline(m, '#b08a5a')
            g = self.E(x + w / 2, y + 6, 18, 14)
            self.img[g] = self.img[g] * 0.92 + rgb('#ffe6a8') * 0.08
        return [r[0], y + 4, r[2], r[3] + 10]

    def wardrobe(self, x, y, w=60, h=96, c='#efe3d3', trim='#c9a77a', open_=False):
        r = self.box(x, y, w, 8, h - 8, shade(c, 1.08), c)
        fy = y + 8
        self.rect(x + w / 2 - 0.5, fy + 2, 1, h - 14, shade(c, 0.6))
        for dx in (4, w / 2 + 3):
            pm = self.R(x + dx, fy + 6, w / 2 - 7, h * 0.45)
            self.outline(pm, shade(c, 0.75))
            pm2 = self.R(x + dx, fy + 10 + h * 0.45, w / 2 - 7, h * 0.3)
            self.outline(pm2, shade(c, 0.75))
        self.rect(x + w / 2 - 4, fy + h * 0.4, 2, 6, trim); self.rect(x + w / 2 + 2, fy + h * 0.4, 2, 6, trim)
        self.rect(x, fy + h - 18, w, 2, shade(c, 0.7))
        self.rect(x + 3, y + 1, w - 6, 2, trim)
        return r

    def desk(self, x, y, w=80, h=44, c='#c9935f', items=('laptop', 'lamp', 'mug'), chair='#e7a3b0'):
        r = self.box(x, y, w, 20, h - 20, shade(c, 1.1), c)
        self.rect(x + w - 26, y + 24, 20, h - 28, shade(c, 0.85)); self.rect(x + w - 17, y + 27, 3, 1.5, '#e6c27a')
        px = x + 6
        for it in items:
            if it == 'laptop':
                self.rect(px, y + 4, 26, 12, '#3b3f4f'); self.rect(px + 2, y + 6, 22, 8, '#9fd6f0')
                self.rect(px - 2, y + 15, 30, 4, '#c7ccd6'); self.outline(self.R(px - 2, y + 4, 30, 15), '#2a2c38')
                g = self.E(px + 13, y + 10, 18, 10); self.img[g] = self.img[g] * 0.9 + rgb('#bfe8ff') * 0.1
                px += 34
            elif it == 'monitor':
                self.rect(px, y - 10, 34, 22, '#2a2d3a'); self.rect(px + 2, y - 8, 30, 17, '#5ac8e8')
                self.rect(px + 4, y - 6, 12, 2, '#e8f8ff'); self.rect(px + 4, y - 2, 20, 2, '#bfe8ff')
                self.rect(px + 15, y + 12, 4, 4, '#2a2d3a'); self.rect(px + 6, y + 15, 24, 3, '#c7ccd6')
                g = self.E(px + 17, y + 2, 30, 18); self.img[g] = self.img[g] * 0.88 + rgb('#bfe8ff') * 0.12
                px += 40
            elif it == 'lamp':
                self.rect(px + 4, y + 2, 2, 14, '#6b6b78'); self.rect(px, y + 15, 10, 2, '#6b6b78')
                self.fill(self.E(px + 7, y + 2, 6, 3.5), '#f2c86a')
                g = self.E(px + 6, y + 12, 16, 10); self.img[g] = self.img[g] * 0.9 + rgb('#ffe6a8') * 0.1
                px += 14
            elif it == 'mug':
                self.rect(px, y + 8, 6, 7, '#f4f0ea'); self.rect(px + 6, y + 10, 2, 3, '#f4f0ea'); self.rect(px + 1, y + 8, 4, 2, '#7a4a2a')
                px += 11
            elif it == 'papers':
                for i in range(3):
                    self.rect(px + i * 3, y + 3 + i * 2, 14, 10, '#fbf8f0'); self.outline(self.R(px + i * 3, y + 3 + i * 2, 14, 10), '#c9bfae')
                px += 22
            elif it == 'books':
                for i, cc in enumerate(('#c45a5a', '#5a7ac4', '#e0b04a')):
                    self.rect(px, y + 12 - i * 3, 16, 3, cc)
                px += 20
            elif it == 'plant':
                self.pot(px + 6, y + 16, 0.45); px += 14
            elif it == 'phone':
                self.rect(px, y + 8, 6, 9, '#2a2c38'); self.rect(px + 1, y + 9, 4, 7, '#8fd0f0'); px += 10
        if chair:
            cy = y + h + 2
            self.drop(x + w / 2 - 10, cy - 4, 20, 18, 0.75, 3, 3)
            self.fill(self.E(x + w / 2, cy + 4, 11, 7), chair)
            self.fill(self.E(x + w / 2, cy + 3, 8, 4.5), shade(chair, 1.15))
            self.outline(self.E(x + w / 2, cy + 4, 11, 7), shade(chair, 0.5))
            self.rect(x + w / 2 - 1, cy + 11, 2, 4, '#6b6b78')
        return [x, y, w, h + (14 if chair else 0)]

    def bookshelf(self, x, y, w=96, h=72, c='#b47a4a', rows=3, deco=True):
        r = self.box(x, y, w, 8, h - 8, shade(c, 1.1), c)
        iy = y + 10
        rh = (h - 14) / rows
        for i in range(rows):
            ry = iy + i * rh
            self.rect(x + 3, ry, w - 6, rh - 3, shade(c, 0.5))
            px = x + 4
            while px < x + w - 8:
                kind = self.rng.random()
                if deco and kind < 0.04:
                    self.plush(px + 6, ry + rh - 3, 0.5, ['#d9a477', '#f2c4cf', '#c9c9d9'][int(px) % 3]); px += 13
                    continue
                if deco and kind < 0.07:
                    self.pot(px + 5, ry + rh - 3, 0.38); px += 11
                    continue
                bw = 3 + self.rng.integers(0, 3)
                bh = rh - 5 - self.rng.integers(0, 5)
                cc = ['#c45a5a', '#5a7ac4', '#e0b04a', '#6aa86a', '#9a6ac4', '#e0866a', '#4aa8a8', '#f0d0a0'][self.rng.integers(0, 8)]
                self.rect(px, ry + rh - 3 - bh, bw, bh, cc)
                self.rect(px, ry + rh - 3 - bh, 1, bh, shade(cc, 1.2))
                self.rect(px, ry + rh - 3 - bh + 2, bw, 1, shade(cc, 0.7))
                px += bw + 0.5
            self.rect(x + 2, ry + rh - 3, w - 4, 3, shade(c, 1.05))
        return r

    def vanity(self, x, y, w=72, h=50, c='#f3e7dc', mirror=True):
        if mirror:
            self.fill(self.E(x + w / 2, y + 6, 15, 17), '#d9b46a')
            self.fill(self.E(x + w / 2, y + 6, 12, 14), '#cfe6f2')
            self.rect(x + w / 2 - 8, y - 4, 3, 12, '#ffffff', 0.6)
        r = self.box(x, y + 18, w, 14, h - 18 - 14 + 14, shade(c, 1.05), c)
        for dx in (4, w - 22):
            self.outline(self.R(x + dx, y + 36, 18, 10), shade(c, 0.7)); self.rect(x + dx + 8, y + 40, 3, 1.5, '#d9b46a')
        self.rect(x + 22, y + 21, 5, 8, '#f2a0b8'); self.rect(x + 29, y + 23, 4, 6, '#bfe3f4'); self.rect(x + 46, y + 22, 9, 6, '#e8b4c8')
        self.fill(self.E(x + 58, y + 25, 4, 3), '#f6d36a')
        # stool
        sy = y + h + 10
        self.drop(x + w / 2 - 9, sy - 6, 18, 16, 0.75, 2, 2)
        self.fill(self.E(x + w / 2, sy, 10, 6), '#f4b6c2'); self.outline(self.E(x + w / 2, sy, 10, 6), '#b0707e')
        self.rect(x + w / 2 - 7, sy + 5, 2, 7, '#e8d8c8'); self.rect(x + w / 2 + 5, sy + 5, 2, 7, '#e8d8c8')
        return [x, y + 10, w, h + 4]

    def sofa(self, x, y, w=84, h=40, c='#e8a0a8', pillows=('#fbe3c0', '#bfe3f4')):
        self.drop(x, y, w, h, 0.68, 5, 4)
        back = self.R(x + 6, y, w - 12, 16)
        self.vgrad(x + 6, y, w - 12, 16, shade(c, 1.1), shade(c, 0.95))
        self.outline(back, shade(c, 0.5))
        seat = self.R(x + 6, y + 14, w - 12, h - 20)
        self.fill(seat, shade(c, 1.05))
        self.rect(x + w / 2, y + 14, 1, h - 22, shade(c, 0.7))
        for ax in (x, x + w - 10):
            am = self.R(ax, y + 6, 10, h - 8)
            self.vgrad(ax, y + 6, 10, h - 8, shade(c, 1.05), shade(c, 0.85)); self.outline(am, shade(c, 0.5))
        self.vgrad(x + 6, y + h - 8, w - 12, 8, shade(c, 0.9), shade(c, 0.75))
        for i, pc in enumerate(pillows):
            self.cushion(x + 20 + i * (w - 40), y + 14, 0.8, pc)
        self.outline(self.R(x, y, w, h), shade(c, 0.42))
        return [x, y, w, h]

    def beanbag(self, cx, cy, c='#f0a3b0'):
        m = self.E(cx, cy, 20, 15)
        self.drop(cx - 20, cy - 15, 40, 30, 0.7, 4, 4)
        self.fill(m, c)
        self.fill(self.E(cx - 4, cy - 4, 12, 7), shade(c, 1.15))
        self.fill(self.E(cx + 2, cy + 3, 10, 6), shade(c, 0.9))
        self.outline(m, shade(c, 0.5))
        return [cx - 20, cy - 15, 40, 30]

    def table(self, x, y, w=60, h=40, c='#c9935f', cloth=None, round_=False, chairs=2, chair_c='#b07a4a', items=()):
        if round_:
            self.drop(x, y, w, h, 0.7, 4, 4)
            top = self.E(x + w / 2, y + h * 0.4, w / 2, h * 0.35)
            self.fill(top, cloth or c)
            self.outline(top, shade(cloth or c, 0.5))
            self.rect(x + w / 2 - 2, y + h * 0.7, 4, h * 0.3, shade(c, 0.6))
        else:
            self.box(x, y, w, h * 0.55, h * 0.45, shade(c, 1.1), c)
            if cloth:
                self.rect(x + 4, y + 2, w - 8, h * 0.55 - 4, cloth)
        px = x + w / 2 - 10
        for it in items:
            if it == 'cup':
                self.rect(px, y + 6, 6, 6, '#fbf4ea'); self.rect(px + 1, y + 6, 4, 2, '#7a4a2a'); px += 10
            elif it == 'cake':
                self.fill(self.E(px + 5, y + 9, 6, 4), '#fbe3c0'); self.rect(px + 3, y + 5, 4, 2, '#e06a7a'); px += 12
            elif it == 'vase':
                self.rect(px, y + 4, 5, 8, '#9fd3f0'); self.dots(self.E(px + 2, y + 1, 5, 4), ['#f2a0b8', '#f6d36a'], 6, 2); px += 10
        if chairs:
            for dx in ([x - 14, x + w + 2] if chairs >= 2 else [x - 14]):
                self.box(dx, y + h * 0.15, 12, 8, 12, shade(chair_c, 1.15), chair_c)
        return [x - (14 if chairs else 0), y, w + (28 if chairs >= 2 else 14 if chairs else 0), h]

    def counter(self, x, y, w, h=48, top='#e9e4dc', front='#8fb3a8', items=(), doors=True):
        r = self.box(x, y, w, 16, h - 16, top, front)
        if doors:
            n = max(1, int(w // 30))
            dw = w / n
            for i in range(n):
                dm = self.R(x + i * dw + 3, y + 20, dw - 6, h - 26)
                self.outline(dm, shade(front, 0.65))
                self.rect(x + i * dw + dw / 2 - 3, y + 24, 6, 1.5, '#d9c9a0')
        px = x + 6
        for it in items:
            if it == 'sink':
                self.rect(px, y + 3, 26, 11, '#c9d2da'); self.rect(px + 2, y + 5, 22, 7, '#9fb2c0'); self.rect(px + 11, y - 3, 3, 7, '#aab4bc')
                px += 32
            elif it == 'stove':
                self.rect(px, y + 2, 34, 13, '#3a3d48')
                for k in range(2):
                    self.fill(self.E(px + 9 + k * 16, y + 8, 5, 3.5), '#5a5e6c'); self.outline(self.E(px + 9 + k * 16, y + 8, 5, 3.5), '#e0704a')
                self.box(px + 4, y - 6, 12, 4, 6, '#9aa4ae', '#7a848e')
                px += 40
            elif it == 'board':
                self.rect(px, y + 4, 20, 9, '#d8ac76'); self.rect(px + 4, y + 6, 6, 3, '#e06a5a'); self.rect(px + 12, y + 6, 4, 3, '#7ac06a'); px += 26
            elif it == 'jars':
                for k in range(3):
                    self.rect(px + k * 8, y + 2, 6, 10, '#e6f1f4', 0.85); self.rect(px + k * 8, y + 7, 6, 5, ['#e0b04a', '#c45a5a', '#a87443'][k]); self.rect(px + k * 8, y + 1, 6, 2, '#b07a4a')
                px += 28
            elif it == 'bread':
                self.fill(self.E(px + 8, y + 8, 8, 4), '#d9a35c'); self.fill(self.E(px + 20, y + 8, 6, 3.5), '#c98b4a'); px += 30
            elif it == 'register':
                self.box(px, y - 4, 24, 8, 10, '#d9d4cc', '#9a948c'); self.rect(px + 4, y - 2, 16, 3, '#5ac8a8'); px += 30
            elif it == 'kettle':
                self.fill(self.E(px + 6, y + 7, 6, 5), '#e06a5a'); self.rect(px + 2, y + 1, 8, 2, '#3a3d48'); px += 16
            elif it == 'machine':
                self.box(px, y - 10, 22, 6, 18, '#5a5e6c', '#3a3d48'); self.rect(px + 4, y + 2, 14, 3, '#c9d2da'); px += 28
            elif it == 'gap':
                px += 20
        return r

    def fridge(self, x, y, w=34, h=72, c='#e6eef0'):
        r = self.box(x, y, w, 6, h - 6, shade(c, 1.05), c)
        self.rect(x, y + 6 + (h - 6) * 0.35, w, 1.5, shade(c, 0.6))
        self.rect(x + w - 6, y + 12, 2, 12, '#9aa4ae'); self.rect(x + w - 6, y + 32, 2, 18, '#9aa4ae')
        for i, cc in enumerate(('#f2a0b8', '#9fd3f0', '#f6d36a')):
            self.rect(x + 5 + i * 7, y + 14 + i * 3, 5, 5, cc)
        self.rect(x + 6, y + 36, 14, 10, '#fbf8f0')
        return r

    def plant_big(self, cx, bot, kind='tall', s=1.0):
        self.pot(cx, bot, 1.25 * s, kind=kind)
        return [cx - 12 * s, bot - 34 * s, 24 * s, 34 * s]

    def arcade_cab(self, x, y, w=34, h=64, c='#4b3a8c', screen='#5ad8f0', marquee='#f26a9a'):
        r = self.box(x, y, w, 8, h - 8, shade(c, 1.2), c)
        self.rect(x + 3, y + 10, w - 6, 8, marquee)
        self.rect(x + 5, y + 12, w - 10, 2, shade(marquee, 1.3))
        self.rect(x + 4, y + 20, w - 8, 20, '#1a1a2a'); self.rect(x + 6, y + 22, w - 12, 16, screen)
        for i in range(4):
            self.rect(x + 8 + (i * 5) % (w - 16), y + 25 + i * 3, 4, 2, ['#ffffff', '#f6d36a', '#f26a9a', '#9af06a'][i])
        self.rect(x + 3, y + 42, w - 6, 8, shade(c, 0.8))
        self.fill(self.E(x + 10, y + 45, 2.5, 2.5), '#e04a4a'); self.fill(self.E(x + 20, y + 45, 2, 2), '#4ae0a0'); self.fill(self.E(x + 26, y + 45, 2, 2), '#f6d36a')
        g = self.E(x + w / 2, y + 30, w * 0.9, 26); self.img[g] = self.img[g] * 0.9 + col(screen) * 0.1
        return r

    def claw(self, x, y, w=60, h=84, c='#f26a9a'):
        r = self.box(x, y, w, 10, h - 10, shade(c, 1.15), c)
        self.rect(x + 4, y + 12, w - 8, h * 0.5, '#bfe8f4', 0.55)
        for i in range(9):
            self.plush(x + 10 + (i * 13) % (w - 18), y + 12 + h * 0.5 - (i // 4) * 6, 0.55, ['#d9a477', '#f2c4cf', '#bfe3ff', '#f6d36a', '#c9e8a8'][i % 5])
        self.rect(x + w / 2 - 1, y + 12, 2, 14, '#c9d2da'); self.rect(x + w / 2 - 5, y + 25, 10, 3, '#c9d2da')
        self.rect(x + 4, y + 12, 2, h * 0.5, '#ffffff', 0.5)
        self.rect(x + 6, y + h - 22, 14, 10, '#1a1a2a')
        self.fill(self.E(x + w - 14, y + h - 16, 4, 4), '#f6d36a')
        return r

    def neon(self, x, y, w, h, c='#f26a9a'):
        m = self.R(x, y, w, h) & ~self.R(x + 2, y + 2, w - 4, h - 4)
        self.fill(m, shade(c, 1.4))
        g = self.E(x + w / 2, y + h / 2, w * 0.8, h * 1.4); self.img[g] = self.img[g] * 0.86 + col(c) * 0.14

    def flower_table(self, x, y, w=96, h=40, c='#a8744c'):
        r = self.box(x, y, w, 18, h - 18, shade(c, 1.1), c)
        for i in range(int(w // 16)):
            bx = x + 4 + i * 16
            self.box(bx, y - 6, 12, 4, 10, '#7a848e', '#5a6470', light=False)
            self.leaves(bx + 6, y - 10, 8, 6, n=14)
            self.dots(self.E(bx + 6, y - 12, 8, 6), [['#f2a0b8', '#ffffff'], ['#f6d36a', '#f2a04a'], ['#c4b2f2', '#ffffff'], ['#e04a5a', '#f2a0b8']][i % 4], 12, 2)
        return [x, y - 18, w, h + 18]

    def bucket(self, cx, bot, flowers=('#f2a0b8', '#ffffff')):
        self.box(cx - 7, bot - 14, 14, 4, 10, '#9aa4ae', '#7a848e', light=False)
        self.leaves(cx, bot - 18, 9, 7, n=16)
        self.dots(self.E(cx, bot - 20, 9, 6), flowers, 14, 2)
        return [cx - 9, bot - 26, 18, 26]

    def crate(self, x, y, w=26, h=24, c='#b48a5e'):
        r = self.box(x, y, w, 7, h - 7, shade(c, 1.1), c)
        self.rect(x + 2, y + 7 + (h - 7) / 2, w - 4, 1.5, shade(c, 0.65))
        return r

    def cabinet(self, x, y, w=40, h=56, c='#8c7a6a', drawers=3):
        r = self.box(x, y, w, 8, h - 8, shade(c, 1.1), c)
        dh = (h - 12) / drawers
        for i in range(drawers):
            self.outline(self.R(x + 4, y + 10 + i * dh, w - 8, dh - 3), shade(c, 0.6))
            self.rect(x + w / 2 - 4, y + 10 + i * dh + dh / 2 - 2, 8, 2, '#d9c9a0')
        return r

    def pillar(self, x, y, w=24, h=90, c='#c9c2d6'):
        r = self.box(x, y, w, 8, h - 8, shade(c, 1.1), c)
        for k in range(3):
            self.rect(x + 5 + k * 6, y + 10, 2, h - 20, shade(c, 0.85))
        return r

    def easel(self, x, y, w=40, h=56, art=1):
        self.rect(x + 4, y + 8, 2, h - 8, '#8c5a3a'); self.rect(x + w - 6, y + 8, 2, h - 8, '#8c5a3a')
        self.frame(x, y, w, h * 0.6, art, '#d9c09a')
        self.rect(x, y + h * 0.6, w, 3, '#8c5a3a')
        return [x, y + h * 0.6, w, h * 0.4]

    def glow(self, cx, cy, rx, ry, c='#ffe6a8', a=0.18):
        g = self.E(cx, cy, rx, ry)
        d = np.sqrt(((self.c.xx[g] / K - cx) / rx) ** 2 + ((self.c.yy[g] / K - cy) / ry) ** 2)
        t = ((1 - d) * a)[:, None]
        self.img[g] = self.img[g] * (1 - t) + col(c) * t

    def floor_lamp(self, cx, bot, shade_c='#fbe2b0'):
        self.drop(cx - 6, bot - 6, 12, 6, 0.75, 2, 2)
        self.fill(self.E(cx, bot - 2, 6, 2.5), '#6b6b78')
        self.rect(cx - 1, bot - 50, 2, 48, '#7a6a5a')
        m = self.R(cx - 9, bot - 62, 18, 14) & ~self.R(cx - 9, bot - 62, 3, 4) & ~self.R(cx + 6, bot - 62, 3, 4)
        self.fill(m, shade_c); self.outline(m, shade(shade_c, 0.6))
        self.glow(cx, bot - 40, 40, 36, '#ffe6a8', 0.14)
        return [cx - 9, bot - 14, 18, 14]

    def guitar(self, cx, bot, c='#c9793a'):
        self.drop(cx - 8, bot - 10, 16, 10, 0.75, 2, 2)
        body = self.E(cx, bot - 10, 8, 9) | self.E(cx, bot - 22, 6, 6)
        self.fill(body, c); self.outline(body, shade(c, 0.45))
        self.fill(self.E(cx, bot - 17, 2.5, 2.5), '#3a2418')
        self.rect(cx - 1.5, bot - 48, 3, 26, '#6a4228'); self.rect(cx - 2.5, bot - 52, 5, 6, '#3a2418')
        return [cx - 9, bot - 14, 18, 14]

    def tv(self, x, y, w=70, h=40, c='#5a4636'):
        r = self.box(x, y + 22, w, 10, h - 22, shade(c, 1.1), c)
        self.rect(x + 8, y - 8, w - 16, 30, '#20222c'); self.rect(x + 10, y - 6, w - 20, 25, '#3a5a8a')
        self.rect(x + 12, y - 4, 16, 3, '#9fd3f0', 0.7)
        self.rect(x + w / 2 - 8, y + 22, 16, 3, '#20222c')
        self.box(x + 6, y + 26, 18, 4, 4, '#ece8e0', '#bcb8b0', light=False)
        return [x, y + 22, w, h - 12]

    def doormat(self, x, y, w=44, h=14, c='#c97a5a'):
        self.rect(x, y, w, h, c)
        self.rect(x + 3, y + 3, w - 6, h - 6, shade(c, 1.15))
        st = self.R(x + 3, y + 3, w - 6, h - 6) & ((self.c.xx // K) % 4 == 0)
        self.img[st] = shade(c, 0.9)
        self.outline(self.R(x, y, w, h), shade(c, 0.5))
