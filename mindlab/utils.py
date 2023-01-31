import time
from functools import partial
from typing import Any, Callable, Optional


class Timer:
    def __init__(self) -> None:
        self.time: Optional[int] = None

    def __enter__(self) -> 'Timer':
        self.time = time.perf_counter_ns()
        return self

    def __exit__(self, *_args: Any, **_kwargs: Any) -> None:
        self.time = time.perf_counter_ns() - self.time  # type: ignore[operator]


def _raise_missing_extra(extra: str, *_args: Any, **_kwargs: Any) -> Any:
    raise ImportError(f'You must install the `{extra}` extra')


def _missing_extra(extra: str) -> Callable[..., Any]:
    return partial(_raise_missing_extra, extra)
