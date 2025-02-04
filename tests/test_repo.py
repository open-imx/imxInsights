import os
import tempfile

import pytest

from imxInsights import ImxSingleFile, ImxContainer

from pandas import MultiIndex


def test_imx_parse_project_v124(imx_v124_project_instance: ImxSingleFile):
    imx = imx_v124_project_instance
    assert imx.file.imx_version == "1.2.4", "imx version should be 1.2.4"
    assert (
        len(list(imx.initial_situation.get_all())) == 5600
    ), "should have x objects in tree"
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


def test_imx_repo_dataframes_v124(imx_v124_project_instance: ImxSingleFile):
    imx = imx_v124_project_instance
    df_types = imx.initial_situation.get_pandas_df(["Signal"])
    assert len(df_types) == 166, "Should be x Signals"
    df_type_and_paths = imx.initial_situation.get_pandas_df(["Signal", "Signal.IlluminatedSign"])
    assert len(df_type_and_paths) == 200, "Should be x Signals"

    df_all = imx.initial_situation.get_pandas_df()
    assert len(df_all) == 5600, "Dataframe should contain x objects"

    df_types_dict = imx.initial_situation.get_pandas_df_dict()
    assert len(df_types_dict) == 73, "Should be x Objects"

    df_overview = imx.initial_situation.get_pandas_df_overview()
    assert isinstance(df_overview.index, MultiIndex), "Overview should be multi index."
    assert df_overview.index.nlevels == 5, "Index should have x levels"
    assert len(df_overview) == 5600

def test_imx_repo_geojson_v124(imx_v124_project_instance: ImxSingleFile):
    imx = imx_v124_project_instance
    wgs_geojson = imx.initial_situation.get_geojson(["Signal", "Signal.IlluminatedSign"])
    assert wgs_geojson.crs.name == "WGS84", "should have crs x"
    assert len(wgs_geojson.features) == 200, "should have x features"

    rd_geojson = imx.initial_situation.get_geojson(["Signal", "Signal.IlluminatedSign"], to_wgs=False)
    assert rd_geojson.crs.name == "RD_NEW_NAP", "should have crs x"
    assert len(rd_geojson.features) == 200, "should have x features"

    with tempfile.TemporaryDirectory() as temp_dir:
        imx.initial_situation.create_geojson_files(temp_dir)
        file_count = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
        assert file_count == 73, "Should have x geojson files"


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
    puic_to_find = "65ccaade-e1c7-43e8-975b-e377951ba621"
    assert imx.find(puic_to_find).puic == puic_to_find, "Should return x object"
    assert len(list(imx.get_all())) == 302, "objects in tree should is off"
    assert len(imx.get_build_exceptions()) == 6, "should have x exceptions"
    assert imx.project_metadata is not None, "Should have project metadata"


def test_imx_repo_queries_v1200(imx_v1200_zip_instance: ImxContainer):
    imx = imx_v1200_zip_instance
    assert len(list(imx.get_by_types(["Signal"]))) == 1, "should have x objects in tree"
    assert len(list(imx.get_by_paths(["Signal", "Signal.IlluminatedSign"]))) == 2, "should have x objects in tree"


def test_imx_repo_dataframes_v1200(imx_v1200_zip_instance: ImxContainer):
    imx = imx_v1200_zip_instance
    df = imx.get_pandas_df(["Signal"])
    assert len(df) == 1, "Should contain x objects"

    df_type_and_paths = imx.get_pandas_df(["Signal", "Signal.IlluminatedSign"])
    assert len(df_type_and_paths) == 2, "Should contain x objects"

    df_all = imx.get_pandas_df()
    assert len(df_all) == 302, "Should contain x objects"

    df_overview = imx.get_pandas_df_overview()
    assert isinstance(df_overview.index, MultiIndex), "Overview should be multi index."
    assert df_overview.index.nlevels == 5, "Index should have x levels"
    assert len(df_overview) == 302, "Should contain x objects"


def test_imx_repo_geojson_v1200(imx_v1200_zip_instance: ImxContainer):
    imx = imx_v1200_zip_instance
    wgs_geojson = imx.get_geojson(["Signal", "Signal.IlluminatedSign"])
    assert wgs_geojson.crs.name == "WGS84", "should have crs x"
    assert len(wgs_geojson.features) == 2, "should have x features"

    rd_geojson = imx.get_geojson(["Signal", "Signal.IlluminatedSign"], to_wgs=False)
    assert rd_geojson.crs.name == "RD_NEW_NAP", "should have crs x"
    assert len(rd_geojson.features) == 2, "should have x features"

    with tempfile.TemporaryDirectory() as temp_dir:
        imx.create_geojson_files(temp_dir)
        file_count = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
        assert file_count == 247, "Should have x geojson files"


def test_imx_parse_v1200_dir(imx_v1200_dir_instance: ImxContainer):
    imx = imx_v1200_dir_instance
    assert (
        imx.files.signaling_design.imx_version == "12.0.0"
    ), "imx version should be 12.0.0"
    assert len(list(imx.get_all())) == 302, "objects in tree should is off"
    # dir has one more extension course of mismatch on file hash for observations
    assert len(imx.get_build_exceptions()) == 7, "should have x exceptions"

