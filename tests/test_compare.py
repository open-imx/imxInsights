import os
import tempfile

import pytest


from imxInsights import ImxMultiRepo, ImxSingleFile, ImxContainer
from imxInsights.compare.compareMultiRepo import ImxCompareMultiRepo
from pandas import DataFrame


def create_excel(compared_imx: ImxCompareMultiRepo):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".xlsx") as temp_file:
        compared_imx.create_excel(temp_file.name, styled_df=True, add_analyse=True)

@pytest.mark.slow
def test_imx_multi_repo_different_versions(
    imx_v124_project_instance: ImxSingleFile,
    imx_v500_project_instance: ImxSingleFile,
):
    # todo: replace testdata with overlapping imx files, v124 amd v1200.

    with pytest.raises(ValueError):
        ImxMultiRepo(
            [
                imx_v124_project_instance.initial_situation,
                imx_v500_project_instance.initial_situation,
            ],
            version_safe=True,
        )

    multi_repo = ImxMultiRepo(
        [
            imx_v124_project_instance.initial_situation,
            imx_v500_project_instance.initial_situation,
        ],
        version_safe=False,
    )

    assert multi_repo.container_order[0] == imx_v124_project_instance.initial_situation.container_id, "wrong container id order"
    assert multi_repo.container_order[1] == imx_v500_project_instance.initial_situation.container_id, "wrong container id order"
    assert len(multi_repo.containers) == 2, "should contain x containers"
    assert len(multi_repo._tree.build_extensions.exceptions) == 0, "should not have build errors"
    assert len(multi_repo._tree.keys) == 9289, "Count of keys in tree not correct"
    assert len(multi_repo._tree.tree_dict.keys()) == 9289, "Count of items in tree dict not correct"

    compared_imx = multi_repo.compare()
    assert compared_imx.container_order[0] == imx_v124_project_instance.initial_situation.container_id, "wrong container id order"
    assert compared_imx.container_order[1] == imx_v500_project_instance.initial_situation.container_id, "wrong container id order"

    assert len(compared_imx.diff["SingleSwitch"]) == 154, "Should contain x SingleSwitchs"
    assert len(compared_imx.diff["Signal"]) == 299, "Should contain x Signal"

    assert len([item for item in compared_imx.diff["SingleSwitch"] if item.status.value == 'removed']) == 88, "Should be x removed"
    assert len([item for item in compared_imx.diff["SingleSwitch"] if item.status.value == 'added']) == 66, "Should be x added"

    create_excel(compared_imx)


@pytest.mark.slow
def test_imx_multi_repo_v124(
    imx_v124_project_instance: ImxSingleFile,
):
    multi_repo = ImxMultiRepo(
        [
            imx_v124_project_instance.initial_situation,
                imx_v124_project_instance.new_situation,
        ],
        version_safe=False,
    )
    compared_imx = multi_repo.compare()
    create_excel(compared_imx)


@pytest.mark.slow
def test_compair_as_pandas(
        imx_v124_project_instance: ImxSingleFile,
):
    multi_repo = ImxMultiRepo(
        [
            imx_v124_project_instance.initial_situation,
                imx_v124_project_instance.new_situation,
        ],
        version_safe=False,
    )
    # this takes to long,...  async?
    compared_imx = multi_repo.compare()

    normal = compared_imx.get_pandas()
    assert len(normal.keys()) == 75, "Should contain x object types"
    assert isinstance(normal['ATBNGBeacon'], DataFrame), "Should be a pd dataframe"

    including_analyse = compared_imx.get_pandas(add_analyse=True)
    assert isinstance(including_analyse['ATBNGBeacon'], DataFrame), "Should be a pd dataframe"
    analyse_columns = including_analyse['ATBNGBeacon'].columns[including_analyse['ATBNGBeacon'].columns.str.endswith('analyse')]
    assert len(analyse_columns) == 1 , "should contain x columns ending with analyse"

    styled_df = compared_imx.get_pandas(styled_df=True)
    assert isinstance(styled_df['ATBNGBeacon'].data, DataFrame), "Should be a pd dataframe"
    assert hasattr(styled_df['ATBNGBeacon'], 'css'), "Styler object should have css attribute"
