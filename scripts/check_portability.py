"""Check the portable operational knowledge without reading private work folders."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MACHINE_PATH = re.compile(r'/Users/|/home/[^/\s]+/|/private/(?:tmp|var)/|[A-Za-z]:\\\\Users\\\\')
PRIVATE_KEY = re.compile(r'^(?:password|cookie|cookies|token|access_token|refresh_token|authorization_header|account|plan|.*credits.*|.*downloads_(?:before|after|used)|local_path|download_path)$', re.I)


def inspect_record(value, location, errors):
    if isinstance(value, dict):
        for key, child in value.items():
            if PRIVATE_KEY.fullmatch(key):
                errors.append(f'{location}: private account/session field {key}')
            inspect_record(child, location, errors)
    elif isinstance(value, list):
        for child in value:
            inspect_record(child, location, errors)


def validate(root=ROOT):
    errors = []
    required = ['AGENTS.md', 'skills/poetry-to-music/SKILL.md',
                'skills/poetry-to-music/scripts/prepare_queue.py',
                'production/README.md', 'kb/guides/portable-workspace.md',
                '.devcontainer/devcontainer.json', '.devcontainer/Dockerfile']
    for name in required:
        if not (root / name).is_file():
            errors.append(f'Missing portable resource: {name}')
    paths = [root / 'AGENTS.md', root / 'kb/guides/portable-workspace.md']
    for folder in ('skills', 'production', '.devcontainer'):
        paths.extend(p for p in (root / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        name = str(path.relative_to(root))
        if MACHINE_PATH.search(text):
            errors.append(f'{name}: machine-specific home/temp path')
        if path.suffix == '.json':
            try:
                value = json.loads(text)
            except ValueError:
                errors.append(f'{name}: invalid JSON')
                continue
            if name.startswith('production/'):
                inspect_record(value, name, errors)
    skill = root / 'skills/poetry-to-music/SKILL.md'
    if skill.exists():
        for target in re.findall(r'\]\((references/[^)]+)\)', skill.read_text()):
            if not (skill.parent / target).is_file():
                errors.append(f'Missing skill reference: {target}')
    if errors:
        raise ValueError('\n'.join(errors))


if __name__ == '__main__':
    try:
        validate()
    except ValueError as exc:
        raise SystemExit(str(exc))
    print('Portable operational knowledge is present; no machine paths or private account fields found.')
