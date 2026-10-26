"""Package both editions and the native runtime's corresponding source."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import zipfile
from build_native import SOURCES

REPO=Path(__file__).resolve().parents[1]
PLUGIN=REPO/'pokepal.koplugin'
VERSION=re.search(r'version\s*=\s*"([\d.]+)"',(PLUGIN/'_meta.lua').read_text(encoding="utf-8")).group(1)
STAMP=(2026,10,26,0,0,0)

def add(package,path,name,executable=False):
    info=zipfile.ZipInfo(name,STAMP)
    info.compress_type=zipfile.ZIP_DEFLATED
    info.create_system=3
    info.external_attr=(0o100755 if executable else 0o100644)<<16
    package.writestr(info,path.read_bytes(),compresslevel=9)

def files(root):
    for directory, folders, names in os.walk(root):
        folders[:] = sorted(d for d in folders if not d.startswith('.') and d != '__pycache__')
        for name in sorted(names):
            path=Path(directory)/name
            if not name.startswith('.') and path.suffix not in {'.pyc','.tmp','.dat','.old','.log','.pgm','.exe'}:
                yield path,path.relative_to(root).as_posix()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deps',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=REPO/'dist')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    archives=[]
    plugin=out/f'PokeK-PTBR-v{VERSION}-koreader.zip'
    with zipfile.ZipFile(plugin,'w') as z:
        for path,relative in files(PLUGIN):add(z,path,'koreader/plugins/pokepal.koplugin/'+relative)
    archives.append(plugin)
    standalone=out/f'PokeK-PTBR-v{VERSION}-kual.zip'
    binary=REPO/'native/build/pokepal'
    assert binary.is_file(),'Build the native host first.'
    with zipfile.ZipFile(standalone,'w') as z:
        prefix='extensions/pokepal/'
        add(z,binary,prefix+'pokepal',True)
        add(z,REPO/'native/runtime.lua',prefix+'runtime.lua')
        add(z,REPO/'native/LICENSE-GPL-3.0.txt',prefix+'LICENSE-GPL-3.0.txt')
        add(z,REPO/'native/README.md',prefix+'BUILD-AND-SOURCE.md')
        for path,relative in files(REPO/'native/kual'):add(z,path,prefix+relative,path.suffix=='.sh')
        for path,relative in files(REPO/'native/fonts'):add(z,path,prefix+'fonts/'+relative)
        for path,relative in files(REPO/'native/licenses'):add(z,path,prefix+'licenses/'+relative)
        for path,relative in files(PLUGIN):add(z,path,prefix+'game/'+relative)
        z.writestr(prefix+'data/',b'')
    archives.append(standalone)
    source=out/f'PokeK-PTBR-v{VERSION}-corresponding-source.zip'
    with zipfile.ZipFile(source,'w') as z:
        for path,relative in files(REPO):
            if relative.startswith(('native/build/','tests/rendered/','dist/')):continue
            add(z,path,'PokeK/'+relative,path.suffix=='.sh')
        for path in sorted((REPO/'.github/workflows').glob('*.yml')):
            add(z,path,'PokeK/.github/workflows/'+path.name)
        for name in ('.gitattributes','.gitignore'):
            add(z,REPO/name,'PokeK/'+name)
        for dependency in SOURCES:
            root=args.deps.resolve()/dependency
            assert root.is_dir(),root
            for path,relative in files(root):add(z,path,f'dependencies/{dependency}/'+relative)
            z.writestr(f'dependencies/{dependency}/POKEPAL_REVISION.txt',SOURCES[dependency][1]+'\n')
    archives.append(source)
    checks=out/f'PokeK-PTBR-v{VERSION}-SHA256.txt'
    checks.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in archives))
    for archive in archives:
        with zipfile.ZipFile(archive) as z:assert z.testzip() is None
        print(f'{archive.name}: {archive.stat().st_size:,} bytes')
    with zipfile.ZipFile(standalone) as z:
        names=z.namelist()
        assert 'extensions/pokepal/pokepal' in names
        assert not any(n.endswith(('.dat','.old','.log','.exe','.pgm')) for n in names)
        assert z.getinfo('extensions/pokepal/pokepal').external_attr>>16 & 0o111
    print('Archives, executable permissions, clean saves and checksums verified.')

if __name__=='__main__':main()
