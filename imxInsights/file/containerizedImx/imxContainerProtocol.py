from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from imxInsights.repo.imxRepoProtocol import ImxRepoProtocol

if TYPE_CHECKING:
    from imxInsights.file.containerizedImx.imxContainerFiles import ImxContainerFiles
    from imxInsights.file.containerizedImx.imxContainerMetadata import (
        ImxContainerMetadata,
    )

    # from imxInsights.report.containerImxPandasGenerator import (
    #     ContainerImxPandasGenerator,
    # )


@runtime_checkable
class ImxContainerProtocol(ImxRepoProtocol, Protocol):
    _input_file_path: Path
    files: ImxContainerFiles
    project_metadata: ImxContainerMetadata | None


#    dataframes: ContainerImxPandasGenerator
