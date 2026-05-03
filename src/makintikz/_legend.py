import warnings

import numpy as np
from matplotlib.backends import backend_agg
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.patches import Patch

from . import _color as mycol
from . import _path as mypath
from ._tikzdata import TikzData
from ._util import _common_texification


def draw_legend(data: TikzData, obj: Legend) -> None:
    """Adds legend code."""
    texts = []
    children_alignment = []
    for text in obj.texts:
        texts.append(f"{text.get_text()}")
        children_alignment.append(f"{text.get_horizontalalignment()}")

    legend_style = build_legend_style(data, obj)

    # Get the horizontal alignment
    try:
        alignment = children_alignment[0]
    except IndexError:
        alignment = None

    for child_alignment in children_alignment:
        if alignment != child_alignment:
            warnings.warn(
                "Varying horizontal alignments in the legend. Using default.", stacklevel=2
            )
            alignment = None
            break

    if alignment:
        data.current_axis_options.add(f"legend cell align={{{alignment}}}")

    try:
        ncols = obj._ncols  # type: ignore[attr-defined]  # noqa: SLF001
    except AttributeError:
        # backwards-compatibility with matplotlib < 3.6.0
        ncols = obj._ncol  # type: ignore[attr-defined]  # noqa: SLF001
    if ncols != 1:
        data.current_axis_options.add(f"legend columns={ncols}")


    # Write styles to data
    if legend_style:
        max_length = 80
        j0, j1, j2 = (
            ("", ", ", "")
            if sum(len(s) for s in legend_style) < max_length
            else ("\n  ", ",\n  ", "\n")
        )
        string = j1.join(legend_style)
        style = f"legend style={{{j0}{string}{j2}}}"
        data.current_axis_options.add(style)


def build_legend_style(data: TikzData, obj: Legend) -> list[str]:
    legend_style = [
        "draw opacity=1",
        "text opacity=1",
    ]

    frame_on = obj.get_frame_on()
    if frame_on:
        alpha = obj.get_frame().get_alpha()
        if alpha is not None:
            legend_style.insert(0, f"fill opacity={alpha}")
    else:
        legend_style.append("fill opacity=0, fill=none")

    _legend_position_anchor(data, obj, legend_style)
    _legend_edgecolor(data, obj, legend_style)
    _legend_facecolor(data, obj, legend_style)
    return legend_style


def _legend_position_anchor(data: TikzData, obj: Legend, legend_style: list[str]) -> None:
    # Get the location.
    # http://matplotlib.org/api/legend_api.html
    loc = obj._loc if obj._loc != 0 else _get_location_from_best(obj)  # type: ignore[attr-defined]  # noqa: SLF001
    pad = 0.03
    num_of_coordinates = 2  # x and y
    # Handle loc=(x, y) tuple: coordinates for lower-left corner of legend in axes coords
    if isinstance(loc, (tuple, list)) and len(loc) == num_of_coordinates:
        try:
            x, y = float(loc[0]), float(loc[1])
            position, anchor = ([x, y], "south west")
        except (TypeError, ValueError):
            position, anchor = (None, None)
    else:
        position, anchor = {
            1: (None, None),  # upper right
            2: ([pad, 1.0 - pad], "north west"),  # upper left
            3: ([pad, pad], "south west"),  # lower left
            4: ([1.0 - pad, pad], "south east"),  # lower right
            5: ([1.0 - pad, 0.5], "east"),  # right
            6: ([3 * pad, 0.5], "west"),  # center left
            7: ([1.0 - 3 * pad, 0.5], "east"),  # center right
            8: ([0.5, 3 * pad], "south"),  # lower center
            9: ([0.5, 1.0 - 3 * pad], "north"),  # upper center
            10: ([0.5, 0.5], "center"),  # center
        }[loc]

    # In case of given position via bbox_to_anchor parameter the center
    # of legend is changed as follows:
    if obj._bbox_to_anchor:  # type: ignore[attr-defined]  # noqa: SLF001
        bbox_center = obj.get_bbox_to_anchor()._bbox._points[1]  # type: ignore[attr-defined]  # noqa: SLF001
        position = [bbox_center[0], bbox_center[1]]

    if position:
        ff = data.float_format
        legend_style.append(f"at={{({position[0]:{ff}},{position[1]:{ff}})}}")
    if anchor:
        legend_style.append(f"anchor={anchor}")


def _get_location_from_best(obj: Legend) -> int:
    # Create a renderer
    figure = obj.figure
    if not isinstance(figure, Figure):
        raise TypeError
    renderer = backend_agg.RendererAgg(
        width=figure.get_figwidth(),
        height=figure.get_figheight(),
        dpi=figure.dpi,
    )

    # Rectangles of the legend and of the axes
    # Lower left and upper right points
    x0_legend, x1_legend = obj._legend_box.get_window_extent(renderer).get_points()  # type: ignore[attr-defined]  # noqa: SLF001
    x0_axes, x1_axes = obj.axes.get_window_extent(renderer).get_points()
    dimension_legend = x1_legend - x0_legend
    dimension_axes = x1_axes - x0_axes

    # To determine the actual position of the legend, check which corner
    # (or center) of the legend is closest to the corresponding corner
    # (or center) of the axes box.
    # 1. Key points of the legend
    lower_left_legend = x0_legend
    lower_right_legend = np.array([x1_legend[0], x0_legend[1]], dtype=np.float64)
    upper_left_legend = np.array([x0_legend[0], x1_legend[1]], dtype=np.float64)
    upper_right_legend = x1_legend
    center_legend = x0_legend + dimension_legend / 2.0
    center_left_legend = np.array(
        [x0_legend[0], x0_legend[1] + dimension_legend[1] / 2.0], dtype=np.float64
    )
    center_right_legend = np.array(
        [x1_legend[0], x0_legend[1] + dimension_legend[1] / 2.0], dtype=np.float64
    )
    lower_center_legend = np.array(
        [x0_legend[0] + dimension_legend[0] / 2.0, x0_legend[1]], dtype=np.float64
    )
    upper_center_legend = np.array(
        [x0_legend[0] + dimension_legend[0] / 2.0, x1_legend[1]], dtype=np.float64
    )

    # 2. Key points of the axes
    lower_left_axes = x0_axes
    lower_right_axes = np.array([x1_axes[0], x0_axes[1]], dtype=np.float64)
    upper_left_axes = np.array([x0_axes[0], x1_axes[1]], dtype=np.float64)
    upper_right_axes = x1_axes
    center_axes = x0_axes + dimension_axes / 2.0
    center_left_axes = np.array(
        [x0_axes[0], x0_axes[1] + dimension_axes[1] / 2.0], dtype=np.float64
    )
    center_right_axes = np.array(
        [x1_axes[0], x0_axes[1] + dimension_axes[1] / 2.0], dtype=np.float64
    )
    lower_center_axes = np.array(
        [x0_axes[0] + dimension_axes[0] / 2.0, x0_axes[1]], dtype=np.float64
    )
    upper_center_axes = np.array(
        [x0_axes[0] + dimension_axes[0] / 2.0, x1_axes[1]], dtype=np.float64
    )

    # 3. Compute the distances between comparable points.
    distances = {
        1: upper_right_axes - upper_right_legend,  # upper right
        2: upper_left_axes - upper_left_legend,  # upper left
        3: lower_left_axes - lower_left_legend,  # lower left
        4: lower_right_axes - lower_right_legend,  # lower right
        # 5:, Not Implemented  # right
        6: center_left_axes - center_left_legend,  # center left
        7: center_right_axes - center_right_legend,  # center right
        8: lower_center_axes - lower_center_legend,  # lower center
        9: upper_center_axes - upper_center_legend,  # upper center
        10: center_axes - center_legend,  # center
    }
    for k, v in distances.items():
        distances[k] = np.linalg.norm(v, ord=2)

    # 4. Take the shortest distance between key points as the final
    # location
    return min(distances, key=lambda k: distances[k])


def _legend_edgecolor(data: TikzData, obj: Legend, legend_style: list[str]) -> None:
    if obj.get_frame_on():
        edgecolor = obj.get_frame().get_edgecolor()
        frame_xcolor, _ = mycol.mpl_color2xcolor(data, edgecolor)
        if frame_xcolor != "black":  # black is default
            legend_style.append(f"draw={frame_xcolor}")
    else:
        legend_style.append("draw=none")


def _legend_facecolor(data: TikzData, obj: Legend, legend_style: list[str]) -> None:
    facecolor = obj.get_frame().get_facecolor()
    fill_xcolor, _ = mycol.mpl_color2xcolor(data, facecolor)
    if fill_xcolor != "white":  # white is default
        legend_style.append(f"fill={fill_xcolor}")
