import sys
from datetime import datetime

from loguru import logger
from tqdm import tqdm

from imxInsights.file.containerizedImx.imxContainerProtocol import ImxContainerProtocol
from imxInsights.repo.imxMultiRepoObject import ImxMultiRepoObject


class ComparedMultiRepo:
    def __init__(
        self,
        container_1: ImxContainerProtocol,
        container_2: ImxContainerProtocol,
        compared_objects: list[ImxMultiRepoObject],
    ):
        self.container_1 = container_1
        self.container_2 = container_2
        self.compared_objects = []

        with tqdm(total=len(compared_objects), file=sys.stdout) as pbar:  # type: ignore
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            pbar.set_description(
                f"{current_time} | {logger.level('INFO').name}     | Comparing objects"
            )
            for item in compared_objects:
                self.compared_objects.append(
                    item.compare(container_1.container_id, container_2.container_id)
                )
                pbar.update(1)
        logger.success("Compared all objects.")

    # todo: get dataframe

    # todo: get dataframe dict

    # todo: get excel
