import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from jupyter_core.command import main as jupyter_main

CONFIG_DIR = Path(__file__).parent / 'config'


def install_kernel_config(target_dir: Optional[Path] = None) -> None:
    if not target_dir and 'VIRTUAL_ENV' not in os.environ:
        raise RuntimeError('You must run this command in a virtual environment')

    target_dir = target_dir or Path(os.environ['VIRTUAL_ENV']) / 'etc/ipython'

    kernel_config_src = CONFIG_DIR / 'ipython_kernel_config.py'
    kernel_config_dst = target_dir / kernel_config_src.name
    if not kernel_config_dst.exists():
        print(f'Installing IPython kernel configuration at "{kernel_config_dst}"')
        kernel_config_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src=kernel_config_src, dst=kernel_config_dst)


def main() -> None:
    install_kernel_config()
    os.environ['JUPYTERLAB_SETTINGS_DIR'] = str(CONFIG_DIR)
    sys.argv = ['jupyter', 'lab']
    try:
        jupyter_main()
        sys.exit(0)
    except RuntimeError as error:
        sys.exit(f'Error: {error}')
