import os

import pytest

from quantify.utilities._tests_helpers import (
    get_test_data_dir,
    remove_target_then_copy_from,
    rmdir_recursive,
)

# Setting QT_QPA_PLATFORM to offscreen will disable insmon and plotmon popping up
# during pytest running. Comment this string out if you want to see them.
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="session", autouse=True)
def tmp_test_data_dir(request, tmp_path_factory):
    """
    This is a fixture which uses the pytest tmp_path_factory fixture
    and extends it by copying the entire contents of the test_data
    directory. After the test session is finished, then it calls
    the `cleaup_tmp` method which tears down the fixture and cleans up itself.
    """
    temp_data_dir = tmp_path_factory.mktemp("temp_data")
    remove_target_then_copy_from(source=get_test_data_dir(), target=temp_data_dir)

    def cleanup_tmp():
        rmdir_recursive(root_path=temp_data_dir)

    request.addfinalizer(cleanup_tmp)

    return temp_data_dir
