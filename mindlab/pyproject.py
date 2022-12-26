from pathlib import Path

import tomli

PYPROJECT = (
    tomli.loads(Path('pyproject.toml').read_text(encoding='utf-8'))
    if Path('pyproject.toml').exists() else {}
)
MINDLAB_CONFIG = PYPROJECT.get('tool', {}).get('mindlab', {})
