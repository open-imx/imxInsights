import pytest
from unittest.mock import patch

from imxInsights.exceptions import ErrorLevelEnum, ImxException, exception_handler
from imxInsights.exceptions.customException import CustomException


@patch("imxInsights.exceptions.exceptionHandler.exception_handler")
def test_exceptions(mock_exception_handler):
    try:
        raise CustomException(  # noqa: TRY301
            "This is a DEBUG level exception, and should be logged",
            level=ErrorLevelEnum.DEBUG,
        )
    except CustomException as e:
        log_str = exception_handler.handle_exception(e, return_log_as_str=True)
        assert (
            log_str
            == "DEBUG CustomException: This is a DEBUG level exception, and should be logged"
        )

    try:
        raise CustomException(  # noqa: TRY301
            "This is an INFO level exception, and should be logged",  # noqa: TRY301
            level=ErrorLevelEnum.INFO,
        )
    except CustomException as e:
        exception_handler.handle_exception(e)

    try:
        raise CustomException(  # noqa: TRY301
            "This is a WARNING level exception, and should be logged",  # noqa: TRY301
            level=ErrorLevelEnum.WARNING,
        )
    except CustomException as e:
        exception_handler.handle_exception(e)

    try:
        raise CustomException(  # noqa: TRY301
            "This is an ERROR level exception, and should be logged",
            level=ErrorLevelEnum.ERROR,
        )
    except CustomException as e:
        exception_handler.handle_exception(e)

    with pytest.raises(CustomException):
        try:
            raise CustomException(
                "This is a CRITICAL level exception, and should be logged and will raise",
                level=ErrorLevelEnum.CRITICAL,
            )
        except CustomException as e:
            exception_handler.handle_exception(e)
    exception_handler.handle_exception(
        CustomException("ownee toch niet", level=ErrorLevelEnum.INFO)
    )

    try:
        raise ImxException()
    except CustomException as e:
        exception_handler.handle_exception(e)
