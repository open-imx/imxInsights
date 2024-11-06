import tempfile

import pytest

from imxInsights.compare.compareMultiRepo import ImxCompareMultiRepo
from imxInsights.file.containerizedImx.imxContainer import ImxContainer
from imxInsights.repo.imxMultiRepo import ImxMultiRepo
from imxInsights.file.singleFileImx.imxSingleFile import ImxSingleFile


@pytest.mark.slow
def create_excel(compared_imx: ImxCompareMultiRepo):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".xlsx") as temp_file:
        compared_imx.create_excel(temp_file.name, styled_df=True, add_analyse=True)

@pytest.mark.slow
def test_v124_v500(
    imx_v124_project_instance: ImxSingleFile,
    imx_v500_project_instance: ImxSingleFile,
):
    multi_repo = ImxMultiRepo(
        [
            imx_v124_project_instance.initial_situation,
            imx_v500_project_instance.initial_situation,
        ],
        version_safe=False,
    )
    compared_imx = multi_repo.compare()
    compared_imx.create_excel("v124-v500.xlsx", styled_df=True, add_analyse=True)
    # create_excel(compared_imx)


def test_v124_v1200_zip(
    imx_v124_project_instance: ImxSingleFile,
    imx_v1200_zip_instance: ImxContainer,
):
    multi_repo = ImxMultiRepo(
        [
            imx_v124_project_instance.initial_situation,
            imx_v1200_zip_instance,
        ],
        version_safe=False,
    )
    compared_imx = multi_repo.compare()
    compared_imx.create_excel("v1200_zip.xlsx", styled_df=True, add_analyse=True)
    # create_excel(compared_imx)


def test_v124_v1200_folder(
    imx_v124_project_instance: ImxSingleFile,
    imx_v1200_dir_instance: ImxContainer,
):
    multi_repo = ImxMultiRepo(
        [
            imx_v124_project_instance.initial_situation,
            imx_v1200_dir_instance,
        ],
        version_safe=False,
    )
    compared_imx = multi_repo.compare()
    compared_imx.create_excel("v1200_folder.xlsx", styled_df=True, add_analyse=True)
    # create_excel(compared_imx)
