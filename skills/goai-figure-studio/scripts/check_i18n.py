"""Fail when a figure's translation table no longer covers the figure.

The failure this exists for: a lane edited the Chinese labels in the reconstruction script to match the
manuscript glossary, but not the translation table the English set is built from. Nothing checked, so the
English set quietly became unbuildable — 13 strings with no entry — and was only noticed days later, by
accident, while auditing something else.

    python3 check_i18n.py --tr <r5_en.py or tr.json> <zh scene.json ...>

Exits non-zero and lists every source-script string the table cannot translate. Run it in the figure gate,
and any time the Chinese labels change.
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

CJK = re.compile(r'[　-鿿＀-￯]')


def load_tr(path: Path) -> dict:
    """Take the table from a JSON file, or from the first dict literal named TR in a Python file.

    The Python file is parsed, never imported: it may reach for a design-system library that is not on this
    path, and a coverage check should not depend on that.
    """
    if path.suffix == '.json':
        return json.loads(path.read_text(encoding='utf-8'))
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == 'TR' for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit(f'{path}: 找不到 TR 表（既不是 .json，也没有 TR = {{...}} 字面量）')


def strings(scene: Path):
    doc = json.loads(scene.read_text(encoding='utf-8'))
    for slide in doc.get('slides', [doc]):
        for el in slide['elements']:
            if el.get('kind') == 'text' and CJK.search(el.get('text', '')):
                yield el['id'], el['text']


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--tr', required=True, type=Path, help='translation table: a .json, or a .py holding TR')
    ap.add_argument('scenes', nargs='+', type=Path)
    a = ap.parse_args()

    tr = load_tr(a.tr)
    missing = {}
    total = 0
    for s in a.scenes:
        for eid, text in strings(s):
            total += 1
            if text not in tr:
                missing.setdefault(text, []).append(f'{s.parent.name}:{eid}')

    print(f'{len(a.scenes)} 个场景、{total} 条源语言字串，TR 收录 {len(tr)} 条')
    if not missing:
        print('覆盖完整')
        return 0
    print(f'\n!! {len(missing)} 条没有译文 —— 英文版无法重生成：')
    for text, where in sorted(missing.items()):
        print(f'   {text!r}  ({", ".join(where[:3])})')
    return 1


if __name__ == '__main__':
    sys.exit(main())
