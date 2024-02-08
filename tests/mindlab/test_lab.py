import os
from pathlib import Path

from pytest import raises
from pytest_mock import MockerFixture

from mindlab.lab import install_config, main


def test_install_config(tmp_path: Path) -> None:
    install_config(virtual_env_dir=tmp_path)
    assert (tmp_path / 'etc/ipython/ipython_kernel_config.py').exists()
    assert (tmp_path / 'share/jupyter/lab/settings/overrides.json').exists()


def test_install_config_error(mocker: MockerFixture) -> None:
    mocker.patch.dict(os.environ, {}, clear=True)
    with raises(RuntimeError, match='virtual environment'):
        install_config()


def test_lab(mocker: MockerFixture) -> None:
    jupyter_main = mocker.patch('mindlab.lab.jupyter_main')
    with raises(SystemExit, match='^0$'):
        main()
    assert jupyter_main.called


def test_lab_install(mocker: MockerFixture) -> None:
    jupyter_main = mocker.patch('mindlab.lab.jupyter_main')
    with raises(SystemExit, match='^0$'):
        main(args=['--install'])
    assert not jupyter_main.called


def test_lab_error(mocker: MockerFixture) -> None:
    mocker.patch('mindlab.lab.jupyter_main', side_effect=RuntimeError('Test'))
    with raises(SystemExit, match='^Error: Test$'):
        main()
