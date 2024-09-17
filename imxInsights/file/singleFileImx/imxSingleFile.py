from pathlib import Path

from loguru import logger

from imxInsights.file.imxFile import ImxFile
from imxInsights.file.singleFileImx.imxSituation import ImxSituation


class ImxSingleFile:
    """
    Represents an IMX file that contains project situations or just a situation.

    Args:
        imx_file_path: Path to the IMX container.

    Attributes:
        file: The IMX file.
        situation: The IMX Situation.
        new_situation: The IMX NewSituation.
        initial_situation: The IMX InitialSituation.

    """

    def __init__(self, imx_file_path: Path | str):
        imx_file_path = Path(imx_file_path)
        logger.info(f"processing {imx_file_path.name}")

        self.file: ImxFile = ImxFile(imx_file_path=imx_file_path)
        self.situation: ImxSituation | None = None
        self.new_situation: ImxSituation | None = None
        self.initial_situation: ImxSituation | None = None

        for situation_type, attribute_name in [
            ("Situation", "situation"),
            ("InitialSituation", "initial_situation"),
            ("NewSituation", "new_situation"),
        ]:
            if self.file.root is not None:
                situation = self.file.root.find(
                    f".//{{http://www.prorail.nl/IMSpoor}}{situation_type}"
                )
                if situation is not None:
                    imx_situation = ImxSituation(imx_file_path, situation, self.file)
                    setattr(self, attribute_name, imx_situation)

        logger.success(f"finished processing {self.file.path.name}")
