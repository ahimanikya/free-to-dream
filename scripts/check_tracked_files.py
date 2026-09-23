"""Reject accidentally staged recordings, private archives and oversized files."""
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[1]
names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
errors = []
for name in filter(None, names):
    path = root / name
    if name.startswith(('local-assets/', '.venv/', 'site/', 'site-public/')):
        errors.append(name)
    elif path.suffix.lower() in {'.mp3','.mp4','.wav','.m4a','.mov','.webm'}:
        errors.append(name)
    elif path.is_file() and path.stat().st_size > 10 * 1024 * 1024:
        errors.append(name)
if errors: raise SystemExit('Keep these files outside Git: ' + ', '.join(errors))
print('Tracked files contain no recordings, private archives or oversized assets.')
