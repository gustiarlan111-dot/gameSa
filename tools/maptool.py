"""Map design toolkit for the Godot project: one command that audits every area (or one) and writes
a report, so the same mistakes are caught before they reach the game.

  python3 tools/maptool.py check [area ...]      # validators below, exit code 1 on errors
  python3 tools/maptool.py catalog OUT.png        # asset catalog: contact sheet of every HD prop
  python3 tools/maptool.py preview AREA OUT.png   # map preview: ground + props + colliders + stairs

Validators per area:
  missing assets     prop types not in props.json, images or HD tiles missing on disk
  navigation         spawn free, every door / quest point / examine spot reachable from spawn
  doors              door rect reachable, the arrival point (tx, ty) in the target map is free
  collision          prop colliders covering a door rect or a stair, props outside the map
  stairs/elevation   each stair's top and bottom landing is walkable and both ends connect
  pixel consistency  HD maps (tiles @2x) that still use 1x props, props with odd texel sizes
  performance        props, distinct textures, estimated texture memory per area
"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'assets'
sys.path.insert(0, str(ROOT / 'tools/worldgen'))
import common                                                               # noqa: E402


def load():
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    return M, P, Q


def _img_size(rel, cache={}):
    if rel not in cache:
        p = A / rel
        cache[rel] = Image.open(p).size if p.exists() else None
    return cache[rel]


def overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def check_area(name, M, P, Q):
    a = M['areas'][name]
    err, warn, info = [], [], {}
    # ---- missing assets
    a2 = dict(a)
    a2['props'] = [p for p in a.get('props', []) if p.get('type') in P]
    for p in a.get('props', []):
        if p.get('type') not in P:
            err.append('missing prop type %s at %s,%s' % (p.get('type'), p.get('x'), p.get('y')))
        elif _img_size(P[p['type']]['image']) is None:
            err.append('missing image %s' % P[p['type']]['image'])
        if 'alt' in p and p['alt'] not in P:
            err.append('missing alt prop type %s' % p['alt'])
    if a.get('image') and not (A / a['image']).exists():
        err.append('missing ground image %s' % a['image'])
    for t in a.get('tiles', []):
        if not (A / t['image']).exists():
            err.append('missing tile %s' % t['image'])
    # ---- navigation
    blocked = common.blocked_fn(a2, P)
    seen, st = common.reachable(a2, blocked)
    if not seen.any():
        err.append('spawn %s blocked' % a['spawn'])

    def reach(x, y, r=40):
        j0, j1 = max(0, int((y - r) // st)), int((y + r) // st) + 1
        i0, i1 = max(0, int((x - r) // st)), int((x + r) // st) + 1
        return seen[j0:j1, i0:i1].any()

    for d in a.get('doors', []):
        x, y, w, h = d['rect']
        if not reach(x + w / 2, y + h / 2, max(w, h) / 2 + 30):
            err.append('door %s not reachable from spawn' % d['id'])
        for p in a2['props']:
            dd = P[p['type']]
            if dd.get('cw', 0) and dd.get('ch', 0):
                box = [p['x'] - dd['cw'] / 2, p['y'] - dd['ch'], dd['cw'], dd['ch']]
                if overlap(box, [x, y + h, w, 24]):     # the tile you stand on to use the door
                    err.append('prop %s blocks the front of door %s' % (p['type'], d['id']))
        tgt = M['areas'].get(d.get('to'))
        if tgt is None:
            err.append('door %s leads to unknown area %s' % (d['id'], d.get('to')))
        elif 'tx' in d:
            t2 = dict(tgt); t2['props'] = [p for p in tgt.get('props', []) if p.get('type') in P]
            if common.blocked_fn(t2, P)(d['tx'], d['ty']):
                warn.append('door %s arrives on a blocked spot %s,%s in %s' % (d['id'], d['tx'], d['ty'], d['to']))
    for e in a.get('examine', []):
        if blocked(e['x'], e['y']) and not reach(e['x'], e['y'], e.get('r', 56)):
            err.append('examine %s unreachable' % e['id'])
        elif not blocked(e['x'], e['y']) and not seen[int(e['y'] // st), int(e['x'] // st)]:
            err.append('examine %s unreachable' % e['id'])
    pts = [(m[0], m[3], m[4], m[5]) for m in common.migrate_quests(json.loads(json.dumps(Q)), name, lambda x, y: (x, y))]
    bad = common.validate(a2, P, pts)
    for b in bad:
        err.append('quest point %s %s at %s,%s' % (b[1], b[0], b[2], b[3]))
    # ---- stairs / elevation
    for s in a.get('stairs', []):
        x, y, w, h = s['rect']
        if s.get('dir', 'down') in ('down', 'up'):
            ends = [(x + w / 2, y - 16), (x + w / 2, y + h + 16)]
        else:
            ends = [(x - 16, y + h / 2), (x + w + 16, y + h / 2)]
        mid = (x + w / 2, y + h / 2)
        for ex, ey in ends + [mid]:
            if blocked(ex, ey):
                err.append('stairs %s: landing %d,%d blocked' % (s.get('id', '?'), ex, ey))
            elif not seen[int(ey // st), int(ex // st)]:
                err.append('stairs %s: landing %d,%d not connected' % (s.get('id', '?'), ex, ey))
        for p in a2['props']:
            dd = P[p['type']]
            if dd.get('cw', 0) and dd.get('ch', 0) and overlap([p['x'] - dd['cw'] / 2, p['y'] - dd['ch'], dd['cw'], dd['ch']], s['rect']):
                err.append('prop %s collider sits on stairs %s' % (p['type'], s.get('id', '?')))
    # ---- props outside the map
    for p in a2['props']:
        if not (0 <= p['x'] <= a['w'] and 0 <= p['y'] <= a['h'] + 40):
            warn.append('prop %s outside map at %s,%s' % (p['type'], p['x'], p['y']))
    # ---- pixel consistency
    hd = bool(a.get('tiles'))
    lowres = sorted({p['type'] for p in a2['props'] if '@2x' not in P[p['type']]['image']})
    if hd and lowres:
        warn.append('HD map uses %d 1x prop types: %s' % (len(lowres), ', '.join(lowres[:12])))
    for t in {p['type'] for p in a2['props']}:
        sz = _img_size(P[t]['image'])
        if sz and '@2x' in P[t]['image'] and (sz[0] % 2 or sz[1] % 2):
            warn.append('HD prop %s has an odd pixel size %s (blurs on texel grid)' % (t, sz))
    # ---- performance
    types = {p['type'] for p in a2['props']}
    mem = sum((lambda s: s[0] * s[1] * 4 if s else 0)(_img_size(P[t]['image'])) for t in types)
    nt = len(a.get('tiles', []))
    mem += sum(t['w'] * t['h'] * 4 * 4 for t in a.get('tiles', []))
    info.update(props=len(a2['props']), textures=len(types), tiles=nt, tex_mb=round(mem / 2 ** 20, 1),
                walkable_pct=round(100 * seen.mean(), 1))
    if len(a2['props']) > 900:
        warn.append('%d props: heavy for low-end Android' % len(a2['props']))
    if mem > 300 * 2 ** 20:
        warn.append('texture memory %.0f MB' % (mem / 2 ** 20))
    return err, warn, info


def cmd_check(names):
    M, P, Q = load()
    names = names or list(M['areas'])
    total = 0
    lines = ['# Map check', '']
    for n in names:
        e, w, i = check_area(n, M, P, Q)
        total += len(e)
        lines.append('## %s  (%s)' % (n, ', '.join('%s %s' % kv for kv in i.items())))
        lines += ['- ERROR ' + x for x in e] + ['- warn ' + x for x in w]
        if not e and not w:
            lines.append('- ok')
        print('%-20s errors %3d  warnings %3d  %s' % (n, len(e), len(w), i))
    out = ROOT / 'build' / 'map_check.md'
    out.parent.mkdir(exist_ok=True)
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('report:', out)
    return 1 if total else 0


def cmd_catalog(out):
    M, P, Q = load()
    ims = []
    for pid, d in sorted(P.items()):
        if '@2x' in d['image'] and (A / d['image']).exists():
            im = Image.open(A / d['image']).convert('RGBA')
            im.thumbnail((160, 200))
            ims.append((pid, im))
    cols = 12
    cw, chh = 170, 230
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * cw, rows * chh), (92, 140, 84, 255))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for k, (pid, im) in enumerate(ims):
        x, y = (k % cols) * cw, (k // cols) * chh
        sheet.alpha_composite(im, (x + (cw - im.width) // 2, y + 205 - im.height))
        d.text((x + 4, y + 212), pid[:26], fill=(255, 255, 255, 255))
    sheet.save(out)
    print(len(ims), 'HD props ->', out)


def cmd_preview(name, out, scale=0.5):
    M, P, Q = load()
    a = M['areas'][name]
    g = Image.open(A / a['image']).convert('RGBA').resize((int(a['w'] * scale), int(a['h'] * scale)))
    for p in sorted(a.get('props', []), key=lambda p: (P.get(p['type'], {}).get('layer') != 'floor', p['y'])):
        d = P.get(p['type'])
        if not d or not (A / d['image']).exists():
            continue
        im = Image.open(A / d['image']).convert('RGBA')
        k = (0.5 if '@2x' in d['image'] else 1.0) * scale
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        g.alpha_composite(im, (int(p['x'] * scale - im.width / 2), int(p['y'] * scale - im.height)))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(g, 'RGBA')
    if '--colliders' in sys.argv:
        for x, y, w, h in a['walls']:
            dr.rectangle([x * scale, y * scale, (x + w) * scale, (y + h) * scale], outline=(255, 40, 40, 220))
        for p in a.get('props', []):
            d = P.get(p['type'], {})
            if d.get('cw', 0) and d.get('ch', 0):
                x, y = p['x'] - d['cw'] / 2, p['y'] - d['ch']
                dr.rectangle([x * scale, y * scale, (x + d['cw']) * scale, p['y'] * scale], outline=(255, 200, 0, 200))
        for s in a.get('stairs', []):
            x, y, w, h = s['rect']
            dr.rectangle([x * scale, y * scale, (x + w) * scale, (y + h) * scale], outline=(40, 200, 255, 255), width=2)
    g.save(out)
    print('preview ->', out)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == 'check':
        sys.exit(cmd_check([x for x in args[1:] if not x.startswith('--')]))
    elif args[0] == 'catalog':
        cmd_catalog(args[1])
    elif args[0] == 'preview':
        cmd_preview(args[1], args[2])
