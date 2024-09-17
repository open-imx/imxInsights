from typing import Any

from imxInsights.domain.imxObject import ImxObject
from imxInsights.exceptions.customException import CustomException
from imxInsights.exceptions.exceptionLevels import ErrorLevelEnum


class ImxException(CustomException):
    """
    IMX specific exception.

    ??? info
        This is a base exception class for IMX-related errors, allowing for a
        generic exception message and error level, along with optional additional data.

    Args:
        msg: The exception message.
        level: The error level of the exception.
        data: Optional additional data associated with the exception.
    """

    def __init__(
        self,
        msg: str = "Generic Imx Exception",
        level: ErrorLevelEnum = ErrorLevelEnum.ERROR,
        data: Any | None = None,
    ) -> None:
        super().__init__(msg, level, data)


class ImxUnconnectedExtension(ImxException):
    """
    Exception for unconnected IMX object extension.

    ??? info
        This exception is raised when an IMX object extension cannot be matched
        to an entity and is not connected. The additional data is expected to be an ImxObject.

    Args:
        msg: The exception message.
        level: The error level of the exception.
        data: Optional additional data associated with the exception, expected to be an ImxObject.
    """

    def __init__(
        self,
        msg: str = "Imx Exception object can not be matched to entity and is not connected",
        level: ErrorLevelEnum = ErrorLevelEnum.ERROR,
        data: ImxObject | None = None,
    ) -> None:
        super().__init__(msg, level, data)


class ImxDuplicatedPuicsInContainer(ImxException):
    """
    Exception for duplicated PUICs in a container.

    ??? info
        This exception is raised when there are duplicated PUICs in a container. The
        additional data is expected to be a list of the duplicated PUICs.

    Args:
        msg: The exception message.
        level: The error level of the exception.
        data: Optional additional data associated with the exception, expected to be a list.
    """

    def __init__(
        self,
        msg: str = "Duplicated puic in container",
        level: ErrorLevelEnum = ErrorLevelEnum.CRITICAL,
        data: list[Any] | None = None,
    ) -> None:
        super().__init__(msg, level, data)


class ImxRailConnectionRefNotPresent(ImxException):
    """
    Exception for missing PUICs in RailConnections.

    ??? info
        This exception is raised when building RailConnections and a PUIC is not present
        in the container. The additional data is expected to be a list of the missing PUICs.

    Args:
        msg: The exception message.
        level: The error level of the exception.
        data: Optional additional data associated with the exception, expected to be a list.
    """

    def __init__(
        self,
        msg: str = "puic not in container",
        level: ErrorLevelEnum = ErrorLevelEnum.ERROR,
        data: list[str] | None = None,
    ) -> None:
        super().__init__(msg, level, data)


class ImxTopologyExtensionNotPresent(ImxException):
    """
    Exception for missing PUICs in Topology Extensions.

    ??? info
        This exception is raised when building Topology Extensions and a PUIC is not
        present in the container. The additional data is expected to be a list of the missing PUICs.

    Args:
        msg: The exception message.
        level: The error level of the exception.
        data: Optional additional data associated with the exception, expected to be a list.
    """

    def __init__(
        self,
        msg: str = "puic not in container",
        level: ErrorLevelEnum = ErrorLevelEnum.ERROR,
        data: list[str] | None = None,
    ) -> None:
        super().__init__(msg, level, data)


class ImxRailConnectionMultiLinestring(ImxException):
    """
    Exception for PUICs present in multiple linestrings in RailConnections.

    ??? info
        This exception is raised when building RailConnections and a PUIC is present
        in multiple linestrings. The additional data is expected to be a list of the PUICs.

    Args:
        msg: The exception message.
        level: The error level of the exception.
        data: Optional additional data associated with the exception, expected to be a list.
    """

    def __init__(
        self,
        msg: str = "puic not in container",
        level: ErrorLevelEnum = ErrorLevelEnum.ERROR,
        data: list[str] | None = None,
    ) -> None:
        super().__init__(msg, level, data)
