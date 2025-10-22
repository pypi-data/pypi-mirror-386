"""Utility command enumerations for plot monitoring."""

from enum import Enum


class CommandType(Enum):
    """Enumeration of command types for plot monitoring."""

    START = "start_experiment"
    STOP = "stop_experiment"
    GRAPH_CONFIG = "graph_config"
    UPDATE_DATA = "update_data"

    @staticmethod
    def from_str(label: str) -> "CommandType":
        """Convert a string to a CommandType enum member."""
        match label.lower():
            case "start_experiment":
                return CommandType.START
            case "stop_experiment":
                return CommandType.STOP
            case "graph_config":
                return CommandType.GRAPH_CONFIG
            case "update_data":
                return CommandType.UPDATE_DATA
            case _:
                raise ValueError(f"Unknown command type: {label}")


class ExperimentState(Enum):
    """Enumeration of experiment states."""

    STARTED = "started"
    FINISHED = "finished"

    @staticmethod
    def from_str(label: str) -> "ExperimentState":
        """Convert a string to an ExperimentState enum member."""
        match label.lower():
            case "started":
                return ExperimentState.STARTED
            case "finished":
                return ExperimentState.FINISHED
            case _:
                raise ValueError(f"Unknown experiment state: {label}")
