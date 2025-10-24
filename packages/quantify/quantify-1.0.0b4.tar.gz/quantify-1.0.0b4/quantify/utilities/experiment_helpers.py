# Repository: https://gitlab.com/quantify-os/quantify
# Licensed according to the LICENSE file on the main branch
"""Helpers for performing experiments."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from deepdiff import DeepDiff  # type: ignore
from qcodes.instrument import Instrument, InstrumentBase, InstrumentChannel
from qcodes.parameters import Parameter

from quantify.data.handling import get_latest_tuid, load_snapshot
from quantify.visualization.pyqt_plotmon import PlotMonitor_pyqt

if TYPE_CHECKING:
    from quantify.data.types import TUID


# pylint: disable=broad-except
def load_settings_onto_instrument(  # noqa PLR0915
    instrument: Instrument | InstrumentChannel,
    tuid: TUID | None = None,
    datadir: str | None = None,
    load_metadata: bool = False,
    exception_handling: Literal["raise", "warn"] = "raise",
) -> None:
    """
    Loads settings from a previous experiment onto a current
    :class:`~qcodes.instrument.Instrument`, or any of its submodules or
    parameters. This information is loaded from the 'snapshot.json' file in
    the provided experiment directory.

    Parameters
    ----------
    instrument :
        the :class:`~qcodes.instrument.Instrument`,
        :class:`~qcodes.instrument.InstrumentChannel` or
        :class:`~qcodes.parameters.Parameter` to be configured.
    tuid : :class:`~quantify.data.types.TUID`
        the TUID of the experiment. If None use latest TUID.
    datadir : str
        path of the data directory. If `None`, uses `get_datadir()` to
        determine the data directory.
    exception_handling:
        desired behaviour if error occurs when trying to get parameter:
        raise exception or give warning.

    Raises
    ------
    ValueError
        if the provided instrument has no match in the loaded snapshot.

    """
    if tuid is None:
        tuid = get_latest_tuid()

    instruments = load_snapshot(tuid, datadir)["instruments"]
    instruments_numpy_array = load_snapshot(tuid, datadir, list_to_ndarray=True)[
        "instruments"
    ]

    def _try_to_set_par_safe(
        instr_mod: Instrument | InstrumentChannel,
        parname: str,
        value: Any,  # noqa: ANN401
        value_np: Any,  # noqa: ANN401
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Tries to set a parameter and emits a warning if not successful."""
        # do not try to set parameters that are not settable
        if "set" not in dir(param := instr_mod.parameters[parname]):
            return
        # do not set to None if value is already None. If there is a runtime
        # error when getting the parameter, do not try to set the parameter.
        try:
            get_val = param()
        except Exception as exc:
            if exception_handling == "raise":
                raise exc
            warnings.warn(
                f"Could not get value of {parname} parameter due to '{exc}'. "
                "We will not try to set this parameter."
            )
            return
        if get_val is None and value is None:
            return

        # Make sure the parameter is actually a settable
        try:
            # Update metadata if desired. We do this before setting the value since some
            # parameters might use metadata when setting the value.
            if load_metadata and metadata:
                param.metadata = metadata
            if isinstance(get_val, np.ndarray):
                param.set(value_np)
            else:
                param.set(value)
        except (RuntimeError, KeyError, ValueError, TypeError) as exc:
            warnings.warn(
                f'Parameter "{parname}" of "{instr_mod.name}" '
                f'could not be set to "{value}" due to error:\n{exc}'
            )

    parents = get_all_parents(instrument)

    # Find the snapshot for this instrument, submodule or parameter
    for parent in parents:
        if isinstance(parent, Instrument):
            if parent.name not in instruments:
                raise ValueError(
                    f'Instrument "{parent.name}" not found in snapshot {datadir}:{tuid}'
                )
            instr_mod_snap = instruments[parent.name]
            instr_mod_snap_numpy_array = instruments_numpy_array[parent.name]

        if isinstance(parent, InstrumentChannel):
            if parent._short_name not in instr_mod_snap["submodules"]:  # type: ignore
                raise ValueError(
                    f'Submodule "{parent.name}" not found in snapshot {datadir}:{tuid}'
                )
            instr_mod_snap = instr_mod_snap["submodules"][parent._short_name]  # type: ignore
            instr_mod_snap_numpy_array = instr_mod_snap_numpy_array["submodules"][  # type: ignore
                parent._short_name
            ]

        # If we are only setting one parameter, try to set this immediately
        if isinstance(parent, Parameter):
            if parent.name not in instr_mod_snap["parameters"]:  # type: ignore
                address = ".".join([p._short_name for p in parents])
                raise ValueError(
                    f'Parameter "{address}" not found in snapshot {datadir}:{tuid}'
                )
            value = instr_mod_snap["parameters"][parent.name]["value"]  # type: ignore
            value_np = instr_mod_snap_numpy_array["parameters"][parent.name]["value"]  # type: ignore
            metadata = instr_mod_snap["parameters"][parent.name].get("metadata")  # type: ignore
            _try_to_set_par_safe(parents[-2], parent.name, value, value_np, metadata)
            return

    def _set_params_instr_mod(
        instr_mod_snap: dict,
        instr_mod_snap_np: dict,
        instr_mod: Instrument | InstrumentChannel,
    ) -> None:
        """
        Private function to set parameters and recursively set parameters
        of submodules.
        """
        # iterate over top-level parameters
        for parname, par in instr_mod_snap["parameters"].items():
            # Check that the parameter exists in this instrument
            if parname in instr_mod.parameters:
                value = par["value"]
                value_np = instr_mod_snap_np["parameters"][parname]["value"]
                metadata = instr_mod_snap["parameters"][parname].get("metadata")
                _try_to_set_par_safe(instr_mod, parname, value, value_np, metadata)
            else:
                warnings.warn(
                    f"Could not set parameter {parname} in {instr_mod.name}. "
                    f"{instr_mod.name} does not possess a parameter named {parname}."
                )
        # recursively call this function for all submodules
        if "submodules" in instr_mod_snap:
            for module_name, module_snap in instr_mod_snap["submodules"].items():
                submodule = instr_mod.submodules[module_name]
                module_snap_np = instr_mod_snap_np["submodules"][module_name]
                _set_params_instr_mod(
                    instr_mod_snap=module_snap,
                    instr_mod_snap_np=module_snap_np,
                    instr_mod=submodule,  # type: ignore
                )

    # set the top-level parameters and then recursively set parameters of submodules
    _set_params_instr_mod(
        instr_mod_snap=instr_mod_snap,  # type: ignore
        instr_mod_snap_np=instr_mod_snap_numpy_array,  # type: ignore
        instr_mod=instrument,
    )


def compare_snapshots(old_snapshot: dict, new_snapshot: dict) -> dict:
    """
    Generate a diff between two quantify snapshots, showing which qcodes parameters
    have changed.

    This function only considers changes in numerical values of quantities and
    ignores type changes, such as :code:`numpy.float64` to :code:`float`, for
    example.

    We also only consider the values of qcodes parameters, and not metadata like
    timestamps, which always change from snapshot to snapshot.

    Parameters
    ----------
    old_snapshot:
        The original snapshot to be compared
    new_snapshot:
        The new snapshot to be compared

    Return
    ------
    :
        A dictionary summarising the differences between the two snapshots

    """
    return DeepDiff(
        old_snapshot,
        new_snapshot,
        exclude_regex_paths=[r"\['ts'\]", r"\['raw_value'\]", r"\['IDN'\]"],
        ignore_numeric_type_changes=True,
    )


def get_all_parents(
    instr_mod: Instrument | InstrumentChannel | InstrumentBase,
) -> list:
    """
    Get a list of all the parent submodules and instruments of a given QCodes
    instrument, submodule or parameter.

    Parameters
    ----------
    instr_mod:
        The QCodes instrument, submodule or parameter whose parents we wish to find

    Returns
    -------
    :
        A list of all the parents of that object (and the object itself)

    """
    if hasattr(instr_mod, "_parent"):
        parents = get_all_parents(instr_mod._parent)
        parents.append(instr_mod)
    elif hasattr(instr_mod, "_instrument"):
        parents = get_all_parents(instr_mod._instrument)
        parents.append(instr_mod)
    else:
        parents = [instr_mod]

    return parents


def create_plotmon_from_historical(
    tuid: TUID | None = None, label: str = ""
) -> PlotMonitor_pyqt:
    """
    Creates a plotmon using the dataset of the provided experiment denoted by the tuid
    in the datadir.
    Loads the data and draws any required figures.

    NB Creating a new plotmon can be slow. Consider using
    :func:`!PlotMonitor_pyqt.tuids_extra` to visualize dataset in the same plotmon.

    Parameters
    ----------
    tuid
        the TUID of the experiment.
    label
        if the `tuid` is not provided, as label will be used to search for the latest
        dataset.

    Returns
    -------
    :
        the plotmon

    """
    # avoid creating a plotmon with the same name
    if tuid is None:
        tuid = get_latest_tuid(contains=label)

    tuid_str = str(tuid)
    # python attributes can't start with a number
    name = "_" + tuid_str

    # hyphens not allowed in instrument names for qcodes v0.34 and up
    name = name.replace("-", "_")

    plotmon = PlotMonitor_pyqt(name)
    plotmon.tuids_append(tuid)
    plotmon.update()  # make sure everything is drawn

    return plotmon
