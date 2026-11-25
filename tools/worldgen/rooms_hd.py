"""HD interiors drawn from code with tools/worldgen/interior.py. One function per room; every quest
point, examine spot, door and the sleep spot of the old room stay where they were and are validated
reachable before anything is written.

Run:  python3 tools/worldgen/rooms_hd.py <area|all> [--preview DIR] [--apply]
"""
import sys, json, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hdmap import HDMap, A          # noqa: E402
from interior import Room           # noqa: E402

ROOMS = {}


def room(fn):
    ROOMS[fn.__name__] = fn
    return fn


# ---------------------------------------------------------------------------------------- homes
@room
def sofia_room(r):
    W, H = 600, 448
    r.shell(W, H, floor='planks', wall='#f6e2d8', wainscot='#e2a7a8', trim='#fff3ea', pattern='dots',
            floor_pal=('#c08e62', '#c9996c', '#d2a476', '#b98760'), door=(274, 52))
    # back wall: windows, frames, fairy lights, hanging plants
    r.window(160, 20, 64, 46, curtain='#f6c3cd')
    r.window(386, 20, 62, 46, curtain='#f6c3cd')
    r.string_lights(34, 150, 16, sag=10, n=10)
    r.frame(244, 24, 24, 30, 3); r.frame(276, 30, 18, 22, 0); r.frame(300, 22, 22, 18, 2)
    r.frame(336, 26, 20, 26, 1)
    r.poster(470, 22, 28, 38, '#fbe9ef', '#9fd3f0'); r.poster(512, 26, 30, 34, '#eef5fb', '#f2a0b8')
    r.hanging_plant(40, 10, 34); r.hanging_plant(560, 10, 34)
    r.clock(232, 70, 7, '#d98a9a')
    # floor
    r.rug(300, 300, 74, 46, '#e9a7ad', '#f8d7d3')
    r.rug(150, 214, 22, 12, '#f2cdd3', '#fff1f1', round_=False)
    r.rug(452, 202, 34, 16, '#f2cdd3', '#fff1f1', round_=True)
    r.doormat(279, 404, 42, 14, '#d98a8a')
    # bed corner (sleep spot 65,190)
    r.block.append(r.bed(36, 72, 78, 116, blanket='#f2a9b6', pattern='quilt'))
    r.plush(98, 110, 0.9, '#d9a477')
    r.block.append(r.nightstand(118, 74))
    r.slippers(84, 200)
    r.plush(126, 214, 0.8, '#f2c4cf')
    # vanity under the second window side (phone / gift at 350-356,192)
    r.block.append(r.vanity(320, 64, 72, 46))
    r.frame(304, 66, 12, 14, 4)
    r.block.append(r.basket(400, 92, 22, 22))
    # dresser with plant, wardrobe on the right wall (outfit point 442,348 in front)
    r.block.append(r.cabinet(500, 92, 56, 48, '#f3e7dc', drawers=3))
    r.pot(514, 92, 0.6, kind='flower'); r.plush(540, 92, 0.6, '#c9c9d9')
    r.block.append(r.wardrobe(486, 226, 70, 100, '#f3e7dc', '#d9b48a'))
    r.pot(548, 360, 1.0, kind='tall'); r.block.append([536, 330, 24, 32])
    # reading corner left: bookshelf + sofa + floor cushions
    r.block.append(r.bookshelf(30, 236, 98, 74, '#c99a6a', rows=3))
    r.block.append(r.sofa(36, 336, 92, 42, '#eba2ac', ('#fbe3c0', '#bfe3f4')))
    r.pot(144, 410, 0.8, kind='leafy'); r.block.append([132, 392, 24, 20])
    r.cushion(236, 362, 1.0, '#f4b6c2'); r.cushion(262, 370, 0.9, '#c4b2f2')
    # writing desk bottom right (letters / stamp crafting happen at the rug)
    r.block.append(r.desk(420, 368, 96, 40, '#f0dccb', items=('laptop', 'lamp', 'mug'), chair=None))
    r.plush(214, 330, 0.7, '#f2c4cf')
    r.slippers(366, 404, '#c4b2f2')
    # little lived-in clutter
    for i, cc in enumerate(('#c45a5a', '#5a7ac4', '#e0b04a')):
        r.rect(190, 300 - i * 3, 16, 3, cc)
    r.rect(392, 330, 14, 10, '#fbf8f0'); r.rect(396, 334, 14, 10, '#fff6e8')
    r.pot(170, 132, 0.9, kind='flower'); r.block.append([160, 108, 22, 26])
    r.block.append(r.basket(214, 98, 20, 18, '#d9b48a', laundry=False))
    r.pot(224, 98, 0.5, kind='leafy')
    r.block.append(r.floor_lamp(150, 372, '#fbd3dc'))
    r.block.append(r.table(408, 160, 26, 20, '#f0dccb', chairs=0, round_=True, items=('vase',)))
    r.pot(36, 214, 0.7, kind='flower'); r.block.append([28, 196, 18, 18])
    r.wall_shelf(470, 74, 70, ('book', 'plush'))
    r.glow(300, 300, 150, 90, '#ffe9c8', 0.08)


@room
def arland_room(r):
    W, H = 600, 448
    r.shell(W, H, floor='planks', wall='#dfe8ee', wainscot='#7d9cb3', trim='#f4f7f9', pattern='stripe',
            floor_pal=('#9c7a5a', '#a6845f', '#b08e68', '#927050'), door=(276, 52))
    r.window(170, 20, 62, 46, curtain='#9fb9d4')
    r.poster(244, 22, 28, 38, '#f2ead8', '#e0866a'); r.poster(278, 26, 24, 30, '#e8f0f6', '#5a7ac4')
    r.clock(312, 40, 9, '#5a6a7a')
    r.frame(440, 24, 36, 26, 1); r.frame(484, 28, 18, 22, 4)
    r.wall_shelf(40, 52, 90, ('book', 'plant', 'jar'))
    r.hanging_plant(560, 10, 30)
    # floor
    r.rug(300, 292, 82, 48, '#5f7f9c', '#a9c3d8', round_=False)
    r.doormat(281, 404, 42, 14, '#8a6a4a')
    # computer corner (phone / projector / screen / fuse 348-380, 194-225)
    r.block.append(r.desk(326, 70, 116, 44, '#8a6a52', items=('monitor', 'lamp', 'mug', 'books'), chair='#4a5a6c'))
    r.block.append(r.crate(446, 96, 22, 22, '#6a7684'))
    # bed on the right (sleep spot 415,190)
    r.block.append(r.bed(476, 72, 80, 116, blanket='#5a7ac4', sheet='#eef2f6', frame='#7a5a40', pattern='stripes'))
    r.block.append(r.nightstand(446, 140, 26, c='#7a5a40'))
    r.slippers(440, 200, '#5a6a7a')
    # wardrobe + bookshelf left (note at 103,244 stays open in front)
    r.block.append(r.wardrobe(30, 96, 64, 100, '#9c7a5a', '#d9b48a'))
    r.block.append(r.bookshelf(100, 96, 56, 66, '#7a5a40', rows=3, deco=False))
    r.pot(176, 130, 1.0, kind='tall'); r.block.append([164, 100, 24, 32])
    # gaming / guitar corner bottom left, beanbag bottom right
    r.block.append(r.sofa(40, 330, 96, 42, '#6a8aa8', ('#f0d0a0', '#e0866a')))
    r.block.append(r.table(160, 352, 44, 26, '#8a6a52', chairs=0, items=('cup',)))
    r.block.append(r.beanbag(500, 370, '#e0866a'))
    r.block.append(r.cabinet(520, 250, 40, 60, '#6a7684', drawers=3))
    r.pot(544, 250, 0.6, kind='leafy')
    r.basket(456, 300, 20, 18, '#8a9aa8')
    r.cushion(236, 360, 0.9, '#a9c3d8')
    r.block.append(r.guitar(148, 412))
    r.block.append(r.floor_lamp(32, 320, '#f0dcb0'))
    r.block.append(r.tv(196, 96, 70, 40))
    r.rect(410, 330, 18, 6, '#6a7684'); r.rect(412, 326, 4, 14, '#4a5260'); r.rect(422, 326, 4, 14, '#4a5260')
    for i, cc in enumerate(('#5a7ac4', '#e0b04a', '#6aa86a', '#c45a5a')):
        r.rect(470, 410 - i * 3, 18, 3, cc)
    r.glow(380, 100, 80, 40, '#bfe8ff', 0.1)


def build(area, apply=False, preview=None):
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = M['areas'][area]
    seed = int(hashlib.sha256(area.encode()).hexdigest()[:8], 16)
    m = HDMap(area, base['w'], base['h'], seed)
    r = Room(m, seed)
    ROOMS[area](r)
    walls = [[int(round(v)) for v in b] for b in r.block]
    m.collision = lambda P_: walls
    extra = dict(visualStyle='godot_hd_interior', visualUpdate='godot_rooms_hd', v4Layout=None,
                 v6Layout=dict(version=3, generator='tools/worldgen/rooms_hd.py', hd=True))
    out = None
    if preview:
        Path(preview).mkdir(parents=True, exist_ok=True)
        out = str(Path(preview) / ('%s.png' % area))
    return m.write(base, extra, P, Q, apply=apply, preview=out)


if __name__ == '__main__':
    which = sys.argv[1]
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    for a in (ROOMS if which == 'all' else which.split(',')):
        build(a, apply='--apply' in sys.argv, preview=prev)
