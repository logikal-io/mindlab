import filecmp
import shutil
from collections.abc import Iterable
from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import IO, Any

import matplotlib
from matplotlib import artist, colormaps, colors, dates, pyplot, ticker
from matplotlib.collections import PathCollection
from matplotlib.legend_handler import HandlerPathCollection
from pandas import DataFrame, Series
from pandas.core.groupby.generic import DataFrameGroupBy
from xdg_base_dirs import xdg_data_home

from mindlab.utils import get_config


def copy_folder(source_dir: Path, target_dir: Path) -> list[Path]:
    """
    Copy a given source directory to a target directory and return the paths of the copied files.
    """
    target_files: list[Path] = []
    for source_file in source_dir.glob('*'):
        target_file = target_dir / source_file.name
        target_files.append(target_file)
        if not target_file.exists() or not filecmp.cmp(source_file, target_file):
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source_file, target_file)
    return target_files


def use_mindlab_styles(
    font_install_path: Path | None = None,
    apply_mindlab_styles: bool = True,
    project_styles: bool | Iterable[str] | None = None,
) -> bool:
    """
    Install and use MindLab and project styles.

    Args:
        font_install_path: The path to install the style fonts to.
            Defaults to ``$XDG_DATA_HOME/fonts``.
        apply_mindlab_styles: Whether to use the MindLab styles.
            Defaults to ``tool.mindlab.apply_mindlab_styles`` in ``pyproject.toml`` or
            ``$MINDLAB_APPLY_MINDLAB_STYLES``.
        project_styles: The project styles to use in addition to the MindLab style.
            Defaults to ``tool.mindlab.styles`` in ``pyproject.toml`` or ``$MINDLAB_STYLES``.

    Returns:
        :data:`True` if the styles were applied and :data:`False` otherwise.

    """
    if not get_config('apply_mindlab_styles', apply_mindlab_styles):
        return False

    # Installing fonts and styles
    font_files = copy_folder(
        source_dir=Path(__file__).parent / 'fonts',
        target_dir=font_install_path or xdg_data_home() / 'fonts',
    )

    # Refreshing font cache if necessary
    font_manager = matplotlib.font_manager.fontManager
    font_library = set(font.fname for font in font_manager.ttflist)
    for font_file in font_files:
        if font_file.suffix == '.ttf' and str(font_file.resolve()) not in font_library:
            font_manager.addfont(str(font_file))

    # Applying styles
    matplotlib.style.use([
        'mindlab.styles.mindlab',
        'mindlab.styles.mindlab_light',
        *get_config('styles', project_styles, value_type=list)
    ])
    return True


# Import-time side effects are bad, but we must do it to reliably modify Matplotlib global state
use_mindlab_styles()


class Figure:
    def __init__(  # pylint: disable=too-many-arguments, too-complex
        self,
        *,
        size: tuple[float, float] | None = None,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
        xtics: str | None = None,
        ytics: str | None = None,
        xscale: str | None = None,
        yscale: str | None = None,
        xlim: tuple[float | None, float | None] | None = None,
        ylim: tuple[float | None, float | None] | None = None,
        legend: str | None = 'best',
    ):
        """
        Create professional plots easily.

        Note that in addition to the overwritten methods described below, a Figure instance also
        exposes all the same methods as the underlying :class:`matplotlib.axes.Axes` instance.

        Args:
            size: The size of the figure (in inches).
            title: The title of the figure.
            xlabel: The x axis label of the figure.
            ylabel: The y axis label of the figure.
            xtics: The x tick locators (one of ``eng``, ``auto``, ``log``, ``percent``, ``year``,
                ``month``, ``week`` or ``day``). Defaults to ``eng`` in ``linear`` scale and
                ``log`` in ``log`` scale.
            ytics: The y tick locators (same choices as for xtics).
            xscale: The scale of the x axis (one of ``linear`` or ``log``).
            yscale: The scale of the y axis (same choices as for xscale).
            xlim: The x axis limits.
            ylim: The y axis limits.
            legend: The location of the legend (either ``best``, or a combination of
                ``top``/``center``/``bottom`` and ``left``/``center``/``right``.

        Attributes:
            figure (matplotlib.figure.Figure): The underlying figure instance.
            axes (matplotlib.axes.Axes): The underlying axes instance.

        """
        xtics = xtics or ('log' if xscale else 'eng')
        ytics = ytics or ('log' if yscale else 'eng')
        self.figure, self.axes = pyplot.subplots(figsize=size)
        if title:
            self.axes.set_title(title)
        if xlabel:
            self.axes.set_xlabel(xlabel)
        if ylabel:
            self.axes.set_ylabel(ylabel)
        if xscale:
            self.axes.set_xscale(xscale)
        if yscale:
            self.axes.set_yscale(yscale)
        if xtics:
            self._set_tics(which='x', tics=xtics)
        if ytics:
            self._set_tics(which='y', tics=ytics)
        if xlim:
            self.axes.set_xlim(*xlim)
        if ylim:
            self.axes.set_ylim(*ylim)
        if legend:
            self._legend_location = legend.replace('top', 'upper').replace('bottom', 'lower')
            self.figure.canvas.mpl_connect('draw_event', self._add_legend)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.axes, name)  # default to the axes interface

    def as_bytes(self) -> bytes:
        output = BytesIO()
        self.save(output, format='png')
        return output.getvalue()

    def save(self, output: str | PathLike[Any] | IO[Any], **kwargs: Any) -> None:
        """
        Save the figure.

        Args:
            output: A path or object to use for saving.
            **kwargs: Arguments to forward to :meth:`matplotlib.figure.Figure.savefig`.

        """
        self.figure.savefig(output, **kwargs)

    def line(self, *args: Any, **kwargs: Any) -> None:
        """
        Draw a line chart.

        Args:
            *args: Arguments to forward to :meth:`matplotlib.axes.Axes.plot`.
                If the first argument is a grouped data frame (see :doc:`GroupBy
                <pandas:reference/groupby>`) we draw a line for each group.
            **kwargs: Arguments to forward to :meth:`matplotlib.axes.Axes.plot`.

        """
        if args and isinstance(args[0], DataFrameGroupBy):
            for group in args[0].groups:
                group_data = args[0].get_group(group)
                self.line(group_data[group_data.columns[0]], label=group, **kwargs)
        else:
            kwargs.setdefault('marker', '')
            self.axes.plot(*args, **kwargs)

    def scatter(self, *args: Any, **kwargs: Any) -> None:
        """
        Draw a scatter plot.

        Args:
            *args: Arguments to forward to :meth:`matplotlib.axes.Axes.scatter`.
                If the first argument is a grouped data frame (see :doc:`GroupBy
                <pandas:reference/groupby>`) we draw a scatter plot for each group.
            **kwargs: Arguments to forward to :meth:`matplotlib.axes.Axes.scatter`.

        """
        color_values = kwargs.pop('c', None)
        cmap = kwargs.pop('cmap', None)

        # Apply colors to facecolor
        if color_values is not None and not isinstance(color_values, str):
            normalize = colors.Normalize()
            kwargs['facecolor'] = pyplot.get_cmap(cmap)(normalize(color_values))

        # Draw plot
        if args and isinstance(args[0], DataFrameGroupBy):
            groups: dict[Any, Any] = args[0].groups
            if cmap:
                normalized = colors.Normalize(min(groups.keys()), max(groups.keys()))
            for group in groups:
                if cmap:
                    kwargs['color'] = colormaps[cmap](normalized(group))
                group_data = args[0].get_group(group)
                self.axes.scatter(
                    x=group_data[group_data.columns[0]],
                    y=group_data[group_data.columns[1]],
                    label=group, **kwargs,
                )
        else:
            self.axes.scatter(*args, **kwargs)

        # Draw colorbar
        if color_values is not None:
            with pyplot.rc_context({'axes.grid': False}):
                mappable = matplotlib.cm.ScalarMappable(norm=normalize, cmap=cmap)
                mappable.set_array(color_values)
                colorbar = self.figure.colorbar(mappable=mappable, ax=self.axes)
                colorbar.ax.minorticks_off()

    def bar(self, data: DataFrameGroupBy, **kwargs: Any) -> None:  # type: ignore[type-arg]
        """
        Draw a stacked bar chart.

        Args:
            data: The grouped data frame to plot (see :doc:`GroupBy <pandas:reference/groupby>`).
            **kwargs: Arguments to forward to :meth:`matplotlib.axes.Axes.bar`.

        """
        y_column = str(data.first().columns[0])
        if (data[y_column].min() < 0).any():
            raise ValueError('You cannot have negative y values in a stacked bar chart')

        bottom = DataFrame(columns=[y_column])
        for group in data.groups:
            group_data = data.get_group(group)
            self.axes.bar(
                x=group_data.index, height=group_data[y_column],
                bottom=bottom.reindex(group_data.index, fill_value=0)[y_column],
                label=group, **kwargs,
            )
            bottom = bottom.add(group_data[[y_column]], fill_value=0)

    def kde(
        self,
        series: Series,  # type: ignore[type-arg]
        rug: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Draw a kernel density estimation plot.

        Args:
            series: The series for which to calculate the kernel density estimate.
            rug: Whether to add a rug plot.
            **kwargs: Arguments to forward to :meth:`pandas.Series.plot`.

        """
        kwargs.setdefault('label', None)
        self._set_tics(which='y', tics='auto')
        series.plot(kind='density', ax=self.axes, marker='', **kwargs)
        if rug:
            self.axes.plot(series, [0] * len(series), '|', color=kwargs.get('color', 'black'))

    def _set_tics(self, which: str, tics: str) -> None:
        axis = getattr(self.axes, f'get_{which}axis')()

        if tics == 'eng':
            axis.set_major_formatter(ticker.EngFormatter(sep=''))
        elif tics == 'auto':
            axis.set_major_formatter(ticker.ScalarFormatter())
        elif tics == 'log':
            axis.set_major_formatter(LogFormatter())
        elif tics == 'year':
            axis.set_major_formatter(dates.DateFormatter('%Y'))
            axis.set_major_locator(dates.YearLocator())
            axis.set_minor_locator(dates.MonthLocator())
        elif tics == 'month':
            axis.set_major_formatter(dates.DateFormatter('%b %Y'))
            axis.set_major_locator(dates.MonthLocator())
            axis.set_minor_locator(dates.WeekdayLocator(byweekday=dates.MONDAY))
        elif tics == 'week':
            axis.set_major_formatter(dates.DateFormatter('W%-V %G'))
            axis.set_major_locator(dates.WeekdayLocator(byweekday=dates.MONDAY))
            axis.set_minor_locator(dates.DayLocator())
        elif tics == 'day':
            axis.set_major_formatter(dates.DateFormatter('%b %-d, %Y'))
            axis.set_major_locator(dates.WeekdayLocator(byweekday=dates.MONDAY))
            axis.set_minor_locator(dates.DayLocator())
        else:
            raise ValueError(f'Invalid tics setting "{tics}"')

        if tics in {'year', 'month', 'week', 'day'} and which == 'x':
            # Unfortunately axis.set_tick_params does not allow us to set the rotation mode and the
            # horizontal alignment (see https://github.com/matplotlib/matplotlib/issues/13774), so
            # we must use a draw event callback instead.
            self._rotate_x_tick_labels_callback = self.figure.canvas.mpl_connect(
                'draw_event', self._rotate_x_tick_labels,
            )

    @staticmethod
    def _make_handle_opaque(legend_handle: artist.Artist, orig_handle: artist.Artist) -> None:
        legend_handle.update_from(orig_handle)
        legend_handle.set_alpha(1)

    def _add_legend(self, *_args: Any, **_kwargs: Any) -> None:
        handles, labels = self.axes.get_legend_handles_labels()
        if handles and labels and not all(not bool(label) or label == 'None' for label in labels):
            self.axes.legend(handles, labels, loc=self._legend_location, handler_map={
                PathCollection: HandlerPathCollection(update_func=self._make_handle_opaque),
            })

    def _rotate_x_tick_labels(self, *_args: Any, **_kwargs: Any) -> None:
        for label in self.axes.get_xticklabels():
            label.set_horizontalalignment('right')
            label.set_rotation_mode('anchor')
            label.set_rotation(30)

        self.figure.canvas.mpl_disconnect(self._rotate_x_tick_labels_callback)
        self.figure.canvas.draw()


class LogFormatter(ticker.LogFormatterSciNotation):
    def __call__(self, x: Any, pos: Any = None) -> str:
        value = super().__call__(x, pos=pos)
        overrides = {r'$\mathdefault{10^{0}}$': '1'}
        return overrides.get(value, value)
