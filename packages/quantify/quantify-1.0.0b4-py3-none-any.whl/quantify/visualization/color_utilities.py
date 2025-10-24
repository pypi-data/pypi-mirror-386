# Repository: https://gitlab.com/quantify-os/quantify
# Licensed according to the LICENSE file on the main branch
"""Module containing utilities for color manipulation."""

from __future__ import annotations

import colorsys
from typing import TYPE_CHECKING

import matplotlib.colors as mplc
import numpy as np

if TYPE_CHECKING:
    from matplotlib.typing import ColorType


def set_hlsa(
    color: ColorType,
    h: float | None = None,
    l: float | None = None,
    s: float | None = None,
    a: float | None = None,
    to_hex: bool = False,
) -> tuple:
    """
    Create an RGB(A) color specification from HLS(A) values.

    Accepts a  Matplotlib HLS(A) color specification (hue/lightness/saturation and
    optionally alpha value) and returns an RGB (red/green/blue) color with
    the specified HLS(A) values.

    .. seealso:: :ref:`howto-visualization-custom-colormaps`

    Parameters
    ----------
    color
        HLS(A) color values
    h
        The value of the first hue.
    l
        The lightness value.
    s
        The saturation intensity.
    a
        Alpha bending value
    to_hex
        If `True`, returns integers in `0..255` interval, otherwise floats in `0..1`
        range.

    Returns
    -------
    :
        Color RGB(A)

    """

    def clip(x):  # noqa: ANN001, ANN202
        return np.clip(x, 0, 1)

    rgb = mplc.to_rgb(color)
    hls = colorsys.rgb_to_hls(*mplc.to_rgb(rgb))
    new_hls = (old if new is None else clip(new) for old, new in zip(hls, (h, l, s)))
    col = colorsys.hls_to_rgb(*new_hls)

    # append alpha to tuple
    col = col if a is None else col + (clip(a),)
    # convert to int 255 range
    col = col if not to_hex else tuple(round(255 * x) for x in col)

    return col


def make_fadded_colors(  # noqa: D103
    num: int = 5,
    color: ColorType = "#1f77b4",
    min_alpha: float = 0.3,
    sat_power: int = 2,
    to_hex: bool = False,
) -> tuple:
    hls = colorsys.rgb_to_hls(*mplc.to_rgb(mplc.to_rgb(color)))
    sat_vals = (np.linspace(1.0, 0.0, num) ** sat_power) * hls[2]
    alpha_vals = np.linspace(1.0, min_alpha, num)
    colors = tuple(
        set_hlsa(color, s=s, a=a, to_hex=to_hex)  # type: ignore
        for s, a in zip(sat_vals, alpha_vals)
    )
    return colors
