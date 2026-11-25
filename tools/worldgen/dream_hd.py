"""Memory / dream maps, HD rebuild from code (2 texels per unit, same sizes, doors and quest points).

The layout is derived from the story itself: every quest point, examine spot, door and the spawn
become nodes; nearby nodes merge into clearings; a minimum spanning tree joins the clearings with
gently curving paths. Each map then gets its own theme: ground and path palettes, water, the trees
and lights that line the paths, decor around the clearings and a few hand-placed landmarks.
Cave mode (Gua Kristal) carves the walkable floor out of solid rock instead.

Usage: python3 tools/worldgen/dream_hd.py <area|all> [--preview DIR] [--apply]
"""
import sys, json, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hdmap import HDMap, K, GRASS, PATH, STONE, WATER, DECK, SAND, A   # noqa: E402
from paint import rgb, hash2                                           # noqa: E402
from ground import noise, dist_from                                    # noqa: E402
import common                                                          # noqa: E402

ROCK = 11

THEMES = {
    'memory_garden': dict(
        grass=('#5b4f8f', '#63579a', '#6c5fa4', '#7568ad', '#8073b6', '#8c80bf'),
        path='tiles', path_pal=('#e9e2f4', '#dcd3ee'), plaza=('#efe8f8', '#e2d9f2', '#d6ccec', '#cbc0e4'), mortar='#a89cc8',
        trees=(['hd_tree_dream_a', 'hd_tree_dream_b', 'hd_tree_dream_c', 'hd_tree_cherry_a'], [3, 3, 3, 1]),
        lights='hd_lantern_post', light_every=210,
        ring=['hd_crystal', 'hd_crystal_cyan', 'hd_flowers_violet', 'hd_mushrooms_glow'],
        small=(['hd_flowers_violet', 'hd_flowers_white', 'hd_flowers_pink', 'hd_mushrooms_glow', 'hd_crystal', 'hd_grass_tall_b'], [3, 2, 2, 2, 1, 2]),
        specials=[('hd_arch', 412, 640), ('hd_star_stone', 1000, 470), ('hd_stone_lantern', 950, 1000), ('hd_stone_lantern', 1050, 1000)],
        density=1.0),
    'lantern_field': dict(
        grass=('#2f4a46', '#35524c', '#3c5b52', '#436559', '#4b6e60', '#557868'),
        path='dirt', path_pal=('#8c7656', '#977f5c', '#a18a64', '#ab946c'), plaza=('#b8a27e', '#c4ae88', '#ccb893', '#a8946e'), mortar='#7a6a52',
        trees=(['hd_tree_lantern', 'hd_tree_lantern_b', 'hd_tree_dream_a', 'hd_tree_pine_b'], [4, 3, 1, 1]),
        lights='hd_lantern_post', light_every=230,
        ring=['hd_flowers_yellow', 'hd_grass_tall', 'hd_mushrooms_glow', 'hd_stone_lantern'],
        small=(['hd_grass_tall', 'hd_grass_tall_b', 'hd_flowers_yellow', 'hd_flowers_white', 'hd_mushrooms_glow', 'hd_fern_a'], [4, 3, 2, 2, 1, 1]),
        specials=[('hd_bench', 1250, 720), ('hd_stone_lantern', 1180, 980), ('hd_stone_lantern', 1220, 1030)],
        density=1.0),
    'star_path': dict(
        grass=('#1f2550', '#252c5c', '#2c3468', '#343d74', '#3d4680', '#47508c'),
        path='tiles', path_pal=('#a8aee8', '#959be0'), plaza=('#c4c8f4', '#b4b9ee', '#d2d5f8', '#a6abe6'), mortar='#5a5fa0',
        trees=(['hd_tree_dream_c', 'hd_tree_dream_a', 'hd_tree_dream_b', 'hd_star_stone'], [3, 2, 2, 1]),
        lights='hd_star_stone', light_every=260,
        ring=['hd_crystal', 'hd_crystal_cyan', 'hd_star_stone', 'hd_mushrooms_glow'],
        small=(['hd_crystal_cyan', 'hd_mushrooms_glow', 'hd_flowers_white', 'hd_grass_tall_b'], [1, 4, 3, 4]),
        specials=[('hd_carving_star', 1275, 520), ('hd_telescope', 2075, 460), ('hd_carving_moon', 475, 372)],
        density=0.9, stars=True),
    'starfall_village': dict(
        grass=('#2a3a5c', '#304266', '#374a70', '#3f537a', '#485c84', '#52668e'),
        path='bricks', path_pal=('#8a86a8', '#948fb2', '#7e7a9c', '#a09bbd'), plaza=('#a6a2c2', '#b2aecc', '#9a96b8', '#bcb8d4'), mortar='#5a5878',
        trees=(['hd_tree_pine_a', 'hd_tree_pine_b', 'hd_tree_dream_c', 'hd_tree_lantern'], [3, 3, 2, 1]),
        lights='hd_lantern_post', light_every=200,
        ring=['hd_flowers_white', 'hd_bush_a', 'hd_star_stone', 'hd_planter_violet'],
        small=(['hd_flowers_white', 'hd_flowers_violet', 'hd_bush_a', 'hd_bush_b', 'hd_mushrooms_glow', 'hd_grass_tall'], [2, 2, 2, 2, 1, 2]),
        specials=[('hd_cottage_blue', 900, 600), ('hd_cottage_red', 1520, 600), ('hd_cottage_green', 900, 1120),
                  ('hd_well', 1200, 760), ('hd_star_stone', 1200, 1210), ('hd_mailbox', 980, 640), ('hd_crate_stack', 1600, 640)],
        density=0.8, stars=True),
    'eternal_garden': dict(
        grass=('#4f8f5a', '#57995f', '#5fa264', '#68ab69', '#72b46f', '#7dbd76'),
        path='dirt', path_pal=('#d8c8a8', '#e0d0b0', '#cfbf9e', '#e8d9bb'), plaza=('#efe6d4', '#e6dcc6', '#dcd1b8', '#f4ecde'), mortar='#b8a88a',
        trees=(['hd_tree_cherry_a', 'hd_tree_cherry_b', 'hd_tree_blossom', 'hd_tree_oak_a', 'hd_tree_willow'], [3, 3, 2, 2, 1]),
        lights='hd_lamp_gold', light_every=240,
        ring=['hd_flowerbed', 'hd_bush_rose', 'hd_flowers_pink', 'hd_flowers_white'],
        small=(['hd_flowers_pink', 'hd_flowers_white', 'hd_flowers_yellow', 'hd_bush_rose', 'hd_bush_a', 'hd_grass_tall'], [3, 3, 2, 2, 2, 1]),
        specials=[('hd_tree_lantern_b', 1200, 780), ('hd_gazebo', 1875, 1240), ('hd_arch', 1200, 1460), ('hd_arch', 525, 1040),
                  ('hd_bench', 1350, 660), ('hd_bench', 1050, 790)],
        density=1.0),
    'rain_garden': dict(
        grass=('#3a5a52', '#40625a', '#476b61', '#4f7468', '#577d70', '#608678'),
        path='tiles', path_pal=('#8a9098', '#7e848c'), plaza=('#9aa0a8', '#8e949c', '#a6acb4', '#848a92'), mortar='#5a6068',
        trees=(['hd_tree_willow', 'hd_tree_oak_b', 'hd_tree_dark_a', 'hd_tree_dream_b'], [3, 2, 2, 1]),
        lights='hd_stone_lantern', light_every=230,
        ring=['hd_reeds', 'hd_fern_a', 'hd_bush_b', 'hd_mushrooms_glow'],
        small=(['hd_fern_a', 'hd_fern_b', 'hd_grass_tall', 'hd_reeds', 'hd_mushrooms', 'hd_bush_b'], [3, 2, 3, 2, 1, 1]),
        specials=[('hd_arch', 960, 620), ('hd_lantern_post', 840, 1010), ('hd_lantern_post', 560, 960), ('hd_lantern_post', 1080, 530),
                  ('hd_lantern_post', 850, 320), ('hd_lantern_post', 1420, 310)],
        density=1.0, puddles=True),
    'clockwork_station': dict(
        grass=('#2e2a4a', '#342f54', '#3a355e', '#413b68', '#484272', '#504a7c'),
        path='tiles', path_pal=('#b8a27e', '#a8926e'), plaza=('#d8c49a', '#cdb88e', '#e2cea6', '#c2ad84'), mortar='#7a6a4a',
        trees=(['hd_column_stone', 'hd_tree_dream_c', 'hd_tree_dream_a'], [1, 3, 2]),
        lights='hd_lamp_gold', light_every=200,
        ring=['hd_column_stone', 'hd_flowers_white', 'hd_planter_violet', 'hd_lamp_gold'],
        small=(['hd_mushrooms_glow', 'hd_grass_tall_b', 'hd_flowers_white'], [3, 3, 2]),
        specials=[('hd_bench', 960, 900), ('hd_bench', 700, 640), ('hd_bench', 1280, 640)],
        density=0.6, stars=True, clocks=True),
    'moonlight_lake': dict(
        grass=('#243a4a', '#294254', '#2f4a5e', '#355368', '#3c5c72', '#44667c'),
        path='dirt', path_pal=('#8a8aa0', '#9494aa', '#80809a', '#a0a0b4'), plaza=('#b4b4c8', '#a8a8bc', '#bebed2', '#9c9cb0'), mortar='#5a5a70',
        trees=(['hd_tree_willow', 'hd_tree_dream_b', 'hd_tree_pine_b', 'hd_tree_dark_b'], [3, 2, 2, 2]),
        lights='hd_stone_lantern', light_every=240,
        ring=['hd_reeds', 'hd_flowers_white', 'hd_crystal_cyan', 'hd_mushrooms_glow'],
        small=(['hd_reeds', 'hd_flowers_white', 'hd_grass_tall', 'hd_fern_a', 'hd_mushrooms_glow'], [2, 2, 3, 1, 1]),
        specials=[('hd_rowboat', 1300, 860), ('hd_pier_post', 860, 760), ('hd_pier_post', 920, 760)],
        lakes=[(1260, 880, 430, 220), (560, 800, 200, 110)], density=0.9, stars=True),
    'memory_bridge': dict(
        grass=('#3b3a62', '#42416c', '#4a4976', '#525180', '#5b5a8a', '#646394'),
        path='tiles', path_pal=('#cfc6e8', '#c2b8de'), plaza=('#ddd5f0', '#d0c7e8', '#e8e1f6', '#c6bce0'), mortar='#8a80b0',
        trees=(['hd_tree_dream_a', 'hd_tree_dream_b', 'hd_tree_dream_c', 'hd_crystal'], [3, 3, 3, 1]),
        lights='hd_lantern_post', light_every=200,
        ring=['hd_crystal', 'hd_crystal_cyan', 'hd_flowers_violet', 'hd_mushrooms_glow'],
        small=(['hd_flowers_violet', 'hd_flowers_white', 'hd_mushrooms_glow', 'hd_grass_tall_b'], [2, 2, 2, 3]),
        specials=[], river=(590, 70), bridge=(904, 1016), density=0.9, stars=True),
    'hall_of_tomorrow': dict(
        grass=('#4a3f6a', '#524674', '#5a4e7e', '#635688', '#6c5f92', '#76689c'),
        path='tiles', path_pal=('#efe9f6', '#e2dbee'), plaza=('#f6f2fa', '#ebe5f4', '#e0d9ee', '#d4cce6'), mortar='#a89cc8',
        trees=(['hd_tree_dream_a', 'hd_tree_dream_c', 'hd_tree_dream_b'], [2, 2, 1]),
        lights='hd_lamp_gold', light_every=180,
        ring=['hd_column_stone', 'hd_flowers_white', 'hd_crystal', 'hd_planter_violet'],
        small=(['hd_flowers_white', 'hd_flowers_violet', 'hd_crystal', 'hd_mushrooms_glow'], [2, 2, 1, 1]),
        specials=[('hd_arch', 750, 360), ('hd_arch', 1210, 360), ('hd_arch', 960, 420), ('hd_star_stone', 965, 560)],
        density=0.8, stars=True),
    'arsip_memudar': dict(      # story v7: the archive where unspoken stories fade
        grass=('#4a4a58', '#525262', '#5a5a6c', '#636376', '#6c6c80', '#76768a'),
        path='tiles', path_pal=('#c8c2b4', '#bab4a6'), plaza=('#d6d0c2', '#cac4b6', '#e0dacc', '#beb8aa'), mortar='#8a8478',
        trees=(['hd_column_stone', 'hd_tree_dark_a', 'hd_tree_dark_b', 'hd_tree_willow'], [2, 3, 3, 1]),
        lights='hd_stone_lantern', light_every=230,
        ring=['hd_column_stone', 'hd_flowers_white', 'hd_mushrooms_glow', 'hd_crystal'],
        small=(['hd_flowers_white', 'hd_grass_tall_b', 'hd_mushrooms_glow', 'hd_fern_b'], [2, 3, 2, 2]),
        specials=[('hd_arch', 800, 380), ('hd_column_stone', 560, 640), ('hd_column_stone', 1040, 640),
                  ('hd_mailbox', 1290, 650), ('hd_bench', 420, 760), ('hd_star_stone', 800, 860)],
        density=0.8, stars=True),
    'kenangan_gazebo': dict(    # story v7: Taman Kota on a rainy day forty years ago
        grass=('#5a6a4a', '#627252', '#6a7a5a', '#728262', '#7a8a6a', '#849472'),
        path='dirt', path_pal=('#a8987a', '#b2a284', '#9e8e70', '#bcac8e'), plaza=('#c4b494', '#cebe9e', '#baaa8a', '#d6c6a8'), mortar='#8a7a5e',
        trees=(['hd_tree_oak_a', 'hd_tree_oak_b', 'hd_tree_willow', 'hd_tree_cherry_a'], [3, 2, 2, 1]),
        lights='hd_lamp_gold', light_every=220,
        ring=['hd_flowerbed', 'hd_bush_a', 'hd_flowers_white', 'hd_bush_rose'],
        small=(['hd_flowers_white', 'hd_flowers_yellow', 'hd_grass_tall', 'hd_fern_a', 'hd_bush_b'], [2, 2, 3, 2, 1]),
        specials=[('hd_gazebo', 800, 540), ('hd_bench', 500, 610), ('hd_bench', 1120, 760), ('hd_lamp_gold', 640, 520),
                  ('hd_lamp_gold', 960, 520)],
        density=0.9, puddles=True),
    'gua_kristal': dict(
        grass=('#2a2440', '#2f2848', '#352d50', '#3b3258', '#423860', '#493e68'),
        path='cave', path_pal=('#8a82b8', '#968ec4', '#7e76ac', '#a29ad0'), plaza=('#9a92c8', '#a69ed4', '#8e86bc', '#b2aadc'), mortar='#2a2440',
        trees=(['hd_crystal', 'hd_crystal_cyan'], [1, 1]),
        lights='hd_crystal_cyan', light_every=99999,
        ring=['hd_crystal', 'hd_crystal_cyan', 'hd_mushrooms_glow', 'hd_rock_a'],
        small=(['hd_mushrooms_glow'], [1]),
        specials=[], cave=True, density=1.0),
}
KEEP_TYPES = {'lantern_off', 'v41_lantern_off_lantern'}     # story-lit lanterns keep their alt look


def nodes_for(area, base, M, Q):
    pts = [(p[3], p[4]) for p in common.migrate_quests(json.loads(json.dumps(Q)), area, lambda x, y: (x, y)) if p[3] is not None]
    pts += [(e['x'], e['y']) for e in base.get('examine', [])]
    pts += [(d['tx'], d['ty']) for b in M['areas'].values() for d in b.get('doors', []) if d.get('to') == area]
    pts.append(tuple(base['spawn']))
    W, H = base['w'], base['h']
    doors = []
    for d in base['doors']:
        x, y, w, h = d['rect']
        cx, cy = x + w / 2, y + h / 2
        doors.append((cx, cy, w, h))
        pts.append((min(max(cx, 60), W - 60), min(max(cy, 70), H - 50)))
    return pts, doors


def clusters(pts, r=80):
    cl = []
    for x, y in pts:
        for c in cl:
            if (c[0] / c[2] - x) ** 2 + (c[1] / c[2] - y) ** 2 < r * r:
                c[0] += x; c[1] += y; c[2] += 1
                break
        else:
            cl.append([x, y, 1])
    return [(c[0] / c[2], c[1] / c[2], c[2]) for c in cl]


def mst(cs):
    n = len(cs)
    if n < 2:
        return []
    inside = {0}
    edges = []
    while len(inside) < n:
        best = None
        for i in inside:
            for j in range(n):
                if j in inside:
                    continue
                d = (cs[i][0] - cs[j][0]) ** 2 + (cs[i][1] - cs[j][1]) ** 2
                if best is None or d < best[0]:
                    best = (d, i, j)
        edges.append((best[1], best[2]))
        inside.add(best[2])
    return edges


def curve(a, b, rng):
    ax, ay = a[0], a[1]; bx, by = b[0], b[1]
    L = np.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / (L or 1), (bx - ax) / (L or 1)
    off = rng.uniform(-0.12, 0.12) * L
    pts = []
    for t in np.linspace(0, 1, 9):
        bend = np.sin(t * np.pi) * off
        pts.append((ax + (bx - ax) * t + nx * bend, ay + (by - ay) * t + ny * bend))
    return pts


def design(m, area, base, T, pts, doors, P):
    c = m.c
    W, H = m.W, m.H
    rng = np.random.default_rng(m.seed + 5)
    cs = clusters(pts)
    edges = mst(cs)
    polys = [curve(cs[i], cs[j], rng) for i, j in edges]
    # extra loop for richer walking: join the two farthest leaves if they are not too far apart
    cave = T.get('cave')
    pw = 120 if cave else 54
    paths = np.zeros((c.h, c.w), bool)
    for poly in polys:
        paths |= m.path(poly, pw, wob=3 if not cave else 8, salt=len(poly))
    plazas = np.zeros_like(paths)
    plaza_list = []
    for x, y, n in cs:
        r = min(120, 48 + 14 * n) * (1.5 if cave else 1.0)
        if n >= 2 or cave:
            plazas |= m.ellipse(x, y, r, r * 0.72, wob=2 if not cave else 10, salt=int(x) % 97)
            plaza_list.append((x, y, r))
    # door approaches always reach the map edge
    for cx, cy, w, h in doors:
        tx, ty = min(max(cx, 60), W - 60), min(max(cy, 70), H - 50)
        paths |= m.path([(cx, cy), (tx, ty)], max(pw, min(w, h) + 20) if cave else pw, wob=2)
    walk = paths | plazas
    # ---- ground
    grass = c.grass(T['grass'])
    if cave:
        rock = c.dirt(('#1c1830', '#221d38', '#272140', '#2d2648'))
        c.put(np.ones((c.h, c.w), bool), rock, ROCK)
        floor = c.dirt(T['path_pal'])
        c.put(walk, floor, STONE)
        edge = walk & (dist_from(~walk, 10) < 6)
        c.img[edge] *= 0.7
        nz = noise(c.h, c.w, 26, m.seed + 41); nz2 = noise(c.h, c.w, 9, m.seed + 42)
        rk = ~walk
        c.img[rk] *= (0.7 + 0.45 * nz[rk] + 0.12 * nz2[rk])[:, None]
        hl = rk & (nz > 0.62) & (np.roll(nz, 3, 0) < nz)
        c.img[hl] = c.img[hl] * 0.75 + rgb('#6a6098') * 0.25
        for _ in range(60):                       # crystal veins in the rock
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            vm = m.path([(x, y), (x + rng.uniform(-40, 40), y + rng.uniform(-30, 30))], 3) & rk
            c.img[vm] = rgb(('#7ad8e8', '#b8a8f0')[_ % 2])
        gl = noise(c.h, c.w, 60, m.seed + 43) > 0.6       # pools of crystal light on the floor
        c.img[walk & gl] = c.img[walk & gl] * 0.8 + rgb('#9ff0f0') * 0.2
        ridge = ~walk & (dist_from(walk, 10) < 5)
        c.img[ridge] = c.img[ridge] * 0.6 + rgb('#7a70a8') * 0.4
    else:
        c.put(np.ones((c.h, c.w), bool), grass, GRASS)
    # ---- water
    water = np.zeros_like(walk)
    for wz in base.get('water', []):
        water |= m.ellipse(wz['cx'], wz['cy'], wz['rx'], wz['ry'], wob=4, salt=3)
    for cx, cy, rx, ry in T.get('lakes', []):
        water |= m.ellipse(cx, cy, rx, ry, wob=5, salt=int(cx) % 31)
    if T.get('river'):
        ry_, rw = T['river']
        xs = np.arange(0, W + 40, 40)
        water |= m.path([(x, ry_ + 30 * np.sin(x / 260.0)) for x in xs], rw * 2, wob=4, salt=9)
    if T.get('puddles'):
        for _ in range(16):
            x, y = rng.uniform(100, W - 100), rng.uniform(150, H - 100)
            water |= m.ellipse(x, y, rng.uniform(30, 60), rng.uniform(14, 24), wob=2, salt=int(x) % 13)
    for x, y in pts:
        water &= ~m.ellipse(x, y, 44, 38)
    deck = np.zeros_like(walk)
    if T.get('bridge'):
        bx0, bx1 = T['bridge']
        deck = m.rect(bx0, T['river'][0] - T['river'][1] - 50, bx1 - bx0, T['river'][1] * 2 + 100)
        water |= deck & ~walk & m.rect(0, T['river'][0] - T['river'][1] - 10, W, T['river'][1] * 2 + 20)
    water &= ~walk | deck
    if not cave:
        shore = (dist_from(water, 20) < 12) & ~water
        c.put(shore & ~walk, c.dirt(('#7a7a8c', '#868698', '#9090a2', '#9a9aac')), SAND)
        w_only = water & ~deck
        if w_only.any():
            c.put(w_only, c.water(w_only, ('#1b2e5a', '#223a6a', '#2b487a', '#36588a', '#46699a')), WATER)
        # moon / star glints on the water
        ys, xs = np.nonzero(w_only[::6, ::6])
        for i in rng.integers(0, max(1, len(ys)), max(1, len(ys) // 30)):
            if len(ys):
                c.img[ys[i] * 6, xs[i] * 6:xs[i] * 6 + 4] = rgb('#cfe0ff')
    # ---- paths and clearings
    if not cave:
        kind = T['path']
        if kind == 'tiles':
            pimg = c.tiles(*T['path_pal'], size=28, grout=T['mortar'], salt=4)
        elif kind == 'bricks':
            pimg = c.bricks(T['path_pal'], bw=20, bh=10, mortar=T['mortar'], salt=4)
        else:
            pimg = c.dirt(T['path_pal'])
        c.put(paths & ~deck, pimg, PATH)
        for x, y, r in plaza_list:
            pm = m.ellipse(x, y, r, r * 0.72, wob=2, salt=int(x) % 97) & ~water
            rad, rr, th, ri = c.radial(x * K, y * K, 0.72, T['plaza'], 18, 30, salt=int(y) % 50, mortar=T['mortar'])
            c.put(pm, rad, STONE)
            c.img[pm & (rr > (r - 6) * K)] *= 0.8
            if T.get('clocks'):          # clock dial inlay: hour marks and two hands
                for h in range(12):
                    a = h / 12 * 2 * np.pi
                    hx, hy = x + np.cos(a) * r * 0.72, y + np.sin(a) * r * 0.72 * 0.72
                    c.img[m.ellipse(hx, hy, 4, 3)] = rgb('#f2d38a')
                c.img[m.path([(x, y), (x, y - r * 0.4)], 4)] = rgb('#5a4a2a')
                c.img[m.path([(x, y), (x + r * 0.5, y + 6)], 3)] = rgb('#5a4a2a')
                c.img[m.ellipse(x, y, 6, 5)] = rgb('#f2d38a')
        if deck.any():
            c.put(deck, c.planks(('#8b5d3c', '#996a46', '#a5754f', '#b07f57'), 14, salt=5, vertical=True), DECK)
            m.walk_over |= deck
        gm = c.mat == GRASS
        c.rim(np.isin(c.mat, [PATH, STONE, DECK]), gm, dark=T['mortar'], ao=(0.86, 0.93))
        c.overhang(c.mat == PATH, gm, 0.22, 1)
    # ---- sky dust: tiny star sparkles on dark dream grass
    if T.get('stars'):
        ys, xs = np.nonzero((c.mat == GRASS)[::5, ::5])
        for i in rng.integers(0, max(1, len(ys)), max(1, len(ys) // 70)):
            if len(ys):
                y, x = ys[i] * 5, xs[i] * 5
                c.img[y, x] = rgb('#fff6c8'); c.img[y - 1:y + 2, x] = np.maximum(c.img[y - 1:y + 2, x], rgb('#8a86c8'))
    edge = np.minimum.reduce([c.xx, c.yy, c.w - 1 - c.xx, c.h - 1 - c.yy])
    c.img[edge < 14] *= 0.8
    m.water_mask = water & ~deck
    return polys, plaza_list, walk


def furnish(m, T, base, pts, doors, polys, plaza_list, walk, P):
    c = m.c
    W, H = m.W, m.H
    rng = np.random.default_rng(m.seed + 9)
    pr = m.prop
    cave = T.get('cave')
    near_pts = lambda x, y, r=46: any((x - px) ** 2 + (y - py) ** 2 < r * r for px, py in pts)

    def door_zone(x, y):
        return any(abs(x - cx) < w / 2 + 50 and abs(y - cy) < h / 2 + 60 for cx, cy, w, h in doors)
    # keep story props (lanterns lit later, chests)
    for p in base['props']:
        if p['type'] in KEEP_TYPES:
            m.props.append(dict(p))
        elif p.get('altFlag') == 'CHEST_CAVE':
            m.props.append(dict(type='hd_chest', x=p['x'], y=p['y'], alt='hd_chest_open', altFlag='CHEST_CAVE'))
    for pid, x, y in T.get('specials', []):
        if pid in P:
            pr(pid, x, y)
    # lights along the paths, alternating sides
    for poly in polys:
        pts_ = np.array(poly)
        seg = np.cumsum([0] + [np.hypot(*(pts_[i + 1] - pts_[i])) for i in range(len(pts_) - 1)])
        side = 1
        for s in np.arange(T['light_every'] / 2, seg[-1], T['light_every']):
            i = min(len(pts_) - 2, np.searchsorted(seg, s) - 1)
            t = (s - seg[i]) / max(1e-6, seg[i + 1] - seg[i])
            x, y = pts_[i] + t * (pts_[i + 1] - pts_[i])
            d = pts_[i + 1] - pts_[i]; nrm = np.array([-d[1], d[0]]) / max(1e-6, np.hypot(*d))
            lx, ly = (x, y) + nrm * (72 if cave else 44) * side
            side = -side
            X, Y = int(lx * K), int(ly * K)
            if 0 < X < c.w and 0 < Y < c.h and not near_pts(lx, ly, 40) and not door_zone(lx, ly) \
                    and (cave or c.mat[Y, X] == GRASS) and not (cave and walk[Y, X]):
                pr(T['lights'], lx, ly)
    # decor ring around each clearing
    for x, y, r in plaza_list:
        n = int(6 + r / 14)
        for k in range(n):
            a = k / n * 2 * np.pi + rng.uniform(-0.15, 0.15)
            rx = x + np.cos(a) * (r + (60 if cave else 18)); ry = y + np.sin(a) * (r + (60 if cave else 18)) * 0.72
            X, Y = int(rx * K), int(ry * K)
            if 0 < X < c.w and 0 < Y < c.h and not walk[Y, X] and not near_pts(rx, ry, 36) and not door_zone(rx, ry) \
                    and c.mat[Y, X] not in (WATER, DECK):
                pr(T['ring'][k % len(T['ring'])], rx, ry)
    m.keep_out = [(x, y, 46) for x, y in pts] + [(cx, cy, max(w, h) / 2 + 50) for cx, cy, w, h in doors]
    blocked = (c.mat != (ROCK if cave else GRASS)) | (dist_from(walk, 40) < (26 if cave else 14))
    if cave:
        blocked = walk | (dist_from(walk, 60) > 26) | (dist_from(walk, 60) < 6)
    trees, wts = T['trees']
    dens = T.get('density', 1.0)
    area = W * H / 1e6
    if cave:
        m.scatter(trees, wts, int(140 * area), (20, 20, W - 40, H - 40), blocked, 16, P)
        m.scatter(['hd_rock_ledge', 'hd_rock_ledge_b', 'hd_rock_a', 'hd_rock_b'], [1, 1, 2, 2], int(60 * area), (20, 20, W - 40, H - 40), blocked, 20, P)
        m.scatter(T['small'][0], T['small'][1], int(28 * area), (20, 20, W - 40, H - 40), ~walk | (dist_from(~walk, 30) < 10), 10, P)
        return
    m.scatter(trees, wts, int(34 * area * dens), (20, 20, W - 40, 220), blocked, 22, P)
    m.scatter(trees, wts, int(24 * area * dens), (20, H - 220, W - 40, 200), blocked, 22, P)
    m.scatter(trees, wts, int(12 * area * dens), (20, 200, 220, H - 400), blocked, 22, P)
    m.scatter(trees, wts, int(12 * area * dens), (W - 240, 200, 220, H - 400), blocked, 22, P)
    m.scatter(trees, wts, int(18 * area * dens), (20, 20, W - 40, H - 40), blocked, 60, P)
    m.scatter(['hd_bush_a', 'hd_bush_b', 'hd_rock_a', 'hd_rock_b'], [2, 2, 1, 1], int(30 * area), (20, 20, W - 40, H - 40), blocked, 16, P)
    m.scatter(T['small'][0], T['small'][1], int(150 * area), (20, 20, W - 40, H - 40), blocked, 9, P)


def build(area, apply=False, preview=None):
    T = THEMES[area]
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = M['areas'][area]
    seed = int(hashlib.sha256((area + '_dream_hd').encode()).hexdigest()[:8], 16)
    m = HDMap(area, base['w'], base['h'], seed)
    pts, doors = nodes_for(area, base, M, Q)
    polys, plazas, walk = design(m, area, base, T, pts, doors, P)
    furnish(m, T, base, pts, doors, polys, plazas, walk, P)
    m.bake_shadows(P)
    W, H = m.W, m.H
    edge = []                      # the map bounds already stop walking
    if T.get('cave'):
        rock = (m.c.mat == ROCK)
        small = rock.reshape(H, K, W, K).mean(axis=(1, 3)) > 0.5
        walls = common.mask_to_walls(small, step=8)
    else:
        walls = HDMap.collision(m, P)
    door_rects = [d['rect'] for d in base['doors']]

    def cut(wl):
        out = []
        for x, y, w, h in wl:
            if any(x < dx + dw and x + w > dx and y < dy + dh and y + h > dy for dx, dy, dw, dh in door_rects):
                continue
            out.append([x, y, w, h])
        return out
    allw = cut(edge) + walls
    m.collision = lambda P_: allw
    extra = dict(ellipses=[], stairs=[], animals=base.get('animals', []), visualStyle='godot_hd_dream',
                 visualUpdate='godot_dream_hd', v6Layout=dict(version=3, generator='tools/worldgen/dream_hd.py', hd=True))
    out = None
    if preview:
        Path(preview).mkdir(parents=True, exist_ok=True)
        out = str(Path(preview) / ('%s.png' % area))
    return m.write(base, extra, P, Q, apply=apply, preview=out)


if __name__ == '__main__':
    which = sys.argv[1]
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    for a in (THEMES if which == 'all' else which.split(',')):
        build(a, apply='--apply' in sys.argv, preview=prev)
