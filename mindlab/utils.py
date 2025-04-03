import time
from os import getenv
from typing import Any

from logikal_utils.project import tool_config

mindlab_config = tool_config('mindlab')


class Timer:
    def __init__(self) -> None:
        self.time: int | None = None

    def __enter__(self) -> 'Timer':
        self.time = time.perf_counter_ns()
        return self

    def __exit__(self, *_args: Any, **_kwargs: Any) -> None:
        self.time = time.perf_counter_ns() - self.time  # type: ignore[operator]


def get_config(
    name: str,
    value: Any | None = None,
    value_type: Any | None = None,
    required: bool = False,
) -> Any:
    if value is not None:
        return value

    if (value := mindlab_config.get(name)) is not None:
        return value

    value = getenv(f'MINDLAB_{name.upper()}')
    if value_type == list:
        value = value.split(',') if value else []

    if required and value is None:
        raise ValueError(f'You must specify configuration "{name}"')

    return value
