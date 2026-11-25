"""Find assets and data nobody uses, and optionally delete them (git history keeps everything).

A file is used when
  * its path (relative to assets/), path without extension, or file name appears in game data
    (assets/data/*.json) or Godot code/scenes (src/, tests/, project.godot), or
  * it is loaded by a pattern the code uses: map tiles of a used area, normal maps of a used prop,
    audio/ui/fx/portrait files whose name appears as a quoted token in code or data, character
    sheets the Actor loader actually picks (it prefers @2x and the v53/8-direction sheets), or
  * it is an animal sprite (kept: the area data lists animals; the Godot port draws them next).
Props: props.json entries that no map, quest or code mentions are unused, with their images.
    python3 tools/asset_audit.py [--delete]
"""
import sys, re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'assets'
SHEETS_8 = ['walk_8dir_v53', 'idle_8dir_v53', 'poses_v53', 'poses', 'walk']
SHEETS = ['walk_v53', 'idle_v53', 'poses_v53', 'poses', 'walk']


def read(paths):
    return '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in paths if p.exists())


def actor_sheets(char_dir):
    """Files the Actor loader would open for this character (mirror of src/actor.gd _sheet)."""
    eight = char_dir.name in ('arland', 'sofia')
    names = SHEETS_8 if eight else SHEETS
    used, have = set(), lambda n: (char_dir / n).exists()
    def pick(n):
        for f in (n + '@2x.png', n + '.png'):
            if have(f):
                return f
    w8 = pick('walk_8dir_v53') if eight else None
    i8 = pick('idle_8dir_v53') if eight else None
    wv, iv = (None, None) if eight else (pick('walk_v53'), pick('idle_v53'))
    for f in (w8, i8, wv, iv):
        if f:
            used.add(f)
    if (eight and not (w8 and i8)) or (not eight and not (wv and iv)):
        if pick('walk'):
            used.add(pick('walk'))
    pv = pick('poses_v53')
    used.add(pv) if pv else (used.add(pick('poses')) if pick('poses') else None)
    return {u for u in used if u}


def main():
    data_files = list((A / 'data').rglob('*.json'))
    code_files = list((ROOT / 'src').rglob('*.gd')) + list((ROOT / 'src').rglob('*.tscn')) + list((ROOT / 'tests').rglob('*'))
    code_files = [p for p in code_files if p.is_file() and p.suffix in ('.gd', '.tscn', '.json')] + [ROOT / 'project.godot']
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))
    code = read(code_files)
    other_data = read([p for p in data_files if p.name != 'props.json'])
    text = code + other_data
    tokens = set(re.findall(r'"([A-Za-z0-9_\-]+)"', text)) | set(re.findall(r"'([A-Za-z0-9_\-]+)'", code))
    # props: used if a map places it (type or alt), or code/quests name it
    used_props = set()
    for a in M['areas'].values():
        for p in a.get('props', []):
            used_props.add(p.get('type')); used_props.add(p.get('alt'))
    for pid in P['props']:
        if pid in tokens:
            used_props.add(pid)
    # hd_* props stay: the map generators in tools/worldgen place them by name on the next rebuild
    dead_props = sorted(k for k in P['props'] if k not in used_props and not k.startswith('hd_'))
    prop_images = {}
    for pid, d in P['props'].items():
        prop_images.setdefault(d['image'], set()).add(pid)
    live_images = {img for img, ids in prop_images.items() if ids & used_props}
    used_tiles = {t['image'] for a in M['areas'].values() for t in a.get('tiles', [])}
    used_tiles |= {a.get('image') for a in M['areas'].values()}
    char_used = {}
    unused = []
    for f in sorted(A.rglob('*')):
        if not f.is_file() or f.suffix in ('.import', '.json') or f.name.startswith('.'):
            continue
        rel = f.relative_to(A).as_posix()
        top = rel.split('/')[0]
        stem = rel.rsplit('.', 1)[0]
        base = f.stem.replace('@2x', '')
        if rel in used_tiles or rel in live_images:
            continue
        if rel in prop_images:                                  # image of dead props only
            unused.append(rel); continue
        if rel.startswith('props/hd/n/'):
            if 'props/hd/' + f.stem[:-2] + '@2x.png' in live_images:
                continue
            unused.append(rel); continue
        if top == 'maps':
            unused.append(rel); continue
        if top == 'characters' and '/portraits/' not in rel and rel.count('/') == 2:
            cd = f.parent
            if cd not in char_used:
                char_used[cd] = actor_sheets(cd)
            if f.name not in char_used[cd]:
                unused.append(rel)
            continue
        if top in ('animals',) or '/portraits/' in rel or base in ('cat_meow', 'dog_bark', 'duck_quack', 'bird_chirp'):
            continue
        if base.endswith('_b') and base[:-2] in tokens:          # random variant of a named sound
            continue
        if rel in text or stem in text or f.name in text or base in tokens or (base.endswith('_theme') and base[:-6] in tokens):
            continue
        if top == 'ui' and base.startswith('emote_') and base[6:] in tokens:
            continue
        unused.append(rel)
    size = sum((A / r).stat().st_size for r in unused) / 2 ** 20
    groups = {}
    for r in unused:
        groups.setdefault('/'.join(r.split('/')[:2]) if r.count('/') > 1 else r.split('/')[0], []).append(r)
    print('dead prop entries: %d of %d' % (len(dead_props), len(P['props'])))
    print('unused files: %d, %.1f MB' % (len(unused), size))
    for g, L in sorted(groups.items()):
        print('  %-34s %4d  %6.1f MB  e.g. %s' % (g, len(L), sum((A / r).stat().st_size for r in L) / 2 ** 20, L[0].split('/')[-1]))
    out = ROOT / 'build' / 'asset_audit.txt'
    out.parent.mkdir(exist_ok=True)
    out.write_text('# dead props\n' + '\n'.join(dead_props) + '\n# unused files\n' + '\n'.join(unused) + '\n', encoding='utf-8')
    print('list:', out)
    if '--delete' in sys.argv:
        for r in unused:
            (A / r).unlink()
            imp = A / (r + '.import')
            if imp.exists():
                imp.unlink()
        for k in dead_props:
            del P['props'][k]
        (A / 'data/props.json').write_text(json.dumps(P, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('deleted', len(unused), 'files and', len(dead_props), 'prop entries')


if __name__ == '__main__':
    main()
