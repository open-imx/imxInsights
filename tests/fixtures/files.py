import pytest

from tests.helpers import sample_path


@pytest.fixture(scope="module")
def imx_v124_project_test_file_path() -> str:
    return sample_path("124/basic_124.xml")


@pytest.fixture(scope="module")
def imx_v500_project_test_file_path() -> str:
    return sample_path("500/basic_500.xml")


@pytest.fixture(scope="module")
def imx_v1200_test_zip_file_path() -> str:
    return sample_path("1200/set 1 as zip.zip")


@pytest.fixture(scope="module")
def imx_v1200_test_dir_file_path() -> str:
    return sample_path("1200/set_1")
