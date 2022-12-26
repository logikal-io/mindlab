from pytest import raises

from mindlab.utils import _missing_extra


def test_missing_extra() -> None:
    with raises(ImportError, match='You must install the `test` extra'):
        _missing_extra('test')(some_argument='works')
