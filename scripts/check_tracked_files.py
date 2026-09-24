"""Require Git LFS for recording files and keep private archives out of Git."""
from pathlib import Path
import re
import subprocess
root = Path(__file__).resolve().parents[1]
names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
errors = []
for name in filter(None, names):
    path = root / name
    if name.startswith(('local-assets/', '.venv/', 'site/', 'site-public/')):
        errors.append(name)
    elif path.suffix.lower() in {'.mp3','.mp4','.wav','.m4a','.ogg','.mov','.webm'}:
        # Check the index, not the hydrated working file, which can be large.
        size = int(subprocess.check_output(['git','cat-file','-s',':'+name], cwd=root))
        if not name.startswith('media/') or size > 256:
            errors.append(name + ' (recordings must use Git LFS under media/)')
            continue
        pointer = subprocess.check_output(['git','show',':'+name], cwd=root)
        if not re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:[0-9a-f]{64}\nsize [1-9][0-9]*\n', pointer):
            errors.append(name + ' (missing valid LFS pointer)')
        attributes = subprocess.check_output(['git','check-attr','--cached','filter','--',name],cwd=root).decode().strip()
        if not attributes.endswith(': filter: lfs'):
            errors.append(name + ' (missing LFS tracking attribute)')
    elif path.is_file() and path.stat().st_size > 10 * 1024 * 1024:
        errors.append(name)
if errors: raise SystemExit('Fix tracked files: ' + ', '.join(errors))
print('Tracked recordings use Git LFS; private archives and oversized ordinary blobs are excluded.')
