from pathlib import Path
from typing import Callable, Iterator

from numpy import random
from pyspark.sql import SparkSession
from pytest import fixture
from pytest_logikal.utils import assert_image_equal, hide_traceback
from pytest_mock import MockerFixture

from mindlab.magics import MindLabMagics
from mindlab.plot import Figure
from mindlab.spark import spark_session

CheckFigure = Callable[[Figure, str], None]


@fixture
def magics(mocker: MockerFixture) -> MindLabMagics:
    return MindLabMagics(shell=mocker.Mock(parent=None), parent=None)  # nosec: the shell is mocked


@fixture
def generator() -> random.Generator:
    return random.default_rng(seed=42)


@fixture
def check_figure(tmp_path: Path) -> CheckFigure:
    @hide_traceback
    def check_figure_wrapper(figure: Figure, name: str) -> None:
        expected_path = Path(__file__).parent / 'plots' / name
        assert_image_equal(actual=figure.as_bytes(), expected=expected_path, temp_path=tmp_path)
    return check_figure_wrapper


@fixture(scope='session')
def spark() -> Iterator[SparkSession]:
    with spark_session() as session:
        yield session
