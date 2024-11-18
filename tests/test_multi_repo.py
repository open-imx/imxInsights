import pytest
from imxInsights import ImxMultiRepo, ImxContainer, ImxSingleFile


def test_multi_repo_version_safe(
    imx_v1200_zip_instance: ImxContainer,
    imx_v1200_dir_instance: ImxContainer
):
    multi_repo = ImxMultiRepo(
        [
            imx_v1200_zip_instance,
            imx_v1200_dir_instance,
        ]
    )

    assert multi_repo.container_order[0] == imx_v1200_zip_instance.container_id, "wrong container id order"
    assert multi_repo.container_order[1] == imx_v1200_dir_instance.container_id, "wrong container id order"
    assert len(multi_repo.containers) == 2, "should contain x containers"
    assert len(multi_repo._keys) == 302, "Count of keys in tree not correct"
    assert len(multi_repo.tree_dict.keys()) == 302, "Count of items in tree dict not correct"


def test_multi_repo_version_un_safe(
    imx_v500_project_instance: ImxSingleFile,
    imx_v1200_zip_instance: ImxContainer,
):
    with pytest.raises(ValueError):
        ImxMultiRepo(
            [
                imx_v500_project_instance.initial_situation,
                imx_v1200_zip_instance,
            ],
            version_safe=True,
        )

    multi_repo = ImxMultiRepo(
        [
            imx_v500_project_instance.initial_situation,
            imx_v1200_zip_instance,
        ],
        version_safe=False,
    )

    assert multi_repo.container_order[0] == imx_v500_project_instance.initial_situation.container_id, "wrong container id order"
    assert multi_repo.container_order[1] == imx_v1200_zip_instance.container_id, "wrong container id order"
    assert len(multi_repo.containers) == 2, "should contain x containers"
    assert len(multi_repo._keys) == 3991, "Count of keys in tree not correct"
    assert len(multi_repo.tree_dict.keys()) == 3991, "Count of items in tree dict not correct"


def test_multi_repo_queries(
    imx_v1200_zip_instance: ImxContainer,
    imx_v1200_dir_instance: ImxContainer
):
    pass


def test_multi_repo_geojson(
    imx_v1200_zip_instance: ImxContainer,
    imx_v1200_dir_instance: ImxContainer
):
    pass
