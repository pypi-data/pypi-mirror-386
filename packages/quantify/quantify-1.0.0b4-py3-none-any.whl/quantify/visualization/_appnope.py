# Repository: https://gitlab.com/quantify-os/quantify
# Licensed according to the LICENSE file on the main branch
"""Wrapper of appnope to avoid App Nap (macOS) of Quantify process."""

import platform
import sys

# See also:
# https://github.com/pyqtgraph/pyqtgraph/pull/1092
# https://forum.libcinder.org/topic/os-x-how-to-keep-rendering-in-background
import appnope
from packaging.version import Version


def requires_appnope() -> bool:
    """Used to check if `appnope` is necessary."""
    # extracted from `appnope` source
    return (sys.platform == "darwin") and Version(platform.mac_ver()[0]) > Version(
        "10.9"
    )


def refresh_nope() -> None:
    """
    Communicate to the macOS that the process needs to stay awake
    and must not be sent to App Nap.

    This refresh needs to be triggered recurrently (e.g. QtCore.QTimer)
    """
    appnope.nope()
