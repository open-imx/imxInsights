from imxInsights.file.containerizedImx.imxContainer import ImxContainer
from imxInsights.file.singleFileImx.imxSingleFile import ImxSingleFile

# from imxInsights.repo.imxMultiRepo import ImxMultiRepo

__version__ = "0.2.0-dev7"


class Imx:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "The 'Imx' class is deprecated in imxInsights v0.2. Use 'ImxContainer' for v12.0 and above else 'ImxSingleFile'."
        )


__all__ = [
    "ImxContainer",
    "ImxSingleFile",
    # "ImxMultiRepo",
]
