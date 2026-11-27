#!/usr/bin/env python3
"""U5d: one name per place. U5c renamed the dream places on their area title only; doors, quest
objectives, captions and dialogue still said "Starfall Village", "Rain Garden", ... This replaces the
old English names in every text a player reads with the Indonesian name.

Only player-facing keys are touched (dialogue t, text, sub, label, title, desc, hint, the per-route
objectives arland/sofia). Area ids, image paths, design notes ("note", layout notes) and the area
titles written by tools/story_u5c.py ("Taman Kenangan (Memory Garden)") keep their English.

Idempotent:  python3 tools/names_u5d.py
"""
import json
import re
from pathlib import Path

A = Path(__file__).resolve().parents[1] / 'assets/data'

# longest first, so "Starfall Village" goes before "Starfall"
NAMES = [
    ('Starfall Village', 'Desa Bintang Jatuh'),
    ('starfall village', 'Desa Bintang Jatuh'),
    ('Memory Garden', 'Taman Kenangan'),
    ('Lantern Field', 'Padang Lentera'),
    ('Star Path', 'Jalan Bintang'),
    ('Eternal Garden', 'Taman Abadi'),
    ('Rain Garden', 'Taman Hujan'),
    ('Clockwork Station', 'Stasiun Jam'),
    ('Moonlight Lake', 'Danau Cahaya Bulan'),
    ('Memory Bridge', 'Jembatan Kenangan'),
    ('Hall of Tomorrow', 'Balai Hari Esok'),
    ('Memory Realm', 'dunia kenangan'),
    ('Starfall', 'Desa Bintang Jatuh'),
]
KEYS = {'t', 'text', 'sub', 'label', 'title', 'desc', 'hint', 'arland', 'sofia', 'objective'}
FILES = ['story.json', 'quests.json', 'maps.json', 'memory_book.json']
AREA_TITLE = re.compile(r'^[^()]+ \([A-Z][A-Za-z ]+\)$')     # "Taman Kenangan (Memory Garden)"


def fix(s: str) -> str:
    if AREA_TITLE.match(s):
        return s
    for old, new in NAMES:
        s = s.replace(old, new)
    return s


def walk(o, key=None, count=None):
    if isinstance(o, dict):
        return {k: walk(v, k, count) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v, key, count) for v in o]
    if isinstance(o, str) and key in KEYS:
        n = fix(o)
        if n != o:
            count[0] += 1
        return n
    return o


def main():
    total = 0
    for f in FILES:
        p = A / f
        d = json.loads(p.read_text(encoding='utf-8'))
        c = [0]
        d = walk(d, None, c)
        if c[0]:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('%-16s %d teks' % (f, c[0]))
        total += c[0]
    print('total', total)


if __name__ == '__main__':
    main()
