# Repository: https://gitlab.com/quantify-os/quantify
# Licensed according to the LICENSE file on the main branch
"""Helpers for building docs."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import quantify.data.handling as dh
from quantify.utilities._tests_helpers import get_test_data_dir

if TYPE_CHECKING:
    from quantify.data.types import TUID


def create_tmp_dir_from_test_dataset(
    tuid: TUID,
) -> tuple[Path, tempfile.TemporaryDirectory]:
    """
    Creates a temporary directory and copies the test dataset into a folder under the
    corresponding date. After using the `tmp_dir` you should call `tmp_dir.cleanup()`.

    Intended to be used in the docs build when access to a dataset is handy.

    NB not intended for doc examples that users are supposed to be able to copy-paste
    and run themselves.

    Parameters
    ----------
    tuid
        Identifier of the experiment container that will be copied into the
        temporary directory.

    Returns
    -------
    tmp_path:
        A :class:`pathlib.Path` object pointing to the new directory to used as
        :code:`dh.set_datadir(tmp_path)`.
    tmp_dir:
        The :class:`tempfile.TemporaryDirectory` so that :code:`tmp_dir.cleanup()`
        can be called.

    """
    # not calling dh.get_datadir to avoid warning
    old_dir = dh._datadir  # type: ignore # pylint: disable=no-member
    dh.set_datadir(get_test_data_dir())
    exp_container = Path(dh.locate_experiment_container(tuid=tuid))
    if old_dir:
        dh.set_datadir(old_dir)

    tmp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
    tmp_path = Path(tmp_dir.name)
    date_dir_name = exp_container.parent.name

    shutil.copytree(
        exp_container, Path(tmp_dir.name) / date_dir_name / exp_container.name
    )

    return tmp_path, tmp_dir
