from imxInsights import ImxContainer, ImxMultiRepo


imx_a = ImxContainer(r"path to xml zip container or folder")
imx_b = ImxContainer(r"path to xml zip container or folder")

# create multi repo
multi_repo = ImxMultiRepo(
    [
        imx_a,
        imx_b,
    ],
    version_safe=False,
)
# compare
compared_imx = multi_repo.compare()

# get object type specific diff dataframe
track_diff_dataframe = compared_imx.get_pandas('Track')

# optional add analyses and style
compared_imx.create_excel("diff_excel.xlsx", add_analyse=True, styled_df=True)