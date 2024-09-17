from typing import Any

from imxInsights.exceptions.exceptionLevels import ErrorLevelEnum


class CustomException(Exception):
    """
    Custom exception class for handling errors with specific levels and optional data.

    ??? info
        This exception class allows for the specification of an error message,
        an error level (using the ErrorLevelEnum), and optional additional data
        that can provide more context about the error.

    Args:
        msg: The exception message.
        level: The error level of the exception.
        data: Optional additional data associated with the exception.
    """

    def __init__(
        self,
        msg: str,
        level: ErrorLevelEnum = ErrorLevelEnum.ERROR,
        data: Any | None = None,
    ) -> None:
        super().__init__(msg)
        self.msg = msg
        self.level = level
        self.data = data
