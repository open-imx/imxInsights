from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from imxInsights.repo.imxRepoProtocol import ImxRepoProtocol

if TYPE_CHECKING:
    from datetime import datetime

    from lxml.etree import _Element as Element

    from imxInsights.file.imxFile import ImxFile
    from imxInsights.file.singleFileImx.imxSingleFileMetadata import SingleImxMetadata
    from imxInsights.file.singleFileImx.imxSituationEnum import ImxSituationEnum
#    from imxInsights.report.singleImxPandasGenerator import SingleImxPandasGenerator


@runtime_checkable
class ImxSituationProtocol(ImxRepoProtocol, Protocol):
    _imx_file: ImxFile
    _element: Element
    reference_date: datetime | None
    perspective_date: datetime | None
    situation_type: ImxSituationEnum
    project_metadata: SingleImxMetadata | None


#    dataframes: SingleImxPandasGenerator
