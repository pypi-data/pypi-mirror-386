from __future__ import annotations

import pytest

from quantify.resources import BasebandClockResource, ClockResource


def test_clock_resource() -> None:
    """
    Clock associated with qubit.
    """
    clock = ClockResource("q0:cl:01", freq=6.5e9, phase=23.9)
    assert clock.data["name"] == "q0:cl:01"
    assert clock.data["freq"] == 6.5e9
    assert clock.data["phase"] == 23.9

    # clock 3
    clock = ClockResource("cl3", freq=4.5e9)
    assert clock.data["name"] == "cl3"
    assert clock.data["freq"] == 4.5e9
    assert clock.data["phase"] == 0


def test_baseband_clock_resource() -> None:
    """
    Clock associated with qubit.
    """
    clock = BasebandClockResource("baseband")
    assert clock.data["name"] == "baseband"
    assert clock.data["freq"] == 0


@pytest.mark.parametrize(
    "ressource",
    [
        ClockResource("q0:cl:01", freq=6.5e9, phase=23.9),
        ClockResource("cl3", freq=4.5e9),
        BasebandClockResource("baseband"),
    ],
)
def test_ressource_reconstruction(
    ressource: BasebandClockResource | ClockResource,
) -> None:
    reconstructed_ressource = eval(repr(ressource))
    assert ressource == reconstructed_ressource
