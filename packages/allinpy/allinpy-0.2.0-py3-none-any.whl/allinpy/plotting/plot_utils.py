from __future__ import annotations

import types
from typing import Literal, Sequence, Tuple, Union

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox, blended_transform_factory
from PIL import Image


def latex_plt(matplotlib: types.ModuleType) -> types.ModuleType:
    """This function updates the matplotlib library to use Latex and changes some default plot parameters.

    Parameters
    ----------
    matplotlib : module
        The matplotlib module (e.g., `import matplotlib`) to configure.

    Returns
    -------
    module
        The updated matplotlib module with LaTeX and custom settings applied.
    """

    pgf_with_latex = {
        "axes.labelsize": 6,
        "font.size": 6,
        "legend.fontsize": 6,
        "axes.titlesize": 6,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "figure.titlesize": 6,
        "pgf.rcfonts": False,
    }
    matplotlib.rcParams.update(pgf_with_latex)

    return matplotlib


def cm2inch(*tupl: Union[float, Tuple[float, ...]]) -> Tuple[float, ...]:
    """This function converts cm to inches.

    Obtained from: https://stackoverflow.com/questions/14708695/
    specify-figure-size-in-centimeter-in-matplotlib/22787457

    Parameters
    ----------
    tupl : float or tuple of float
        Size of the plot in centimeters. Can be provided as individual float arguments (e.g., width, height)
        or as a single tuple of floats.

    Returns
    -------
    tuple of float
        Converted image size in inches.

    """

    inch = 2.54
    if isinstance(tupl[0], tuple):
        return tuple(i / inch for i in tupl[0])
    else:
        return tuple(i / inch for i in tupl)


def label_subplots(
    f: Figure,
    texts: Sequence[str],
    x_offset: Union[float, Sequence[float]] = -0.07,
    y_offset: Union[float, Sequence[float]] = 0.015,
) -> None:
    """This function labels the subplots.

    Obtained from: https://stackoverflow.com/questions/52286497/
    matplotlib-label-subplots-of-different-sizes-the-exact-same-distance-from-corner

    Parameters
    ----------
    f : matplotlib.figure.Figure
        Matplotlib figure handle containing the subplots.
    texts : sequence of str
        List of labels for each subplot (e.g., ["A", "B", "C"]).
    x_offset : float or sequence of float, optional
        Horizontal offset(s) for the subplot labels.
        If a single float, the same offset is applied to all subplots.
        Default is -0.07.
    y_offset : float or sequence of float, optional
        Vertical offset(s) for the subplot labels.
        If a single float, the same offset is applied to all subplots.
        Default is 0.015.

    Returns
    -------
    None
        This function does not return any value.
    """

    # Get axes
    axes = f.get_axes()

    if isinstance(x_offset, float):
        x_offset = np.repeat(x_offset, len(axes))

    if isinstance(y_offset, float):
        y_offset = np.repeat(y_offset, len(axes))

    # Cycle over subplots and place labels
    for i, (ax, label) in enumerate(zip(axes, texts)):
        pos = ax.get_position()
        f.text(
            pos.x0 - x_offset[i],
            pos.y1 + y_offset[i],
            label,
            size=12,
        )


def get_text_coords(
    f: Figure,
    ax: Axes,
    cell_lower_left_x: float,
    cell_lower_left_y: float,
    printed_word: str,
    fontsize: int,
    fontweight: str = "normal",
) -> Tuple[float, float, Bbox]:
    """
    This function computes the length and height of a text and consideration of the font size.

    Parameters
    ----------
    f : matplotlib.figure.Figure
        Matplotlib figure handle.
    ax : matplotlib.axes.Axes
        Matplotlib axis handle.
    cell_lower_left_x : float
        Lower left x-coordinate.
    cell_lower_left_y : float
        Lower left y-coordinate.
    printed_word : str
        Text of which length is computed.
    fontsize : int
        Specified font size.
    fontweight : str
        Specified font weight.

    Returns
    -------
    float
        Text length.
    float
        Text height.
    Bbox
        The bounding box of the axis axes coordinates.

    """

    # Temporarily draw text
    t = ax.text(
        cell_lower_left_x,
        cell_lower_left_y,
        printed_word,
        fontsize=fontsize,
        fontweight=fontweight,
    )

    # Get text coordinates
    f.canvas.draw()
    renderer = f.canvas.get_renderer()
    bbox = t.get_window_extent(renderer=renderer).transformed(ax.transAxes.inverted())

    # Compute length and height
    text_length = bbox.x1 - bbox.x0
    text_height = bbox.y1 - bbox.y0

    # Remove printed text
    t.remove()

    return text_length, text_height, bbox


def center_x(
    cell_lower_left_x: float,
    cell_width: float,
    word_length: float,
    correct_for_length: bool = False,
) -> float:
    """This function centers text along the x-axis

    Parameters
    ----------
    cell_lower_left_x : float
        Lower left x-coordinate
    cell_width : float
        Width of cell in which text appears
    word_length : float
        Length of plotted word.
    correct_for_length : bool
        Boolean indicating whether we want to correct for the length of the word.

    Returns
    -------
    float
        Center x-position.
    """

    center = cell_lower_left_x + (cell_width / 2.0)
    if correct_for_length:
        center -= word_length / 2.0
    return center


def center_y(
    cell_lower_left_y: float, cell_height: float, y0: float, word_height: float
) -> float:
    """This function centers text along the y-axis.

    Parameters
    ----------
    cell_lower_left_y : float
        Lower left y-coordinate.
    cell_height : float
        Height of cell in which text appears.
    y0 : float
        Lower bound of text (sometimes can be lower than cell_lower_left_y (i.e., letter y)).
    word_height : float
        Height of plotted word.

    Returns
    -------
    float
        Center y-position.
    """

    return cell_lower_left_y + ((cell_height / 2.0) - y0) - (word_height / 2.0)


def plot_image(
    f: Figure,
    img_path: str,
    cell_x0: float,
    cell_x1: float,
    cell_y0: float,
    ax: Axes,
    text_y_dist: float,
    text: str,
    text_pos: str,
    fontsize: int,
    zoom: float = 0.2,
    cell_y1: float = np.nan,
    text_col: str = "k",
) -> Tuple[Axes, Bbox, AnnotationBbox]:
    """Plot an image centered in a cell (axes coords) and add a caption.

    Parameters
    ----------
    f : Figure
        Matplotlib figure handle.
    img_path : str
        Path to the image.
    cell_x0, cell_x1 : float
        Left/right of the cell (axes coords).
    cell_y0 : float
        Bottom of the cell (axes coords).
    ax : Axes
        Target axes.
    text_y_dist : float
        Vertical distance between image and text (axes coords).
    text : str
        Caption text.
    text_pos : str
        One of: {"left_below", "centered_below", "left_top", "centered_top"}.
    fontsize : int
        Caption fontsize.
    zoom : float
        Image zoom factor.
    cell_y1 : float
        Top of the cell (axes coords). If NaN, use `cell_y0` (place at `cell_y0`).
    text_col : str
        Caption color.

    Returns
    -------
    Axes
        The axes.
    Bbox
        Image bounding box in axes coordinates.
    AnnotationBbox
        The image artist container.
    """

    img = Image.open(img_path)

    # Center image inside the cell (axes coords)
    cell_w = cell_x1 - cell_x0
    image_x = cell_x0 + cell_w / 2.0

    if not np.isnan(cell_y1):
        cell_h = cell_y1 - cell_y0
        image_y = cell_y0 + cell_h / 2.0
    else:
        image_y = cell_y0

    imagebox = OffsetImage(img, zoom=zoom)
    imagebox.image.axes = ax

    ab = AnnotationBbox(
        imagebox,
        (image_x, image_y),
        xycoords="axes fraction",  # << key fix
        frameon=False,
        annotation_clip=False,
        pad=0,
    )
    ax.add_artist(ab)

    # Compute the image bbox in axes coords
    f.canvas.draw()
    renderer = f.canvas.get_renderer()
    bbox = ab.get_window_extent(renderer=renderer).transformed(ax.transAxes.inverted())

    # Compute caption position
    if text_pos == "left_below":
        x = bbox.x0
        y = bbox.y0 - text_y_dist
        va, ha = "top", "left"
    elif text_pos == "centered_below":
        word_len, _, _ = get_text_coords(f, ax, bbox.x0, bbox.y0, text, fontsize)
        x = center_x(bbox.x0, bbox.x1 - bbox.x0, word_len)
        y = bbox.y0 - text_y_dist
        va, ha = "top", "left"
    elif text_pos == "left_top":
        x = bbox.x0
        y = bbox.y1 + text_y_dist  # << top, not bottom
        va, ha = "bottom", "left"
    else:  # "centered_top" (default)
        word_len, _, _ = get_text_coords(f, ax, bbox.x0, bbox.y1, text, fontsize)
        x = center_x(bbox.x0, bbox.x1 - bbox.x0, word_len)
        y = bbox.y1 + text_y_dist
        va, ha = "bottom", "left"

    # ax.text(x, y, text, fontsize=fontsize, color=text_col, ha=ha, va=va, zorder=100)
    ax.text(
        x,
        y,
        text,
        fontsize=fontsize,
        color=text_col,
        ha=ha,
        va=va,
        transform=ax.transAxes,  # <- add this
        zorder=100,
    )
    return ax, bbox, ab


def plot_arrow(
    ax: Axes,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    shrink_a: float = 1,
    shrink_b: float = 1,
    connectionstyle: str = "arc3,rad=0",
    arrow_style: str = "<-",
) -> Axes:
    """This function plots arrows of the task schematic.

    Parameters
    ----------
    ax : Axes
         Matplotlib axis handle.
    x1 : float
         x-position of starting point
    y1 : float
        y-position of starting point
    x2 : float
        x-position of end point.
    y2 : float
        y-position of end point.
    shrink_a : float
        Degree with which arrow is decreasing at starting point.
    shrink_b : float
        Degree with which arrow is decreasing at end point.
    connectionstyle : str
        Style of connection line.
    arrow_style : str
        Matplotlib arrow style specifier (e.g. "->", "<-", "-|>", etc.).

    Returns
    -------
    Axes
         Matplotlib axis handle.
    """

    ax.annotate(
        "",
        xy=(x1, y1),
        xycoords="data",
        xytext=(x2, y2),
        textcoords="data",
        arrowprops=dict(
            arrowstyle=arrow_style,
            color="0.5",
            shrinkA=shrink_a,
            shrinkB=shrink_b,
            patchA=None,
            patchB=None,
            connectionstyle=connectionstyle,
            lw=1,
        ),
        clip_on=False,
        annotation_clip=False,
    )

    return ax


def plot_centered_text(
    ax: Axes,
    x0: float,
    x1: float,
    y0: float,
    y1: float | None,
    text: str,
    fontsize: int,
    fontweight: str = "normal",
    mode: Literal["axes", "data", "x_axes_y_data", "x_data_y_axes"] = "axes",
) -> Axes:
    """
    Plot text centered within a rectangular region, or centered along one axis only.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axis handle.
    x0, x1 : float
        Left/right bounds of the region.
    y0 : float
        Lower y-bound (or fixed y if y1=None).
    y1 : float or None
        Upper y-bound (if None, text is centered only along x).
    text : str
        Text to display.
    fontsize : int
        Font size.
    fontweight : str, optional
        Font weight (default: "normal").
    mode : {"axes", "data", "x_axes_y_data", "x_data_y_axes"}, optional
        Coordinate system mode.

    Returns
    -------
    matplotlib.axes.Axes
        Axis with added text.
    """
    # Compute midpoints
    x_mid = (x0 + x1) / 2.0
    y_mid = (y0 + y1) / 2.0 if y1 is not None else y0

    # Select transform
    if mode == "x_axes_y_data":
        trans = blended_transform_factory(ax.transAxes, ax.transData)
    elif mode == "x_data_y_axes":
        trans = blended_transform_factory(ax.transData, ax.transAxes)
    elif mode == "axes":
        trans = ax.transAxes
    elif mode == "data":
        trans = ax.transData
    else:
        raise ValueError(f"Invalid mode: {mode}")

    ax.text(
        x_mid,
        y_mid,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=fontweight,
        transform=trans,
    )
    return ax


def plot_rec(
    ax: Axes,
    cell_lower_left_x: float,
    width: float,
    cell_lower_left_y: float,
    height: float,
) -> Axes:
    """This function plots a rectangle.

    Parameters
    ----------
    ax : Axes
        Matplotlib axis handle.
    cell_lower_left_x : float
        Lower left corner x coordinate of rectangle.
    width : float
        Width of rectangle
    cell_lower_left_y : float
        Lower left corner y coordinate of rectangle
    height : float
        Height of rectangle

    Returns
    -------
    Axes

    """

    rect = Rectangle(
        (cell_lower_left_x, cell_lower_left_y),
        width,
        height,
        fill=False,
        transform=ax.transAxes,
        clip_on=False,
        linewidth=0.5,
    )
    ax.add_patch(rect)

    return ax


def plot_table(
    ax: Axes,
    n_rows: int = 8,
    n_cols: int = 4,
    col_header_line: float = 0.1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    This function draws grid lines for a table-like schematic on a Matplotlib axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axis handle.
    n_rows : int, optional
        Number of rows in the table (default: 8).
    n_cols : int, optional
        Number of columns in the table (default: 4).
    col_header_line : float, optional
        Fractional height (0–1) of the header row (default: 0.1).

    Returns
    -------
    tuple of numpy.ndarray
        (row_lines, col_lines)
        Coordinates of the horizontal (row) and vertical (column) grid lines.
    """
    # Compute normalized line positions
    row_lines = np.linspace(0.0, 1.0, n_rows + 1)
    col_lines = np.linspace(col_header_line, 1.0, n_cols)

    # Draw vertical grid lines
    for x in col_lines[:-1]:
        ax.axvline(x=x, ymin=0.0, ymax=1.0, color="k", linewidth=0.5, alpha=1)

    # Draw horizontal grid lines (skip first and last for frame)
    for y in row_lines[1:-1]:
        ax.axhline(y=y, xmin=0.0, xmax=1.0, color="k", linewidth=0.5, alpha=1)

    # Add leftmost column boundary (x = 0)
    col_lines = np.concatenate(([0.0], col_lines))

    return row_lines, col_lines
