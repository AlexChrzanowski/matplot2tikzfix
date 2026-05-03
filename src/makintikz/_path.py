from __future__ import annotations

import contextlib
from collections.abc import Iterable, Sequence, Sized
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from matplotlib.dates import DateConverter, num2date
from matplotlib.lines import Line2D, _get_dash_pattern  # type: ignore[attr-defined]
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Circle, Ellipse, Rectangle
from matplotlib.path import Path

if TYPE_CHECKING:
    from matplotlib.collections import Collection, PathCollection
    from matplotlib.patches import Patch

    from ._tikzdata import TikzData

from . import _color, _files
from ._axes import _mpl_cmap2pgf_cmap
from ._hatches import _mpl_hatch2pgfp_pattern
from ._markers import _mpl_marker2pgfp_marker
from ._util import _common_texification, get_legend_text, has_legend


@dataclass
class LineData:
    obj: Collection | Patch
    ec: str | tuple | None = None  # edgecolor
    ec_name: str | None = None
    ec_rgba: np.ndarray | None = None
    fc: str | tuple | None = None  # facecolor
    fc_name: str | None = None
    fc_rgba: np.ndarray | None = None
    ls: str | tuple[float, Sequence[float] | None] | None = None  # linestyle
    lw: float | None = None  # linewidth
    hatch: str | None = None


@dataclass
class PathCollectionData:
    obj: PathCollection
    dd_strings: np.ndarray
    draw_options: list
    labels: list
    table_options: list
    is_contour: bool
    marker: str | None = None
    is_filled: bool = False
    add_individual_color_code: bool | None = False
    legend_text: str | None = None


def draw_path(
    data: TikzData,
    path: Path,
    draw_options: list[str] | None = None,
    *,
    simplify: bool | None = None,
) -> tuple[str, bool]:
    """Adds code for drawing an ordinary path in PGFPlots (TikZ)."""
    # For some reasons, matplotlib sometimes adds void paths which consist of
    # only one point and have 0 fill opacity. To not let those clutter the
    # output TeX file, bail out here.
    if not isinstance(path.vertices, np.ndarray) or (
        len(path.vertices) == 2  # noqa: PLR2004
        and np.all(path.vertices[0] == path.vertices[1])
        and draw_options is not None
        and "fill opacity=0" in draw_options
    ):
        return "", False

    x_is_date = _check_x_is_date(data)

    nodes = []
    ff = data.float_format
    xformat = "" if x_is_date else ff
    prev = None
    is_area = False
    for vert, code in path.iter_segments(simplify=simplify):
        # For path codes see: http://matplotlib.org/api/path_api.html
        is_area = False
        if code == Path.MOVETO:
            nodes.append(
                f"(axis cs:{vert[0] if not x_is_date else num2date(vert[0]):{xformat}},"
                f"{vert[1]:{ff}})"
            )
        elif code == Path.LINETO:
            nodes.append(
                f"--(axis cs:{vert[0] if not x_is_date else num2date(vert[0]):{xformat}},"
                f"{vert[1]:{ff}})"
            )
        elif code == Path.CURVE3:
            # Quadratic Bezier curves aren't natively supported in TikZ, but
            # can be emulated as cubic Beziers.
            # From
            # http://www.latex-community.org/forum/viewtopic.php?t=4424&f=45:
            # If you really need a quadratic Bézier curve on the points P0, P1
            # and P2, then a process called 'degree elevation' yields the cubic
            # control points (Q0, Q1, Q2 and Q3) as follows:
            #   CODE: SELECT ALL
            #   Q0 = P0                         # noqa: ERA001
            #   Q1 = 1/3 P0 + 2/3 P1
            #   Q2 = 2/3 P1 + 1/3 P2
            #   Q3 = P2                         # noqa: ERA001
            #
            # P0 is the point of the previous step which is needed to compute
            # Q1.
            if prev is None:
                msg = "Cannot draw quadratic Bezier curves as the beginning of a path"
                raise ValueError(msg)
            q1 = list(1.0 / 3.0 * prev + 2.0 / 3.0 * vert[0:2])
            q2 = list(2.0 / 3.0 * vert[0:2] + 1.0 / 3.0 * vert[2:4])
            q3 = list(vert[2:4])
            if x_is_date:
                q1 = [num2date(q1[0]), q1[1]]
                q2 = [num2date(q2[0]), q2[1]]
                q3 = [num2date(q3[0]), q3[1]]
            nodes.append(
                ".. controls "
                f"(axis cs:{q1[0]:{xformat}},{q1[1]:{ff}}) and "
                f"(axis cs:{q2[0]:{xformat}},{q2[1]:{ff}}) .. "
                f"(axis cs:{q3[0]:{xformat}},{q3[1]:{ff}})"
            )
        elif code == Path.CURVE4:
            # Cubic Bezier curves.
            nodes.append(
                ".. controls "
                f"(axis cs:{vert[0] if not x_is_date else num2date(vert[0]):{xformat}},"
                f"{vert[1]:{ff}}) and "
                f"(axis cs:{vert[2] if not x_is_date else num2date(vert[2]):{xformat}},"
                f"{vert[3]:{ff}}) .. "
                f"(axis cs:{vert[4] if not x_is_date else num2date(vert[4]):{xformat}},"
                f"{vert[5]:{ff}})"
            )
        else:
            nodes.append("--cycle")
            is_area = True

        # Store the previous point for quadratic Beziers.
        prev = vert[0:2]

    do = "[{}]".format(", ".join(draw_options)) if draw_options else ""
    path_command = "\\path {}\n{};\n".format(do, "\n".join(nodes))

    return path_command, is_area


def _clip_circle(clip_path: Circle, ff: str) -> str:
    """Generate TikZ clip command for Circle patch."""
    x, y = clip_path.center
    radius = clip_path.get_radius()
    return f"\\clip (axis cs:{x:{ff}},{y:{ff}}) circle ({radius:{ff}});\n"


def _clip_rectangle(clip_path: Rectangle, ff: str) -> str:
    """Generate TikZ clip command for Rectangle patch."""
    x1 = clip_path.get_x()
    y1 = clip_path.get_y()
    x2 = x1 + clip_path.get_width()
    y2 = y1 + clip_path.get_height()
    return f"\\clip (axis cs:{x1:{ff}},{y1:{ff}}) rectangle (axis cs:{x2:{ff}},{y2:{ff}});\n"


def _clip_ellipse(clip_path: Ellipse, ff: str) -> str:
    """Generate TikZ clip command for Ellipse patch."""
    x, y = clip_path.center
    rx = 0.5 * clip_path.width
    ry = 0.5 * clip_path.height

    if clip_path.angle != 0:
        return (
            f"\\clip[rotate around={{{clip_path.angle:{ff}}:(axis cs:{x:{ff}},{y:{ff}})}}] "
            f"(axis cs:{x:{ff}},{y:{ff}}) ellipse ({rx:{ff}} and {ry:{ff}});\n"
        )
    return f"\\clip (axis cs:{x:{ff}},{y:{ff}}) ellipse ({rx:{ff}} and {ry:{ff}});\n"


def _clip_path(data: TikzData, path: Path) -> str:
    """Generate TikZ clip command for generic Path object."""
    ff = data.float_format
    x_is_date = _check_x_is_date(data)
    xformat = "" if x_is_date else ff
    nodes = []

    for vert, code in path.iter_segments(simplify=False):
        if code == Path.MOVETO:
            nodes.append(
                f"(axis cs:{vert[0] if not x_is_date else num2date(vert[0]):{xformat}},"
                f"{vert[1]:{ff}})"
            )
        elif code == Path.LINETO:
            nodes.append(
                f"--(axis cs:{vert[0] if not x_is_date else num2date(vert[0]):{xformat}},"
                f"{vert[1]:{ff}})"
            )
        elif code == Path.CLOSEPOLY:
            nodes.append("--cycle")

    # Ensure the path is closed
    if nodes and nodes[-1] != "--cycle":
        nodes.append("--cycle")

    return f"\\clip {' '.join(nodes)};\n" if nodes else ""


def convert_clip_path(
    data: TikzData,
    clip_path: Path | Patch,
) -> str:
    r"""Convert a matplotlib clip path (Patch or Path) to TikZ \clip command.

    Args:
        data: TikzData object containing formatting information
        clip_path: The matplotlib Path or Patch object to use as clip path

    Returns:
        TikZ clip command string (e.g., r"\clip (axis cs:0,0) circle (1);\n")
    """
    ff = data.float_format

    # Handle Circle patches
    if isinstance(clip_path, Circle):
        return _clip_circle(clip_path, ff)

    # Handle Rectangle patches
    if isinstance(clip_path, Rectangle):
        return _clip_rectangle(clip_path, ff)

    # Handle Ellipse patches (but not Circle, which is already handled above)
    if isinstance(clip_path, Ellipse):
        return _clip_ellipse(clip_path, ff)

    # Handle generic Path objects or Patch with get_path()
    if isinstance(clip_path, Path):
        path = clip_path
    elif hasattr(clip_path, "get_path"):
        path = clip_path.get_path()
        if hasattr(clip_path, "get_patch_transform"):
            path = path.transformed(clip_path.get_patch_transform())
    else:
        return ""

    return _clip_path(data, path)


def _check_x_is_date(data: TikzData) -> bool:
    if data.current_mpl_axes is None:
        # This shouldn't be the case
        msg = "No axes defined."
        raise ValueError(msg)

    try:
        converter = data.current_mpl_axes.xaxis.get_converter()  # type: ignore[attr-defined]
    except AttributeError:
        converter = data.current_mpl_axes.xaxis.converter
    return isinstance(converter, DateConverter)


_D2 = 2
_ZERO2 = np.array([0.0, 0.0], dtype=float)


# FIX #594: len(dd)==1 is true for
# 1-point scatter too.
# Only treat as contour if the
# single offset is a dummy near (0,0).
def _is_contour_like_offsets(dd: object) -> bool:
    """Contours often show up as a PathCollection with a single dummy offset near (0, 0)."""
    if not isinstance(dd, Sized) or len(dd) != 1:
        return False
    try:
        offsets = np.asarray(dd, dtype=float)
    except (TypeError, ValueError):
        return False

    if offsets.ndim != _D2 or offsets.shape[1] < _D2:
        return False

    return np.allclose(offsets[0, :_D2], _ZERO2, atol=1e-12, rtol=0.0)


def draw_pathcollection(data: TikzData, obj: PathCollection) -> list[str]:
    """Returns PGFPlots code for a number of patch objects."""
    content = []
    # gather data
    dd = obj.get_offsets()
    if not isinstance(dd, Iterable):
        # No idea what to draw.
        return []

    is_contour = _is_contour_like_offsets(dd)
    path_collection_data = PathCollectionData(
        obj=obj,
        dd_strings=np.array(
            [
                [f"{val:{data.float_format}}" for val in row]  # type: ignore[str-bytes-safe]
                for row in dd
                if isinstance(row, Iterable)
            ]
        ),
        draw_options=["only marks"],
        labels=["x", "y"],
        table_options=[],
        is_contour=is_contour,  # use the correct is_contour
    )
    line_data = LineData(obj=obj)

    if obj.get_array() is not None:
        _draw_pathcollection_scatter_colormap(data, path_collection_data)
    else:
        # gather the draw options
        _draw_pathcollection_get_edgecolors(data, path_collection_data, line_data)
        _draw_pathcollection_get_facecolors(data, path_collection_data, line_data)
        with contextlib.suppress(TypeError, IndexError):
            line_style = obj.get_linestyle()[0]
            if isinstance(line_style, (str, tuple)):  # Mypy thinks it can also be a float?
                line_data.ls = line_style
        _draw_pathcollection_add_individual_color(path_collection_data)
        _draw_pathcollection_get_marker(path_collection_data)

    _draw_pathcollection_drawoptions(data, path_collection_data, line_data)

    # For contours, iterate the actual contour paths and let the contour helper
    # replace the point table. For scatter markers, emit exactly one plot using
    # offsets and avoid treating marker geometry as contour paths.
    paths = obj.get_paths() if path_collection_data.is_contour else [None]

    for path in paths:
        if path is not None:
            _draw_pathcollection_draw_contour(path, data, path_collection_data)
        _draw_pathcollection_scatter_sizes(data, path_collection_data)
        # remove duplicates
        draw_options = sorted(set(path_collection_data.draw_options))

        max_row_length = 80
        len_row = sum(len(item) for item in draw_options)
        j0, j1, j2 = ("", ", ", "") if len_row < max_row_length else ("\n  ", ",\n  ", "\n")
        do = f" [{j0}{{}}{j2}]".format(j1.join(draw_options)) if draw_options else ""
        content.append(f"\\addplot{do}\n")

        if data.externals_search_path is not None:
            esp = data.externals_search_path
            path_collection_data.table_options.append(f"search path={{{esp}}}")

        if len(path_collection_data.table_options) > 0:
            table_options_str = ", ".join(path_collection_data.table_options)
            content.append(f"table [{table_options_str}]{{")
        else:
            content.append("table{")

        # linter fix, reducing statements

        plot_table = [
            "  ".join(path_collection_data.labels) + "\n",
            *(" ".join(row) + "\n" for row in path_collection_data.dd_strings),
        ]

        if data.externalize_tables:
            filepath, rel_filepath = _files.new_filepath(data, "table", ".dat")
            with filepath.open("w") as f:
                # No encoding handling required: plot_table is only ASCII
                f.write("".join(plot_table))
            content.append(str(rel_filepath))
        else:
            content.append("%\n")
            content.extend(plot_table)

        content.append("};\n")

    if path_collection_data.legend_text is not None:
        content.append(
            f"\\addlegendentry{{{_common_texification(path_collection_data.legend_text)}}}\n"
        )

    return content


def _draw_pathcollection_scatter_colormap(data: TikzData, pcd: PathCollectionData) -> None:
    obj_array = pcd.obj.get_array()
    if obj_array is not None:
        # clean_figure() can cause a mismatch in color array len, so check and truncate as needed
        if len(obj_array) != len(pcd.dd_strings):
            obj_array = obj_array[: len(pcd.dd_strings)]

        pcd.dd_strings = np.column_stack([pcd.dd_strings, obj_array])
    pcd.labels.append("colordata")
    pcd.draw_options.append("scatter src=explicit")
    pcd.table_options.extend(["x=x", "y=y", "meta=colordata"])
    if pcd.obj.get_cmap():
        mycolormap, is_custom_cmap = _mpl_cmap2pgf_cmap(pcd.obj.get_cmap(), data)
        pcd.draw_options.append("scatter")
        pcd.draw_options.append("colormap" + ("=" if is_custom_cmap else "/") + mycolormap)
        sizes_will_vary = len(pcd.obj.get_sizes()) == len(pcd.dd_strings)
        if not sizes_will_vary:
            edgecolors = pcd.obj.get_edgecolors()  # type: ignore[attr-defined]
            if len(edgecolors) == 1 and edgecolors[0][3] > 0:
                ec_name, _ = _color.mpl_color2xcolor(data, edgecolors[0])
                pcd.draw_options.append(
                    f"scatter/use mapped color={{draw={ec_name},fill=mapped color}}"
                )
    alpha = pcd.obj.get_alpha()
    if alpha is not None and alpha < 1.0:
        pcd.draw_options.append(f"opacity={alpha:{data.float_format}}")


def _draw_pathcollection_get_edgecolors(
    data: TikzData, pcd: PathCollectionData, line_data: LineData
) -> None:
    try:
        edgecolors = pcd.obj.get_edgecolors()  # type: ignore[attr-defined]
    except TypeError:
        pass
    else:
        if len(edgecolors) == 1:
            line_data.ec = edgecolors[0]
        elif len(edgecolors) > 1:
            pcd.labels.append("draw")

            ec_strings = [
                ",".join(f"{item:{data.float_format}}" for item in row)
                for row in edgecolors[:, :3] * 255
            ]
            pcd.dd_strings = np.column_stack([pcd.dd_strings, ec_strings])
            pcd.add_individual_color_code = True


def _draw_pathcollection_get_facecolors(
    data: TikzData, pcd: PathCollectionData, line_data: LineData
) -> None:
    try:
        facecolors = pcd.obj.get_facecolors()  # type: ignore[attr-defined]
    except TypeError:
        pass
    else:
        if len(facecolors) == 1:
            line_data.fc = facecolors[0]
            pcd.is_filled = True
        elif len(facecolors) > 1:
            pcd.labels.append("fill")
            fc_strings = [
                ",".join(f"{item:{data.float_format}}" for item in row)
                for row in facecolors[:, :3] * 255
            ]
            pcd.dd_strings = np.column_stack([pcd.dd_strings, fc_strings])
            pcd.add_individual_color_code = True
            pcd.is_filled = True


def _draw_pathcollection_add_individual_color(pcd: PathCollectionData) -> None:
    if pcd.add_individual_color_code:
        pcd.draw_options.extend(
            [
                "scatter",
                "visualization depends on={value \\thisrow{draw} \\as \\drawcolor}",
                "visualization depends on={value \\thisrow{fill} \\as \\fillcolor}",
                "scatter/@pre marker code/.code={%\n"
                "  \\expanded{%\n"
                "  \\noexpand\\definecolor{thispointdrawcolor}{RGB}{\\drawcolor}%\n"
                "  \\noexpand\\definecolor{thispointfillcolor}{RGB}{\\fillcolor}%\n"
                "  }%\n"
                "  \\scope[draw=thispointdrawcolor, fill=thispointfillcolor]%\n"
                "}",
                "scatter/@post marker code/.code={%\n  \\endscope\n}",
            ]
        )


def _draw_pathcollection_get_marker(pcd: PathCollectionData) -> None:
    # "solution" from
    # <https://github.com/matplotlib/matplotlib/issues/4672#issuecomment-378702670>
    if pcd.obj.get_paths():
        p = pcd.obj.get_paths()[0]
        if not isinstance(p.codes, np.ndarray) or not isinstance(p.vertices, np.ndarray):
            return
        ms = {style: MarkerStyle(style) for style in MarkerStyle.markers}
        paths = {
            style: marker.get_path().transformed(marker.get_transform())
            for style, marker in ms.items()
        }
        tolerance = 1.0e-10
        for marker, path in paths.items():
            if not isinstance(path.codes, np.ndarray) or not isinstance(path.vertices, np.ndarray):
                continue
            if (
                np.array_equal(path.codes, p.codes)
                and (path.vertices.shape == p.vertices.shape)
                and np.max(np.abs(path.vertices - p.vertices)) < tolerance
            ):
                pcd.marker = str(marker)
                return


def _draw_pathcollection_drawoptions(
    data: TikzData, pcd: PathCollectionData, line_data: LineData
) -> None:
    if pcd.is_contour:
        pcd.draw_options = ["draw=none"]

    if pcd.marker is not None:
        pgfplots_marker, marker_options = _mpl_marker2pgfp_marker(
            data, pcd.marker, is_filled=pcd.is_filled
        )
        pcd.draw_options.append(f"mark={pgfplots_marker}")
        if marker_options:
            pcd.draw_options.append("mark options={{{}}}".format(",".join(marker_options)))

    pcd.draw_options.extend(get_draw_options(data, line_data))

    pcd.legend_text = get_legend_text(pcd.obj)
    if pcd.legend_text is None and has_legend(pcd.obj.axes):
        pcd.draw_options.append("forget plot")


def _draw_pathcollection_draw_contour(path: Path, data: TikzData, pcd: PathCollectionData) -> None:
    if pcd.is_contour:
        ff = data.float_format
        dd = path.vertices
        if not isinstance(dd, Iterable) or not isinstance(dd, Sized):
            return  # We cannot draw a path
        # https://matplotlib.org/stable/api/path_api.html
        codes = path.codes if path.codes is not None else [1] + [2] * (len(dd) - 1)
        dd_strings: list[list[str]] = []
        if not isinstance(codes, Iterable):
            return  # We cannot draw a path
        for row, code in zip(dd, codes, strict=True):
            if code == 1:  # MOVETO
                # Inserts a newline to trigger "move to" in pgfplots
                dd_strings.append([])
            if not isinstance(row, Iterable):
                raise TypeError
            dd_strings.append([f"{val:{ff}}" for val in row])  # type: ignore[str-bytes-safe]
        pcd.dd_strings = np.array(dd_strings[1:], dtype=object)


def _build_scatter_marker_code_no_colors(
    has_variable_sizes: bool,  # noqa: FBT001
    has_variable_linewidths: bool,  # noqa: FBT001
) -> str | None:
    """Build fallback scatter/@pre marker code when no uniform colors."""
    if has_variable_sizes and not has_variable_linewidths:
        return "scatter/@pre marker code/.append style={/tikz/mark size=\\perpointmarksize}"
    if has_variable_linewidths:
        size_mark_str = "\\perpointmarksize pt" if has_variable_sizes else "\\perpointmarksize"
        return (
            f"scatter/@pre marker code/.code={{%\n"
            f"  \\pgfsetlinewidth{{\\perpointlinewidth pt}}%\n"
            f"  \\pgfset{{/tikz/mark size={size_mark_str}}}%\n"
            f"}}"
        )
    return None


def _build_scatter_marker_code_with_colors(  # noqa: PLR0913
    data: TikzData,
    pcd: PathCollectionData,
    linewidths: np.ndarray,
    has_variable_sizes: bool,  # noqa: FBT001
    has_variable_linewidths: bool,  # noqa: FBT001
    n_linewidths: int,
) -> list[str] | None:
    """Build scatter/@pre/@post marker code when uniform colors are present."""
    edgecolors = pcd.obj.get_edgecolors()  # type: ignore[attr-defined]
    facecolors = pcd.obj.get_facecolors()  # type: ignore[attr-defined]
    if len(edgecolors) != 1 or len(facecolors) > 1:
        return None

    ec_name, _ = _color.mpl_color2xcolor(data, edgecolors[0])
    if len(facecolors) == 0 or facecolors[0][3] == 0:
        fc_part = "none"
    else:
        fc_part = _color.mpl_color2xcolor(data, facecolors[0])[0]

    pre_code_lines = []
    if has_variable_linewidths:
        pre_code_lines.append("  \\pgfsetlinewidth{\\perpointlinewidth pt}%\n")

    size_mark_size = "\\perpointmarksize pt" if has_variable_sizes else "\\perpointmarksize"
    scope_attrs = f"draw={ec_name}, fill={fc_part}"
    if n_linewidths == 1:  # uniform linewidth
        lw = float(linewidths[0])
        scope_attrs += f", line width={lw}pt"

    pre_code_lines.append(f"  \\scope[{scope_attrs}]%\n")
    pre_code_lines.append(f"  \\pgfset{{/tikz/mark size={size_mark_size}}}%\n")

    pre_code = "".join(pre_code_lines)
    return [
        f"scatter/@pre marker code/.code={{%\n{pre_code}}}",
        "scatter/@post marker code/.code={%\n  \\endscope\n}",
    ]


def _draw_pathcollection_scatter_sizes(data: TikzData, pcd: PathCollectionData) -> None:
    sizes = pcd.obj.get_sizes()
    linewidths = pcd.obj.get_linewidths()  # type: ignore[attr-defined]
    n_sizes = len(sizes)
    n_linewidths = len(linewidths)
    n_points = len(pcd.dd_strings)

    if n_points in (n_sizes, n_linewidths):
        # Variable sizes and/or linewidths
        size_options = ["scatter"]
        has_variable_sizes = n_sizes == n_points
        has_variable_linewidths = n_linewidths == n_points

        if has_variable_sizes:
            # In Pgfplots, \mark size specifies radii, in matplotlib circle areas.
            radii = np.sqrt(pcd.obj.get_sizes() / np.pi)
            pcd.dd_strings = np.column_stack([pcd.dd_strings, radii])
            pcd.labels.append("sizedata")
            size_options.insert(
                0, "visualization depends on=" + "{\\thisrow{sizedata} \\as\\perpointmarksize}"
            )

        if has_variable_linewidths:
            pcd.dd_strings = np.column_stack([pcd.dd_strings, linewidths])
            pcd.labels.append("lwdata")
            size_options.insert(
                0, "visualization depends on={\\thisrow{lwdata} \\as\\perpointlinewidth}"
            )

        # When scatter mode is active, top-level draw=/fill= options are ignored by pgfplots.
        # If uniform colors are present, use .code with \scope to embed alongside size/linewidth.
        if not pcd.add_individual_color_code and pcd.obj.get_array() is None:
            marker_code = _build_scatter_marker_code_with_colors(
                data,
                pcd,
                linewidths,
                has_variable_sizes,
                has_variable_linewidths,
                n_linewidths,
            )
            if marker_code is not None:
                size_options.extend(marker_code)
                pcd.draw_options.extend(size_options)
                return

        pcd.draw_options.extend(size_options)
        fallback_code = _build_scatter_marker_code_no_colors(
            has_variable_sizes, has_variable_linewidths
        )
        if fallback_code is not None:
            pcd.draw_options.append(fallback_code)
    elif n_sizes > 0:
        # Uniform size (scalar s=... or all same) - use fixed mark size
        # When s=300 is passed, get_sizes() returns array([300]) with length 1
        size = float(sizes.flat[0])
        ff = data.float_format
        radius_pt = np.sqrt(size / np.pi)
        pcd.draw_options.append(f"mark size={radius_pt:{ff}}pt")


def get_draw_options(data: TikzData, line_data: LineData) -> list[str]:
    """Get the draw options for a given (patch) object."""
    return (
        _get_draw_options_ec(data, line_data)
        + _get_draw_options_fc(data, line_data)
        + _get_draw_options_transparency(data, line_data)
        + _get_draw_options_linewidth(data, line_data)
        + _get_draw_options_linestyle(data, line_data)
        + _get_draw_options_hatch(data, line_data)
    )


def _get_draw_options_ec(data: TikzData, line_data: LineData) -> list[str]:
    if line_data.ec is None:
        return []

    line_data.ec_name, line_data.ec_rgba = _color.mpl_color2xcolor(data, line_data.ec)
    if line_data.ec_rgba[3] > 0:
        return [f"draw={line_data.ec_name}"]
    return ["draw=none"]


def _get_draw_options_fc(data: TikzData, line_data: LineData) -> list[str]:
    if line_data.fc is None:
        return []
    line_data.fc_name, line_data.fc_rgba = _color.mpl_color2xcolor(data, line_data.fc)
    if line_data.fc_rgba[3] > 0.0:
        return [f"fill={line_data.fc_name}"]
    # Don't draw if it's invisible anyways.
    return []


def _get_draw_options_transparency(data: TikzData, line_data: LineData) -> list[str]:
    ff = data.float_format
    if (
        line_data.ec_rgba is not None
        and line_data.fc_rgba is not None
        and line_data.ec_rgba[3] != 1.0
        and line_data.ec_rgba[3] == line_data.fc_rgba[3]
    ):
        return [f"opacity={line_data.ec_rgba[3]:{ff}}"]
    draw_options = []
    if line_data.ec_rgba is not None and 0 < line_data.ec_rgba[3] < 1.0:
        draw_options.append(f"draw opacity={line_data.ec_rgba[3]:{ff}}")
    if line_data.fc_rgba is not None and 0 < line_data.fc_rgba[3] < 1.0:
        draw_options.append(f"fill opacity={line_data.fc_rgba[3]:{ff}}")
    return draw_options


def _get_draw_options_linewidth(data: TikzData, line_data: LineData) -> list[str]:
    if line_data.lw is None:
        return []
    lw_ = mpl_linewidth2pgfp_linewidth(data, line_data.lw)
    if lw_:
        return [lw_]
    return []


def _get_draw_options_linestyle(data: TikzData, line_data: LineData) -> list[str]:
    if line_data.ls is None:
        return []
    ls_ = mpl_linestyle2pgfplots_linestyle(data, line_data.ls)
    if ls_ is not None and ls_ != "solid":
        return [ls_]
    return []


def _get_draw_options_hatch(data: TikzData, line_data: LineData) -> list[str]:
    if line_data.hatch is None:
        return []

    # In matplotlib hatches are rendered with edge color and linewidth
    # In PGFPlots patterns are rendered in 'pattern color' which defaults to
    # black and according to opacity fill.
    # No 'pattern line width' option exist.
    # This can be achieved with custom patterns, see _hatches.py

    # There exist an obj.get_hatch_color() method in the mpl API,
    # but it seems to be unused
    try:
        hc = line_data.obj._hatch_color  # type: ignore[union-attr]  # noqa: SLF001
    except AttributeError:  # Fallback to edge color
        if (
            line_data.ec_name is not None
            and line_data.ec_rgba is not None
            and line_data.ec_rgba[3] != 0.0
        ):
            h_col, h_rgba = line_data.ec_name, line_data.ec_rgba
        else:
            # Assuming that a hatch marker indicates that hatches are wanted, also
            # when the edge color is (0, 0, 0, 0), i.e., the edge is invisible
            h_col, h_rgba = "black", np.array([0, 0, 0, 1])
    else:
        h_col, h_rgba = _color.mpl_color2xcolor(data, hc)
    finally:
        if h_rgba[3] > 0:
            pattern = _mpl_hatch2pgfp_pattern(data, line_data.hatch, h_col, h_rgba)
        else:
            pattern = []
    return pattern


def mpl_linewidth2pgfp_linewidth(data: TikzData, line_width: float) -> str | None:
    """PGFplots gives line widths in pt, matplotlib in axes space. Translate.

    Scale such that the default mpl line width (1.5) is mapped to the PGFplots
    line with semithick, 0.6. From a visual comparison, semithick or even thick
    matches best with the default mpl style.
    Keep the line width in units of decipoint to make sure we stay in integers.
    """
    line_width_decipoint = line_width * 4
    try:
        # https://github.com/pgf-tikz/pgf/blob/e9c22dc9fe48f975b7fdb32181f03090b3747499/tex/generic/pgf/frontendlayer/tikz/tikz.code.tex#L1574
        return {
            1.0: "ultra thin",
            2.0: "very thin",
            4.0: None,  # "thin",
            6.0: "semithick",
            8.0: "thick",
            12.0: "very thick",
            16.0: "ultra thick",
        }[line_width_decipoint]
    except KeyError:
        # explicit line width
        ff = data.float_format
        return f"line width={line_width_decipoint / 10:{ff}}pt"


def mpl_linestyle2pgfplots_linestyle(
    data: TikzData,
    line_style: str | tuple[float, Sequence[float] | None],
    line: Line2D | None = None,
) -> str | None:
    """Translates a line style of matplotlib to the corresponding style in PGFPlots."""
    # linestyle is a string or dash tuple. Legal string values are
    # solid|dashed|dashdot|dotted.  The dash tuple is (offset, onoffseq) where onoffseq
    # is an even length tuple of on and off ink in points.
    #
    # solid: [(None, None), (None, None), ..., (None, None)]  # noqa: ERA001
    # dashed: (0, (6.0, 6.0))                                 # noqa: ERA001
    # dotted: (0, (1.0, 3.0))                                 # noqa: ERA001
    # dashdot: (0, (3.0, 5.0, 1.0, 5.0))                      # noqa: ERA001
    ff = data.float_format
    if isinstance(line_style, tuple):
        if line_style[0] is None or line_style[1] is None:
            return None

        pgf_line_style = "dash pattern="
        pgf_line_style += " ".join(
            [
                f"on {ls_on:{ff}}pt off {ls_off:{ff}}pt"
                for ls_on, ls_off in zip(line_style[1][::2], line_style[1][1::2], strict=True)
            ]
        )
        return pgf_line_style

    if isinstance(line, Line2D) and line.is_dashed():
        # see matplotlib.lines.Line2D.set_dashes

        # get defaults
        default_dash_offset, default_dash_seq = _get_dash_pattern(line_style)

        # get dash format of line under test
        dash_offset, dash_seq = line._unscaled_dash_pattern  # type: ignore[attr-defined]  # noqa: SLF001

        lst = []
        if dash_seq != default_dash_seq:
            # generate own dash sequence
            lst.append(
                "dash pattern="
                + " ".join(
                    f"on {a:{ff}}pt off {b:{ff}}pt"
                    for a, b in zip(dash_seq[0::2], dash_seq[1::2], strict=True)
                )
            )

        if dash_offset != default_dash_offset:
            lst.append(f"dash phase={dash_offset}pt")

        if len(lst) > 0:
            return ", ".join(lst)

    return {
        "": None,
        "None": None,
        "none": None,  # happens when using plt.boxplot()
        "-": "solid",
        "solid": "solid",
        ":": "dotted",
        "--": "dashed",
        "-.": "dash pattern=on 1pt off 3pt on 3pt off 3pt",
    }[line_style]
