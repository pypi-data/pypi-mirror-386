# Repository: https://gitlab.com/quantify-os/quantify
# Licensed according to the LICENSE file on the main branch
"""Helpers for testing quantify."""

import os
import pathlib
import shutil


def get_test_data_dir() -> pathlib.PosixPath | pathlib.WindowsPath:
    """
    Returns the path to the `test_data` directory inside the repository.

    Intended for development purposes.
    """
    return pathlib.Path(__file__).parent.parent.parent.resolve() / "tests" / "test_data"  # type: ignore


def rmdir_recursive(root_path) -> None:  # noqa: ANN001
    """
    Recursively removes the directory defined by 'root_path' and all the
    contents inside the directory.

    Parameters
    ----------
    root_path :
        path of the directory to be removed.

    """
    if os.path.exists(root_path):
        shutil.rmtree(root_path)


def remove_target_then_copy_from(source, target) -> None:  # noqa: ANN001
    """
    Removes the target directory before copying the entire
    content of the source directory to the target.

    Parameters
    ----------
    source :
        path of the source directory.
    target :
        path of the target directory

    """
    rmdir_recursive(target)
    shutil.copytree(source, target)
