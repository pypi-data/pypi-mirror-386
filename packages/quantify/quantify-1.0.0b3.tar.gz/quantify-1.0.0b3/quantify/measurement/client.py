"""Measurement client module for handling experiment communication and data updates."""

import logging
from datetime import datetime

from quantify.measurement.control import MeasurementControl
from quantify.measurement.services.experiments import (
    start_experiment,
    stop_experiment,
    update_experiment,
)
from quantify.measurement.services.plot_config import (
    get_config_from_dataset,
)
from quantify.measurement.services.ui_tool import UITool
from quantify.visualization.plotmon.utils.commands import CommandType
from quantify.visualization.plotmon.utils.communication import (
    Message,
)


class MeasurementClient(MeasurementControl):
    """Measurement client for handling experiment communication and data updates."""

    def __init__(self, name: str, ui_tool: UITool) -> None:
        """Initialize the measurement client.

        Args:
            name: Name of the measurement control instance.
            ui_tool: The UI tool instance to use for communication.
            Can initialize and sends it to the server.

        """
        super().__init__(name)
        self._last_experiment_name: str | None = None
        self._ui_tool = ui_tool
        self._ui_tool.init(name)

    def _init(self, name: str) -> None:
        super()._init(name)
        if self._dataset is None:
            logging.warning(
                "Failed to initialize experiment '%s': Dataset not found.", name
            )
            return

        if self._last_experiment_name != name:
            # Reconfigure graphs on new experiment
            graph_config_message = Message(
                event=get_config_from_dataset(self._dataset, self.name),
                event_type=CommandType.GRAPH_CONFIG,
                timestamp=datetime.now().isoformat(),
            )
            self._send_message(graph_config_message)
            self._last_experiment_name = name

        message = Message(
            event=start_experiment(self._dataset, self.name),
            event_type=CommandType.START,
            timestamp=datetime.now().isoformat(),
        )
        self._send_message(message)

    def _finish(self) -> None:
        super()._finish()

        if self._dataset is None:
            logging.warning(
                "Failed to end experiment '%s': Dataset not found.",
                self._last_experiment_name,
            )
            return
        message = Message(
            event=stop_experiment(self._dataset, self.name),
            event_type=CommandType.STOP,
            timestamp=datetime.now().isoformat(),
        )

        self._send_message(message)

    def _send_message(self, message: Message) -> None:
        """Send a message to the plot monitoring server."""
        self._ui_tool.callback(message)

    def _update(self, print_message: str | None = None) -> None:
        """Call the parent class update method, send a message with recent data."""
        super()._update(print_message)  # type: ignore
        if self._dataset is not None:
            updates = update_experiment(
                self._dataset,
                self.name,
                self._nr_acquired_values,
                int(self._batch_size_last) if self._batch_size_last else 1,
            )
            for update in updates:
                message = Message(
                    event=update,
                    event_type=CommandType.UPDATE_DATA,
                    timestamp=datetime.now().isoformat(),
                )
                self._send_message(message)
