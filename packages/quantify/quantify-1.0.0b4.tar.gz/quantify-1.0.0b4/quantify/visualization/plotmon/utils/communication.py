"""A module defining message models for Plotmon communication using Pydantic."""

from pydantic import BaseModel, ConfigDict, Field

from quantify.visualization.plotmon.utils.commands import CommandType
from quantify.visualization.plotmon.utils.figures import HeatmapConfig, OneDFigureConfig

ParamInfo = OneDFigureConfig | HeatmapConfig


class _BaseMessage(BaseModel):
    """Base message model for Plotmon communication."""

    # Disallow additional fields and incorrect types
    model_config = ConfigDict(extra="forbid", strict=True)


class PlotmonConfig(_BaseMessage):
    """
    graph_configs: A two-dimensional list representing the configuration of
      graphs to be displayed.
    Each inner list corresponds to a row of graphs,
      and each dictionary within the inner list contains
    the configuration for an individual graph in that row.
      The outer list represents the columns of the graph layout.

    Example:
    [
        [ {graph1_config}, {graph2_config} ],  # Row 1
        [ {graph3_config} ]                    # Row 2
    ]

    """

    data_source_name: str = Field(
        default="default_source", description="Name of the data source."
    )
    graph_configs: list[list[ParamInfo]] = Field(
        ...,
        description="A two-dimensional list representing the configuration of"
        " graphs to be displayed. "
        "Each inner list corresponds to a row of graphs,"
        " and each dictionary within the inner list "
        "contains the configuration for an individual graph in that row."
        " The outer list represents the columns "
        "of the graph layout.",
    )
    title: str = Field(
        default="Plotmon App", description="Title of the Plotmon application."
    )


class StartExperimentMessage(_BaseMessage):
    """Message model for starting an experiment."""

    data_source_name: str
    tuid: str


class StopExperimentMessage(_BaseMessage):
    """Message model for stopping an experiment."""

    data_source_name: str
    tuid: str


class Data(BaseModel):
    """
    Data has dynamic attributes based on requirements from plottype and
    with config we should be able to have custom names of the data points.
    """

    sequence_ids: list[int] = Field(
        ...,
        description="Unique sequential identifiers for the data points."
        " This should be sequentially updated."
        " Extra check for receiving data in order.",
    )
    tuid: list[str] = Field(
        ..., description="The TUID associated with this data point."
    )

    model_config = ConfigDict(extra="allow")  # Allow dynamic fields


class UpdateDataMessage(_BaseMessage):
    """Message model for updating data."""

    data_source_name: str = Field(..., description="Name of the data source.")
    tuid: str = Field(..., description="The TUID associated with the data.")
    plot_name: str = Field(..., description="Name of the plot to update.")
    data: Data = Field(..., description="Data points to update.")


_EVENT_TYPE = (
    StartExperimentMessage | StopExperimentMessage | UpdateDataMessage | PlotmonConfig
)


class Message(_BaseMessage):
    """General message model for Plotmon communication."""

    event: _EVENT_TYPE = Field(..., description="The event message.")
    timestamp: str = Field(..., description="Timestamp of the message.")
    event_type: CommandType = Field(..., description="Type of the event.")
