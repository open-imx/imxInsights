import pandas as pd
import pytest

from imxInsights import ImxSingleFile, ImxContainer
from imxInsights.repo.imxMultiRepo import ImxMultiRepo


# TODO: add get GEOJSON and GEOJSON WRITE TO FILES


def test_imx_parse_project_v124(imx_v124_project_instance: ImxSingleFile):
    imx = imx_v124_project_instance
    assert imx.file.imx_version == "1.2.4", "imx version should be 1.2.4"
    assert (
        len(list(imx.initial_situation.get_all())) == 5600
    ), "objects in tree should is off"
    assert (
        len(imx.initial_situation.get_build_exceptions()) == 0
    ), "should not have no exceptions"
    assert (
        len(list(imx.new_situation.get_all())) == 5725
    ), "objects in tree should is off"
    assert (
        len(imx.new_situation.get_build_exceptions()) == 0
    ), "should not have no exceptions"


def test_imx_multiple_same_extension_objects_v124(
    imx_v124_project_instance: ImxSingleFile,
):
    imx = imx_v124_project_instance
    switch_mech = imx.initial_situation.find("3d1c6832-ae71-4465-b32f-e79260450002")
    assert len(switch_mech.imx_extensions) == 2, "Should have x extensions"
    assert len(switch_mech.extension_properties) == 8, "Should have x extensions props"


def test_imx_repo_queries_v124(imx_v124_project_instance: ImxSingleFile):
    imx = imx_v124_project_instance
    assert len(list(imx.initial_situation.get_all())) == 5600, "Should have x objects"

    types_in_repo = imx.initial_situation.get_types()
    assert len(types_in_repo) == 60, "Should be x types"
    assert (
        len(imx.initial_situation.get_by_types(["Signal"])) == 166
    ), "Should be x Signals"

    paths_in_repo = imx.initial_situation.get_all_paths()
    assert len(paths_in_repo) == 73, "Should be x paths"
    assert (
        len(imx.initial_situation.get_by_paths(["Signal.IlluminatedSign"])) == 34
    ), "Should be x Signals.IlluminatedSign"

    assert (
        len(imx.initial_situation.get_pandas_df("Signal")) == 166
    ), "Should be x Signals"
    assert len(imx.initial_situation.get_pandas_df_dict()) == 73, "Should be x Objects"


def test_imx_parse_project_v500(imx_v500_project_instance: ImxSingleFile):
    imx = imx_v500_project_instance
    assert imx.file.imx_version == "5.0.0", "imx version should be 5.0.0"
    assert (
        len(list(imx.initial_situation.get_all())) == 3689
    ), "objects in tree should is off"
    assert (
        len(imx.initial_situation.get_build_exceptions()) == 0
    ), "should not have no exceptions"
    assert imx.new_situation is None, "does not have a new situation"


def test_imx_parse_v1200_zip(imx_v1200_zip_instance: ImxContainer):
    imx = imx_v1200_zip_instance
    assert (
        imx.files.signaling_design.imx_version == "12.0.0"
    ), "imx version should be 12.0.0"
    assert len(list(imx.get_all())) == 302, "objects in tree should is off"
    assert len(imx.get_build_exceptions()) == 6, "should have x exceptions"


def test_imx_parse_v1200_dir(imx_v1200_dir_instance: ImxContainer):
    imx = imx_v1200_dir_instance
    assert (
        imx.files.signaling_design.imx_version == "12.0.0"
    ), "imx version should be 12.0.0"
    assert len(list(imx.get_all())) == 302, "objects in tree should is off"
    # dir has one more extension course of mismatch on file hash for observations
    assert len(imx.get_build_exceptions()) == 7, "should have x exceptions"


def test_multi_repo(imx_v500_project_instance: ImxSingleFile, imx_v1200_zip_instance: ImxContainer):
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

    assert len(multi_repo.container_order) == 2, "Should have x containers_ids"
    assert len(multi_repo.containers) == 2, "Should have x containers"
    assert len(multi_repo.tree_dict.keys()) == 3991, "Should have x tree items"
    assert len(multi_repo.tree_dict.keys()) == len(multi_repo._keys), "Tree and keys should match"
    assert len(next(iter(multi_repo.tree_dict.values()))) == 2, "Should have x imx objects"

    assert len(multi_repo.get_all()) == len(multi_repo._keys), "Get all and keys should match"

    imx_multi_repo_object = multi_repo.find(list(multi_repo.tree_dict.keys())[0])
    assert len(imx_multi_repo_object.imx_objects) == 2, "Should have 2 items"
    assert len(imx_multi_repo_object.container_order) == 2, "Should have x containers_ids"

    assert len(list(multi_repo.get_all_types())) == 240, "Should have x object types"
    assert len(multi_repo.get_by_types(["Signal"])) == 134, "Should have x object types"
    assert len(multi_repo.get_by_types(["Signal", "IlluminatedSign"])) == 153, "Should have x object types"

    assert len(list(multi_repo.get_all_paths())) == 252, "Should have x imx paths"
    assert len(list(multi_repo.get_by_paths(["Signal.IlluminatedSign"]))) == 19, "Should have x imx paths items"
    assert len(list(multi_repo.get_by_paths(["Signal", "Signal.IlluminatedSign"]))) == 153, "Should have x imx paths items"

    df = multi_repo.get_pandas_df(paths=["CivilConstruction"], pivot_df=True)
    assert df.shape == (4, 25), "Dataframe should be x, x"

    df_a = multi_repo.get_pandas_df(paths=["AtbVvInstallation"])
    assert df_a.shape == (27, 17), "Dataframe should be x, x"

    df_b = multi_repo.get_pandas_df(
        types=["Signal", "Sign"], paths=["SingleSwitch.SwitchMechanism.Lock"]
    )
    assert df_b.shape == (393, 45), "Dataframe should be x, x"

    df_pivot = multi_repo.get_pandas_df(
        types=["Signal", "Sign"], paths=["SingleSwitch.SwitchMechanism.Lock"], pivot_df=True
    )
    assert df_pivot.shape == (393, 42), "Dataframe should be x, x"
    assert len(df_pivot.index.names) == 3, "Dataframe should have 3 index columns"

    df_dict = multi_repo.get_pandas_df_dict()
    assert len(df_dict.keys()) == 252, "Dataframe dict should contain x object types"
    for value in df_dict.values():
        assert isinstance(value, pd.DataFrame)
