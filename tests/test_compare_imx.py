import os
import shutil
import tempfile
from pathlib import Path

import pytest


from imxInsights import ImxMultiRepo, ImxSingleFile, ImxContainer
from pandas.io.formats.style import Styler

from tests.fixtures.imx_files import imx_v1200_zip_instance


@pytest.fixture(scope="module")
def multi_repo(imx_v124_project_instance, imx_v500_project_instance):
    with pytest.raises(ValueError):
        ImxMultiRepo(
            [
                imx_v124_project_instance.initial_situation,
                imx_v500_project_instance.initial_situation,
            ],
            version_safe=True,
        )

    return ImxMultiRepo(
        [
            imx_v124_project_instance.initial_situation,
            imx_v500_project_instance.initial_situation,
        ],
        version_safe=False,
    )

@pytest.fixture(scope="module")
def compared_multirepo(multi_repo):
    return multi_repo.compare(
        multi_repo.container_order[0],
        multi_repo.container_order[1],
    )


def test_container_order(multi_repo, imx_v124_project_instance, imx_v500_project_instance):
    assert multi_repo.container_order[0] == imx_v124_project_instance.initial_situation.container_id, "Wrong container ID order"
    assert multi_repo.container_order[1] == imx_v500_project_instance.initial_situation.container_id, "Wrong container ID order"


def test_container_count(multi_repo):
    assert len(multi_repo.containers) == 2, "MultiRepo should contain 2 containers"


def test_keys_count(multi_repo, compared_multirepo):
    assert len(multi_repo._keys) == 9289, "Incorrect number of keys in multi-repo"
    assert len(multi_repo._keys) == len(compared_multirepo.compared_objects), "Compared objects count should match key count"


# def test_overview_dataframe(compared_multirepo):
#     overview = compared_multirepo.get_overview_df()
#     assert isinstance(overview, Styler), "Overview should be a Pandas Styler object"
#     assert overview.data.shape == (9289, 8), "Incorrect overview dataframe shape"



def test_create_geojson_files(compared_multirepo):
    with tempfile.TemporaryDirectory() as temp_dir:
        compared_multirepo.create_geojson_files(temp_dir)
        # created_files = [f for f in os.listdir(temp_dir) if f.endswith(".geojson")]
        # assert len(created_files) == 93, "Incorrect number of GeoJSON files created"


def test_create_excel(compared_multirepo):
    compared_multirepo.to_excel("diff.xlsx")
    os.remove("diff.xlsx")


@pytest.fixture(scope="module")
def multi_repo_timeline(imx_v124_project_instance, imx_v500_project_instance, imx_v1200_zip_instance):
    return ImxMultiRepo(
        [
            imx_v124_project_instance.initial_situation,
            imx_v500_project_instance.initial_situation,
            imx_v1200_zip_instance
        ],
        version_safe=False,
    )

@pytest.fixture(scope="module")
def compared_multirepo_timeline(multi_repo_timeline):
    """Create an ImxMultiRepo and perform the comparison once."""

    return multi_repo_timeline.compare_chain(
        [
            (multi_repo_timeline.container_order[0], multi_repo_timeline.container_order[1]),
            (multi_repo_timeline.container_order[1], multi_repo_timeline.container_order[2])
        ]
    )



def test_chain_excel(compared_multirepo_timeline):
    compared_multirepo_timeline.to_excel("timeline.xlsx")
    os.remove("timeline.xlsx")







# @pytest.mark.slow
# def test_imx_multi_repo_v124(
#     imx_v124_project_instance: ImxSingleFile,
# ):
#     multi_repo = ImxMultiRepo(
#         [
#             imx_v124_project_instance.initial_situation,
#                 imx_v124_project_instance.new_situation,
#         ],
#         version_safe=False,
#     )
#     compared_imx = multi_repo.compare()
#     # create_excel(compared_imx)
#
#
# @pytest.mark.slow
# def test_compair_as_pandas(
#         imx_v124_project_instance: ImxSingleFile,
# ):
#     multi_repo = ImxMultiRepo(
#         [
#             imx_v124_project_instance.initial_situation,
#                 imx_v124_project_instance.new_situation,
#         ],
#         version_safe=False,
#     )
#     # this takes to long,...  async?
#     compared_imx = multi_repo.compare()
#
#     normal = compared_imx.get_pandas()
#     assert len(normal.keys()) == 75, "Should contain x object types"
#     assert isinstance(normal['ATBNGBeacon'], DataFrame), "Should be a pd dataframe"
#
#     including_analyse = compared_imx.get_pandas(add_analyse=True)
#     assert isinstance(including_analyse['ATBNGBeacon'], DataFrame), "Should be a pd dataframe"
#     analyse_columns = including_analyse['ATBNGBeacon'].columns[including_analyse['ATBNGBeacon'].columns.str.endswith('analyse')]
#     assert len(analyse_columns) == 1 , "should contain x columns ending with analyse"
#
#     styled_df = compared_imx.get_pandas(styled_df=True)
#     assert isinstance(styled_df['ATBNGBeacon'].data, DataFrame), "Should be a pd dataframe"
#     assert hasattr(styled_df['ATBNGBeacon'], 'css'), "Styler object should have css attribute"
