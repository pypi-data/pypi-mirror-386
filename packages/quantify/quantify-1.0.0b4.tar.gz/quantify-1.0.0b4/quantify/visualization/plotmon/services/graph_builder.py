"""
graph_builder module: Provides utilities for building Bokeh graph layouts for
Plotmon applications.
"""

import logging
from collections.abc import Callable

import numpy as np
from bokeh.models import Column, ColumnDataSource, DataRange1d, Div, Row
from bokeh.plotting import column, figure

from quantify.visualization.plotmon.services.figure_builder import table_builder
from quantify.visualization.plotmon.services.figure_builder.figure_builder_factory import (  # noqa: E501
    FigureBuilderFactory,
)
from quantify.visualization.plotmon.utils.communication import ParamInfo
from quantify.visualization.plotmon.utils.figures import HeatmapConfig, PlotType
from quantify.visualization.plotmon.utils.tuid_data import TuidData

_NAV_ROW_HEIGHT = 200
_NAV_ROW_WIDTH = 500


def _create_rows(
    configs: list[list[ParamInfo]],
    sources: dict[str, ColumnDataSource],
    tuid_data: TuidData,
    current_rows: list | None = None,
) -> list[Row]:
    shared_ranges = _create_shared_ranges(configs)
    rows: list[Row] = []
    if current_rows is None:
        current_rows = [None] * len(configs)
    for row_config, row_obj in zip(configs, current_rows):
        figures = []
        row_elements = [None] * len(row_config) if row_obj is None else row_obj.children
        for config, fig in zip(row_config, row_elements):
            ranges = {
                "x_range": shared_ranges[config.x_key],
                "y_range": shared_ranges[config.y_key],
            }
            f = _build_figure(config, sources, tuid_data, ranges, fig)
            figures.append(f)
            logging.warning("Built figure: %s", f.id)
        rows.append(
            Row(
                *figures,
                sizing_mode="stretch_both",
                styles={
                    "background-color": "#ffffff",
                    "border": "1px solid #e1e5e9",
                    "border-radius": "12px",
                    "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.05)",
                    "padding": "16px",
                    "margin": "8px",
                },
            )
        )
    return rows


def _create_shared_ranges(configs: list[list[ParamInfo]]) -> dict[str, DataRange1d]:
    """
    Create shared x and y ranges for plots that share the same axes.

    Parameters
    ----------
    configs : list[list[dict]]
        List of configuration dictionaries for each figure.

    Returns
    -------
    dict[tuple[str, str], dict[str, Any]]
        A dictionary mapping (x_key, y_key) tuples to shared range dictionaries.

    """
    axis_groups = {}
    for row_config in configs:
        for config in row_config:
            x_key: str = config.x_key
            y_key: str = config.y_key
            if x_key not in axis_groups:
                axis_groups[x_key] = DataRange1d()
            if y_key not in axis_groups:
                axis_groups[y_key] = DataRange1d()

    return axis_groups


def _make_source_name(tuid: str, plot_name: str) -> str:
    """Helper to construct a source name for a given TUID and plot name."""
    if tuid == "":
        return plot_name
    return f"{tuid}_{plot_name}"


def _build_figure(
    config: ParamInfo,
    sources: dict[str, ColumnDataSource],
    tuid_data: TuidData,
    ranges: dict[str, DataRange1d],
    fig: figure | None = None,
) -> figure:
    """
    Build a new figure based on the given configuration and data sources.

    Parameters
    ----------
    config : dict
        Configuration dictionary for the figure.
    sources : dict[str, ColumnDataSource]
        Dictionary of data sources to be used in the figure.
    tuid_data : TuidData
        TUID related data for the application.
    ranges : dict[str, DataRange1d]
        Shared x and y ranges for the figure.
    fig : figure | None
        Existing figure to update, or None to create a new one.

    Returns
    -------
    Column
        A Bokeh Column layout containing the figure.

    """
    plot_type = PlotType(config.plot_type)
    figure_builder = FigureBuilderFactory.get_builder(plot_type)
    return figure_builder.build_figure(config, sources, tuid_data, ranges, fig)


def build_layout(
    configs: list[list[ParamInfo]],
    sources: dict[str, ColumnDataSource],
    tuid_data: TuidData,
    meta_data: dict[str, dict],
    on_select: Callable,
    current_layout: Column | None = None,
) -> Column:
    """
    Build a Bokeh layout from the given configurations and data sources.

    Parameters
    ----------
    configs : list[dict]
        List of configuration dictionaries for each figure.
    sources : dict[str, ColumnDataSource]
        Dictionary of data sources to be used in the figures.
    tuid_data : TuidData
        TUID related data for the application.
    meta_data : dict[str, dict]
        Metadata for the experiments.
    on_select : Callable
        Callback function to be called when a TUID is selected.
    current_layout : Column | None
        Existing layout to update, or None to create a new one.

    Returns
    -------
    Column
        A Bokeh Column layout containing all the figures.

    """
    rows = _create_rows(
        configs,
        sources,
        tuid_data,
        current_layout.children[1:] if current_layout else None,
    )

    header = Div(text="<h3>Select Experiment</h3>")

    prev_table = None
    if (
        current_layout
        and len(current_layout.children) > 0
        and isinstance(current_layout.children[0], Column)
        and len(current_layout.children[0].children) > 1
        and isinstance(current_layout.children[0].children[1], table_builder.DataTable)
    ):
        prev_table = current_layout.children[0].children[1]

    table = table_builder.create_table(
        sources,
        on_select,
        tuid_data,
        meta_data,
        prev_table,
    )

    nav_column = column(
        header,
        table,
        width=_NAV_ROW_WIDTH,
        min_width=0,
        max_width=_NAV_ROW_WIDTH,
        height=_NAV_ROW_HEIGHT,
        min_height=_NAV_ROW_HEIGHT,
        sizing_mode=None,
    )

    if current_layout:
        current_layout.children = [nav_column, *rows]
        return current_layout
    return column(nav_column, *rows, sizing_mode="stretch_both")


def create_sources(
    graph_configs: list[list[ParamInfo]], tuid: str = ""
) -> dict[str, ColumnDataSource]:
    """
    Create data sources based on the provided graph configurations and TUID.

    Parameters
    ----------
    graph_configs : list[dict]
        List of graph configuration dictionaries.
    tuid : str
        The TUID to be used as the key for the data sources.

    Returns
    -------
    dict[str, ColumnDataSource]
        A dictionary of created data sources.

    """
    sources = {}
    for row_config in graph_configs:
        for config in row_config:
            plot_type = config.plot_type
            if plot_type == PlotType.ONE_D.value:
                source_name = _make_source_name(tuid, config.plot_name)
                sources[source_name] = ColumnDataSource(
                    data={
                        config.x_key: [],
                        config.y_key: [],
                        "tuid": [],
                    }
                )
            elif plot_type == PlotType.HEATMAP.value and isinstance(
                config, HeatmapConfig
            ):
                source_name = _make_source_name(tuid, config.plot_name)
                placeholder_image = np.full((1, 1), np.nan)  # 1x1 array of NaN
                sources[source_name] = ColumnDataSource(
                    data={
                        config.image_key: [placeholder_image],
                        config.x_key: [0],
                        config.y_key: [0],
                        config.dw_key: [1],
                        config.dh_key: [1],
                        "tuid": [""],
                    }
                )
            else:
                raise ValueError("Config must contain either '1d' or 'heatmap' key.")

    sources["table_source"] = ColumnDataSource(
        data={"tuid": [], "start_date": [], "end_date": []}
    )
    return sources
