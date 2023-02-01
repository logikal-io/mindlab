from os import environ

from pytest import raises
from pytest_mock import MockerFixture

from mindlab.utils import MINDLAB_CONFIG, _missing_extra, get_config


def test_get_config(mocker: MockerFixture) -> None:
    env = {'MINDLAB_CONFIG': 'env_value', 'MINDLAB_ENV_ONLY': 'env_only_value'}
    mocker.patch.dict(MINDLAB_CONFIG, {'config': 'value'}, clear=True)
    mocker.patch.dict(environ, env, clear=True)

    assert get_config('config') == 'value'
    assert get_config('config', 'test') == 'test'
    assert get_config('env_only') == 'env_only_value'
    assert get_config('env_only', 'test') == 'test'
    assert get_config('non_existent') is None
    assert get_config('non_existent', 'test') == 'test'
    with raises(ValueError):
        get_config('non_existent', required=True)


def test_missing_extra() -> None:
    with raises(ImportError, match='You must install the `test` extra'):
        _missing_extra('test')(some_argument='works')
