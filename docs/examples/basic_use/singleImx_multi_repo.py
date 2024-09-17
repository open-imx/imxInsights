from imxInsights import ImxMultiRepo, ImxSingleFile

imx = ImxSingleFile(r"path to xml file")

multi_repo = ImxMultiRepo([imx.initial_situation, imx.new_situation])
