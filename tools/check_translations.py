"""Check source coverage and placeholder integrity without GUI dependencies."""
import ast
import re
import string
from pathlib import Path
import polib

ROOT = Path(__file__).resolve().parents[1]
PERCENT = re.compile(r'%(?:\([^)]+\))?[#0 +\-]*\d*(?:\.\d+)?[hlL]?[diouxXeEfFgGcrsa%]')


def placeholders(value):
    percent = [token for token in PERCENT.findall(value) if token != '%%']
    braces = [(field, spec, conv) for _, field, spec, conv in string.Formatter().parse(value) if field is not None]
    return percent, braces


def main():
    catalog = polib.pofile(str(ROOT / 'locale/zh_CN/LC_MESSAGES/pronterface.po'))
    entries = {entry.msgid: entry for entry in catalog if not entry.obsolete}
    errors = []
    for entry in entries.values():
        if not entry.msgstr or entry.fuzzy:
            errors.append(f'Missing or fuzzy translation: {entry.msgid!r}')
        if placeholders(entry.msgid) != placeholders(entry.msgstr):
            errors.append(f'Changed placeholders: {entry.msgid!r} -> {entry.msgstr!r}')
    files = [*ROOT.joinpath('printrun').rglob('*.py'), *ROOT.glob('*.py')]
    found = set()
    for path in files:
        if path.name.startswith('.'):
            continue
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_':
                if not node.args or not isinstance(node.args[0], ast.Constant):
                    errors.append(f'Dynamic gettext key: {path.relative_to(ROOT)}:{node.lineno}')
                    continue
                value = node.args[0].value
                found.add(value)
                if value not in entries:
                    errors.append(f'Untranslated source: {path.relative_to(ROOT)}:{node.lineno}: {value!r}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(found)} source messages, {len(entries)} translations, no missing or fuzzy entries; placeholders intact')


if __name__ == '__main__':
    main()
