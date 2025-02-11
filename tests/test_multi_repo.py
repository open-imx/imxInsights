import os
import shutil
import tempfile
from pathlib import Path

import pytest

from imxInsights import ImxMultiRepo, ImxContainer, ImxSingleFile
from imxInsights.domain.imxObject import ImxObject


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
    multi_repo = ImxMultiRepo(
        [
            imx_v1200_zip_instance,
            imx_v1200_dir_instance,
        ]
    )
    assert multi_repo.get_container(imx_v1200_zip_instance.container_id).container_id == imx_v1200_zip_instance.container_id, "Should be same id"
    assert len(multi_repo.get_all()) == 302, "Should be x items"
    assert len(multi_repo.get_all_types()) == 240, "Should be x items"
    assert len(multi_repo.get_by_types(["ReflectorPost"])) == 2, "Should be x items"
    assert len(multi_repo.get_all_paths()) == 247, "Should be x items"
    assert len(multi_repo.get_by_paths(["Signal.ReflectorPost"])) == 2, "Should be x items"


def test_multi_repo_geojson(
    imx_v1200_zip_instance: ImxContainer,
    imx_v1200_dir_instance: ImxContainer,
    imx_v1200_multi_repo_instance: ImxMultiRepo
):
    multi_repo = imx_v1200_multi_repo_instance
    result = multi_repo.get_geojson(["Signal"], imx_v1200_dir_instance.container_id, as_wgs=False)
    assert len(result.features) == 1, "Should be x features"
    assert len(result.features[0].properties) == 28, "Should have x properties"

    result = multi_repo.get_geojson(["Signal"], imx_v1200_zip_instance.container_id, as_wgs=False)
    assert result.crs.name == "RD_NEW_NAP", "Should x crs"

    result = multi_repo.get_geojson(["SingleSwitch"], imx_v1200_dir_instance.container_id, as_wgs=False, extension_properties=True)
    assert 'extension.MicroNode.@junctionRef' in result.features[0].properties.keys(), "Should have extension properties"

    temp_dir = Path("test-multirepo-geojson")
    temp_dir.mkdir(exist_ok=True)

    for container_id in [imx_v1200_dir_instance.container_id, imx_v1200_zip_instance.container_id]:
        with tempfile.TemporaryDirectory() as temp_dir:
            multi_repo.create_geojson_files(temp_dir, container_id)
            file_count = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
            assert file_count == 247, "Should have x geojson files"


def test_multi_repo_dataframe(
    imx_v1200_multi_repo_instance: ImxMultiRepo
):
    multi_repo = imx_v1200_multi_repo_instance
    result = multi_repo.get_pandas(types=["Signal", "Sign"], paths=["Signal.ReflectorPost"])
    assert len(result) == 10, "Should have x entries"
    result = multi_repo.get_pandas(types=["Signal", "Sign"], paths=["Signal.ReflectorPost"], pivot_df=True)
    assert result.index.nlevels == 3, "Index should have x levels"

    result = multi_repo.get_pandas(["Signal"])
    assert len(result) == 2, "Should have x entries"

    assert len(multi_repo.get_pandas_dict().keys()) == 247, "Should have x paths"


def test_multi_repo_object(
    imx_v1200_triple_multi_repo_instance: ImxMultiRepo,
    imx_v500_project_instance: ImxSingleFile,
    imx_v1200_zip_instance: ImxContainer,
    imx_v1200_dir_instance: ImxContainer,
):
    multi_repo = imx_v1200_triple_multi_repo_instance
    imx_multi_object = multi_repo.find("65ccaade-e1c7-43e8-975b-e377951ba621")
    assert len(imx_multi_object.container_order) == 3, "should have 2 containers"
    assert len(imx_multi_object.imx_objects) == 3, "should have 2 imx objects"

    result = imx_multi_object.compare(imx_v500_project_instance.initial_situation.container_id, imx_v1200_zip_instance.container_id)
    assert len(result.changes) == 40, "Should be x changes"
    assert result.geometry.status.name == "ADDED", "Geometry should added"
    assert isinstance(result.t2, ImxObject), "Should be ImxObject"

    result = imx_multi_object.compare(imx_v1200_zip_instance.container_id, imx_v1200_dir_instance.container_id)
    assert len(result.changes) == 40, "Should be x changes"
    assert len(result.get_change_dict(add_analyse=True).keys()) == 42, "Should contain x properties"

    assert result.changes['extension.ObservedLocation.@surveyRef'].status.name == "REMOVED", "observe location should be removed"
    assert result.changes['@signalType'].status.name == "UNCHANGED", "Signal type should be unchanged"
    assert result.geometry.status.name == 'UNCHANGED', "Geometry should be unchanged"
    assert result.status.name == 'CHANGED', "Global stat should be changed"

    compare_list = imx_multi_object.compare_list()
    assert len(compare_list) == 2, "Should be 2 diffs in list"
    assert compare_list[0].t1 is None, "t1 should not have a container"
    assert compare_list[0].t2.container_id == imx_v1200_zip_instance.container_id, "Should be 2th container id"

    assert compare_list[1].t1.container_id == imx_v1200_zip_instance.container_id, "Should be 2th container id"
    assert compare_list[1].t2.container_id == imx_v1200_dir_instance.container_id, "Should be 3th container id"

