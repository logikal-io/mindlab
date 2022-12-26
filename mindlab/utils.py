from functools import partial
from typing import Any, Callable


def _raise_missing_extra(extra: str, *_args: Any, **_kwargs: Any) -> Any:
    raise ImportError(f'You must install the `{extra}` extra')


def _missing_extra(extra: str) -> Callable[..., Any]:
    return partial(_raise_missing_extra, extra)
