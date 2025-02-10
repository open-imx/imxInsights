from imxInsights import ImxContainer, ImxMultiRepo


imx_a = ImxContainer(r"path to xml zip container or folder")
imx_b = ImxContainer(r"path to xml zip container or folder")

# create multi repo
multi_repo = ImxMultiRepo(
    [
        imx_a,
        imx_b,
    ]
)

# compare
compared_imx = multi_repo.compare(imx_a.container_id, imx_b.container_id)

# get object type specific diff dataframe
track_diff_dataframe = compared_imx.get_pandas(object_paths=['Track'])

# optional add analyses and style
track_diff_dataframe_colored = compared_imx.get_pandas(
    object_paths=['Track'], add_analyse=True, styled_df=True
)

# create excel
compared_imx.to_excel(
    file_name="diff_excel.xlsx",
    add_analyse=True, styled_df=True
)

# get geojson feature collection from type
feature_collection = compared_imx.get_geojson(
    object_paths=["Signal", "Signal.ReflectorPost"]
)

# create geojson files
compared_imx.create_geojson_files(directory_path="geojson_diff")
