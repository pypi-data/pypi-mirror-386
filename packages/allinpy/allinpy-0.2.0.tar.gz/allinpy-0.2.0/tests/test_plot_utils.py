import matplotlib
from allinpy import cm2inch, label_subplots
from allinpy.plotting.plot_utils import (center_x, center_y, get_text_coords,
                                         plot_centered_text, plot_rec,
                                         plot_table)

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.transforms import blended_transform_factory


def test_cm2inch_single_tuple():
    assert cm2inch((2.54, 5.08)) == (1.0, 2.0)


def test_cm2inch_two_args():
    assert cm2inch(2.54, 5.08) == (1.0, 2.0)


def test_label_subplots_runs():
    fig, axs = plt.subplots(1, 2)
    label_subplots(fig, ["A", "B"])
    assert len(fig.texts) == 2


def test_get_text_coords_runs():
    fig, ax = plt.subplots()
    width, height, bbox = get_text_coords(fig, ax, 0.1, 0.1, "Test", 12)
    assert width > 0 and height > 0
    assert hasattr(bbox, "x0")


def test_center_x():
    assert center_x(0.0, 1.0, 0.2, False) == 0.5
    assert center_x(0.0, 1.0, 0.2, True) == 0.4


def test_center_y_simple():
    y = center_y(0.0, 1.0, 0.0, 0.2)
    assert round(y, 3) == 0.4


def test_center_y_with_descender():
    y = center_y(0.0, 1.0, -0.05, 0.2)
    assert y > 0.4  # pushed up slightly


def test_plot_centered_text_runs_and_positions():

    fig, ax = plt.subplots()

    # Call matches the current signature
    ax = plot_centered_text(
        ax,
        0.2,
        0.8,  # x0, x1 (axes or data depending on mode)
        0.2,
        0.8,  # y0, y1 (if y1=None, only x is centered)
        "Test",
        fontsize=10,
        fontweight="normal",
        mode="axes",  # both axes coords
    )

    # One text added
    assert len(ax.texts) == 1
    t = ax.texts[0]

    # Position is the midpoint we provided (in the coords implied by 'mode')
    x, y = t.get_position()
    assert abs(x - 0.5) < 1e-6  # (0.2 + 0.8)/2
    assert abs(y - 0.5) < 1e-6  # (0.2 + 0.8)/2

    # Transform matches the mode
    assert t.get_transform() == ax.transAxes


def test_plot_centered_text_x_axes_y_data():

    fig, ax = plt.subplots()
    ax.set_ylim(0.0, 1.0)

    ax = plot_centered_text(
        ax,
        0.2,
        0.8,  # x0,x1 in axes
        0.98,
        None,  # fixed y in data
        "=0.2:",
        fontsize=10,
        mode="x_axes_y_data",
    )

    t = ax.texts[0]
    x, y = t.get_position()
    assert abs(x - 0.5) < 1e-6
    assert abs(y - 0.98) < 1e-12

    # Compare transforms by transforming a point
    expected = blended_transform_factory(ax.transAxes, ax.transData)
    fig.canvas.draw()  # ensure transforms are up to date

    pt_expected = expected.transform((x, y))
    pt_text = t.get_transform().transform((x, y))
    assert np.allclose(pt_expected, pt_text, atol=1e-9)


def test_plot_rec_adds_rectangle():

    fig, ax = plt.subplots()

    # Run function
    ax = plot_rec(ax, 0.1, 0.3, 0.2, 0.4)

    # There should be one rectangle in ax.patches
    rects = [p for p in ax.patches if isinstance(p, Rectangle)]
    assert len(rects) == 1

    # Check coordinates and dimensions roughly match
    r = rects[0]
    assert abs(r.get_x() - 0.1) < 1e-6
    assert abs(r.get_y() - 0.2) < 1e-6
    assert abs(r.get_width() - 0.3) < 1e-6
    assert abs(r.get_height() - 0.4) < 1e-6


def test_plot_table_lines():

    fig, ax = plt.subplots()
    rows, cols = plot_table(ax, n_rows=3, n_cols=2)

    # Basic sanity
    assert isinstance(rows, np.ndarray)
    assert isinstance(cols, np.ndarray)
    assert len(rows) == 4  # n_rows + 1
    assert len(cols) == 3  # n_cols + header col
    assert np.isclose(rows[0], 0.0)
    assert np.isclose(rows[-1], 1.0)
    assert np.isclose(cols[0], 0.0)
    assert np.isclose(cols[-1], 1.0)
