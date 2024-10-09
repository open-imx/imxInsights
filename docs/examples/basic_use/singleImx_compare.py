from imxInsights import ImxMultiRepo, ImxSingleFile


imx = ImxSingleFile(r"path to xml file")

# create multi repo
multi_repo = ImxMultiRepo(
    [
        imx.initial_situation,
        imx.new_situation,
    ],
    version_safe=False,
)
# compare
compared_imx = multi_repo.compare()

# get object type specific diff dataframe
track_diff_dataframe = compared_imx.get_pandas('Track')

# optional add analyses and style
compared_imx.create_excel("diff_excel.xlsx", add_analyse=True, styled_df=True)

