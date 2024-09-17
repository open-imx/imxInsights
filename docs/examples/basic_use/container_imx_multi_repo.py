from imxInsights import ImxContainer, ImxMultiRepo

imx_a = ImxContainer(r"path to xml zip container or folder")
imx_b = ImxContainer(r"path to xml zip container or folder")

multi_repo = ImxMultiRepo([imx_a, imx_b])
