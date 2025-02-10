from imxInsights import ImxSingleFile, ImxContainer, ImxMultiRepo


imx_a = ImxSingleFile(r"path to xml file")
imx_b = ImxContainer(r"path to xml zip container or folder")

# create multi repo
multi_repo = ImxMultiRepo(
    [
        imx_a,
        imx_b,
    ],
    version_safe=False,
)

# # compare
# compared_imx = multi_repo.compare()
#
# # get object type specific diff dataframe
# track_diff_dataframe = compared_imx.get_pandas(object_type='Track')
#
# # optional add analyses and style
# track_diff_dataframe_colored = compared_imx.get_pandas(
#     object_type='Track', add_analyse=True, styled_df=True
# )
#
# # create excel
# compared_imx.create_excel(
#     file_path="diff_excel.xlsx",
#     add_analyse=True, styled_df=True
# )
#
# # get geojson feature collection from type
# feature_collection = compared_imx.get_geojson(
#     object_paths=["Signal", "Signal.ReflectorPost"]
# )
#
# # create geojson files
# compared_imx.create_geojson_files(directory_path="geojson_diff")
