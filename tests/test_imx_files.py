import pytest

from imxInsights import ImxMultiRepo, ImxSingleFile, ImxContainer


@pytest.mark.slow
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


@pytest.mark.slow
def test_imx_multiple_same_extension_objects_v124(
    imx_v124_project_instance: ImxSingleFile,
):
    imx = imx_v124_project_instance
    switch_mech = imx.initial_situation.find("3d1c6832-ae71-4465-b32f-e79260450002")
    assert len(switch_mech.imx_extensions) == 2, "Should have x extensions"
    assert len(switch_mech.extension_properties) == 8, "Should have x extensions props"


@pytest.mark.slow
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


@pytest.mark.slow
def test_imx_multi_repo_v124(
    imx_v124_project_instance: ImxSingleFile,
    imx_v500_project_instance: ImxSingleFile,
    imx_v1200_zip_instance: ImxContainer,
):
    imx = imx_v124_project_instance
    imx_2 = imx_v500_project_instance
    imx_3 = imx_v1200_zip_instance

    # version same

    # version difference
    #  - fail if version safe is False
    #  - ok when version safe is True

    multi_situations = ImxMultiRepo(
        [
            imx.initial_situation,
            imx.new_situation,
            # imx_2.initial_situation #, imx_3],
        ],
        version_safe=False,
    )

    # more then 2 containers test

    compair = multi_situations.compair()
    print()


@pytest.mark.slow
def test_imx_parse_project_v500(imx_v500_project_instance):
    imx = imx_v500_project_instance
    assert imx.file.imx_version == "5.0.0", "imx version should be 5.0.0"
    assert (
        len(list(imx.initial_situation.get_all())) == 3689
    ), "objects in tree should is off"
    assert (
        len(imx.initial_situation.get_build_exceptions()) == 0
    ), "should not have no exceptions"
    assert imx.new_situation is None, "does not have a new situation"


@pytest.mark.slow
def test_imx_parse_v1200_zip(imx_v1200_zip_instance):
    imx = imx_v1200_zip_instance
    assert (
        imx.files.signaling_design.imx_version == "12.0.0"
    ), "imx version should be 12.0.0"
    assert len(list(imx.get_all())) == 302, "objects in tree should is off"
    assert len(imx.get_build_exceptions()) == 6, "should have x exceptions"


@pytest.mark.slow
def test_imx_parse_v1200_dir(imx_v1200_dir_instance):
    imx = imx_v1200_dir_instance
    assert (
        imx.files.signaling_design.imx_version == "12.0.0"
    ), "imx version should be 12.0.0"
    assert len(list(imx.get_all())) == 302, "objects in tree should is off"
    # dir has one more extension course of mismatch on file hash for observations
    assert len(imx.get_build_exceptions()) == 7, "should have x exceptions"
