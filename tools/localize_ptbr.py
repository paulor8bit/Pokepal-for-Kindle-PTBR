"""Apply the reviewed PT-BR literal catalog without changing save identifiers."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'--[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')

def translate(source, catalog):
    def replace(match):
        token = match.group()
        if token.startswith('--') or token[1:-1] not in catalog:
            return token
        return json.dumps(catalog[token[1:-1]], ensure_ascii=False)
    return TOKEN.sub(replace, source)

if __name__ == '__main__':
    catalog = json.loads((ROOT/'tools/pt-BR.json').read_text(encoding='utf-8'))
    for path in list((ROOT/'pokepal.koplugin').glob('*.lua')) + [ROOT/'native/runtime.lua']:
        path.write_text(translate(path.read_text(encoding='utf-8'), catalog), encoding='utf-8', newline='\n')
