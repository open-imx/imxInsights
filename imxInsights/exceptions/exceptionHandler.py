import datetime
import re

from loguru import logger

from imxInsights.domain.imxObject import ImxObject
from imxInsights.exceptions.customException import CustomException
from imxInsights.exceptions.exceptionLevels import ErrorLevelEnum


class ExceptionHandler:
    """
    Handler for logging and managing exceptions.

    ??? info
        This class logs exceptions to a specified file, with log rotation occurring at 10 MB.
        It can handle exceptions by logging the error message and additional data, and optionally
        raise critical exceptions.

    Args:
        log_file: The file where logs should be written.
        lvl: The default logging level.
    """

    LOG_ROTATION_SIZE = "10 MB"

    def __init__(
        self, log_file: str, lvl: ErrorLevelEnum = ErrorLevelEnum.DEBUG
    ) -> None:
        self.log_file = log_file
        self.log_lvl: ErrorLevelEnum = lvl
        try:
            logger.add(log_file, rotation=self.LOG_ROTATION_SIZE, level=lvl.value)
        except (PermissionError, OSError):
            logger.warning(
                f"Could not write to {log_file}, falling back to console logging."
            )

    @staticmethod
    def handle_exception(
        exception: CustomException, return_log_as_str: bool = False
    ) -> str | None:
        """
        Handles a given exception by logging it and optionally raising it.

        ??? info
            This method logs the exception message and any additional data. If the exception
            level is CRITICAL, the exception is raised. It can also return the log message as a
            string if specified.

        Args:
            exception: The exception to be handled.
            return_log_as_str: Whether to return the log message as a string.

        Returns:
            The log message if return_log_as_str is True, otherwise None.

        Raises:
            CustomException: If level is CRITICAL.

        """
        log_level = exception.level.value

        log_msg = f"{exception.__class__.__name__}: {exception.msg}"

        if isinstance(exception.data, ImxObject):
            log_msg += f" - object: {exception.data.puic}"  # pragma: no cover
        elif exception.data is not None:
            log_msg += f" - data: {exception.data}"  # pragma: no cover

        logger.opt(depth=1).log(log_level, log_msg)

        if exception.level in [ErrorLevelEnum.CRITICAL]:
            raise exception  # pragma: no cover

        if return_log_as_str:
            return f"{log_level} {log_msg}"

        return None

    # @classmethod
    # def create_new_log(cls, log_file: str, lvl: ErrorLevelEnum = ErrorLevelEnum.DEBUG):
    #     """
    #     Creates a new log file.
    #
    #     ??? info
    #         This method removes any existing loggers and sets up a new log file with
    #         the specified rotation size and logging level.
    #
    #     Args:
    #         log_file: The file where logs should be written.
    #         lvl: The default logging level.
    #     """
    #     logger.remove()
    #     logger.add(log_file, rotation=cls.LOG_ROTATION_SIZE, level=lvl.value)


timestamp = datetime.datetime.now().isoformat()
safe_timestamp = re.sub(r"[:]", "-", timestamp)
# exception_handler = ExceptionHandler(f"imx_log_{safe_timestamp}.log")
exception_handler = ExceptionHandler("imxInsights.log")
