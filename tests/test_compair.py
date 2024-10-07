import os

import pytest

from imxInsights import ImxMultiRepo, ImxSingleFile, ImxContainer
from imxInsights.compair.compairMultiRepo import ImxCompareMultiRepo


def create_excel(compared_imx: ImxCompareMultiRepo, remove_when_done: bool = False):
    output_file = "temp_diff_excel.xlsx"
    try:
        compared_imx.create_excel(output_file)
    finally:
        if remove_when_done and os.path.exists(output_file):
            os.remove(output_file)


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

    compared_imx = multi_repo.compair()
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
    compared_imx = multi_repo.compair()
    create_excel(compared_imx)








#
# @pytest.mark.slow
# def test_imx_multi_repo_v500(
#     imx_v500_project_instance: ImxSingleFile,
# ):
#     try:
#         ImxMultiRepo(
#             [
#                 imx_v500_project_instance.initial_situation,
#                 imx_v500_project_instance.initial_situation,
#             ],
#             version_safe=False,
#         )
#     except Exception as e:
#         pytest.fail(f"Unexpected exception occurred: {e}")
#
#
# @pytest.mark.slow
# def test_imx_multi_repo_v1200(
#     imx_v1200_zip_instance: ImxContainer,
# ):
#     try:
#         ImxMultiRepo(
#             [
#                 imx_v1200_zip_instance,
#                 imx_v1200_zip_instance,
#             ],
#             version_safe=False,
#         )
#     except Exception as e:
#         pytest.fail(f"Unexpected exception occurred: {e}")
#


# def test_imx_multi_repo_v1200(
#         imx_v124_project_instance: ImxSingleFile,
#
# ):
#     imx_v1200_zip_instance: ImxContainer,
#     imx_3 = imx_v1200_zip_instance
#
#



# @pytest.mark.slow
# def test_imx_multi_repo_v124(
#     imx_v124_project_instance: ImxSingleFile,
#
# ):
#     imx = imx_v124_project_instance
#
#
#     # version difference
#     #  - fail if version safe is False
#     #  - ok when version safe is True
#
#     multi_situations = ImxMultiRepo(
#         [
#             imx.initial_situation,
#             imx.new_situation,
#             # imx_2.initial_situation #, imx_3],
#         ],
#         version_safe=False,
#     )
#
#     # more then 2 containers test
#
#     compair = multi_situations.compair()
#
#     # excek
#
