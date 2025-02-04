import pytest

from imxInsights import ImxMultiRepo, ImxSingleFile
from imxInsights import ImxContainer


@pytest.fixture(scope="module")
def imx_v1200_multi_repo_instance(
    imx_v1200_dir_instance: ImxContainer,
    imx_v1200_zip_instance: ImxContainer
) -> ImxMultiRepo:
    return ImxMultiRepo(
        [
            imx_v1200_zip_instance,
            imx_v1200_dir_instance,
        ]
    )


@pytest.fixture(scope="module")
def imx_v1200_triple_multi_repo_instance(
    imx_v500_project_instance: ImxSingleFile,
    imx_v1200_zip_instance: ImxContainer,
    imx_v1200_dir_instance: ImxContainer,
) -> ImxMultiRepo:
    return ImxMultiRepo(
        [
            imx_v500_project_instance.initial_situation,
            imx_v1200_zip_instance,
            imx_v1200_dir_instance,
        ],
        version_safe=False
    )
