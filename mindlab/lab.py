import os
import shutil
import sys
from collections.abc import Iterable
from pathlib import Path

from jupyter_core.command import main as jupyter_main

CONFIG_DIR = Path(__file__).parent / 'config'


def install_config(virtual_env_dir: Path | None = None, force: bool = False) -> None:
    if not virtual_env_dir and 'VIRTUAL_ENV' not in os.environ:
        raise RuntimeError('You must run this command in a virtual environment')

    virtual_env_dir = virtual_env_dir or Path(os.environ['VIRTUAL_ENV'])
    config = {
        'IPython kernel configuration': {
            'source': CONFIG_DIR / 'ipython_kernel_config.py',
            'destination': virtual_env_dir / 'etc/ipython/ipython_kernel_config.py',
        },
        'JupyterLab default settings overrides': {
            'source': CONFIG_DIR / 'jupyterlab_settings_overrides.json',
            'destination': virtual_env_dir / 'share/jupyter/lab/settings/overrides.json',
        },
    }
    for name, paths in config.items():
        if force or not paths['destination'].exists():
            print(f'Installing {name} at "{paths["destination"]}')
            paths['destination'].parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src=paths['source'], dst=paths['destination'])


def main(args: Iterable[str] | None = None) -> None:
    install_config()
    if '--install' in (args or sys.argv):
        print('Installation successful')
        sys.exit(0)

    sys.argv = ['jupyter', 'lab'] + sys.argv[1:]
    try:
        jupyter_main()
        sys.exit(0)
    except RuntimeError as error:
        sys.exit(f'Error: {error}')
