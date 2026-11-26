"""Shared writer for assets/data/props.json: indent 2 like the hand-kept file, but lists of plain
numbers (U2a "vol", U2b "ext" points) stay on one line so the file does not grow by a line per number."""
import json
import re

_NUMS = re.compile(r'\[\s*(-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)*)\s*\]')


def dumps(data):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return _NUMS.sub(lambda m: '[' + ', '.join(v.strip() for v in m.group(1).split(',')) + ']', text) + '\n'
