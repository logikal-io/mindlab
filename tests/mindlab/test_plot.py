from pathlib import Path

from matplotlib import pyplot
from numpy.random import Generator
from pandas import DataFrame, Series
from pytest import raises
from pytest_mock import MockerFixture

from mindlab import Figure, mock_data
from mindlab.plot import use_mindlab_styles
from tests.mindlab.conftest import CheckFigure


def test_use_mindlab_styles_refresh_fonts(mocker: MockerFixture, tmp_path: Path) -> None:
    add_font = mocker.patch('mindlab.plot.matplotlib.font_manager.fontManager.addfont')
    assert use_mindlab_styles(font_install_path=tmp_path / 'fonts')
    assert add_font.called


def test_use_mindlab_styles_refresh_styles() -> None:
    with raises(OSError, match='\'unavailable\' not found in the style library'):
        use_mindlab_styles(project_styles=['unavailable'])


def test_use_mindlab_styles_disable() -> None:
    assert not use_mindlab_styles(project_styles=False)


def test_use_mindlab_styles_error() -> None:
    with raises(ValueError):
        use_mindlab_styles(project_styles=True)


def test_invalid_tics() -> None:
    with raises(ValueError, match='tics setting'):
        Figure(xtics='invalid')


def test_boxplot(check_figure: CheckFigure) -> None:
    figure = Figure(xlabel='Sets', ylabel='Values', title='Title')
    figure.boxplot([[1, 2, 3, 4, 6], [1, 2, 3, 3, 5, 8]], labels=['set-1', 'set-2'])
    check_figure(figure, 'boxplot.png')


def test_time_series(check_figure: CheckFigure) -> None:
    figure = Figure(ylabel='Values', title='Title', xtics='year')
    figure.line(mock_data.stock_prices(days=1000))
    check_figure(figure, 'time_series_year.png')

    figure = Figure(ylabel='Values', title='Title', xtics='month')
    figure.line(mock_data.stock_prices(days=90))
    check_figure(figure, 'time_series_month.png')

    figure = Figure(ylabel='Values', title='Title', xtics='week')
    figure.line(mock_data.stock_prices(days=60))
    check_figure(figure, 'time_series_week.png')

    figure = Figure(ylabel='Values', title='Title', xtics='day')
    figure.line(mock_data.stock_prices(days=30))
    check_figure(figure, 'time_series_day.png')


def test_log_plot(check_figure: CheckFigure) -> None:
    figure = Figure(xscale='log', yscale='log')
    figure.scatter([1e0, 1e1, 1e2, 1e3, 1e4], [1e-2, 1e-1, 1e0, 1e1, 1e2])
    check_figure(figure, 'log_plot.png')


def test_scatter_plot(generator: Generator, check_figure: CheckFigure) -> None:
    figure = Figure()
    data = DataFrame({
        'x': generator.random(100) * 10,
        'y': generator.random(100) * 10,
        'z': 25 * [1] + 25 * [2] + 25 * [3] + 25 * [4],
    })
    figure.scatter(data.groupby('z'), cmap='viridis')
    check_figure(figure, 'scatter_plot.png')


def test_scatter_plot_colors(generator: Generator, check_figure: CheckFigure) -> None:
    figure = Figure()
    figure.scatter(
        x=generator.random(100) * 10,
        y=generator.random(100) * 10,
        c=generator.random(100) * 100,
    )
    check_figure(figure, 'scatter_plot_colors.png')


def test_stacked_bar(check_figure: CheckFigure) -> None:
    data = DataFrame(
        index=[1, 2, 3, 1, 3, 5],
        data={'y': [1, 1, 1, 1, 3, 2], 'group': ['a', 'a', 'a', 'b', 'b', 'c']},
    )
    figure = Figure(xlabel='Sets', ylabel='Values', title='Title')
    figure.bar(data.groupby('group'))
    check_figure(figure, 'stacked_bar.png')


def test_stacked_bar_errors() -> None:
    with raises(ValueError, match='negative y'):
        Figure().bar(DataFrame(index=[1], data={'y': [-1], 'group': ['a']}).groupby('group'))


def test_kde(check_figure: CheckFigure) -> None:
    figure = Figure(xlabel='Values')
    figure.kde(Series([-10, 0, 5, 5, 6, 10]), bw_method='silverman')
    check_figure(figure, 'kde.png')


def test_colors(check_figure: CheckFigure) -> None:
    x_data = [1, 2, 3, 4, 5]
    y_data = [2, 3, 5, 2, 3]

    for scheme in ['light', 'dark']:
        with pyplot.style.context(f'mindlab-{scheme}'):
            figure = Figure(
                title=f'MindLab Matplotlib Colors ({scheme.title()})',
                xlim=(0.8, 5.8), ylim=(0.5, 13.5), legend='center right',
            )
            for color in range(0, 10):
                figure.plot(x_data, [15 - value - color for value in y_data], label=f'C{color}')
            check_figure(figure, f'colors_{scheme}.png')
