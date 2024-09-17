from enum import Enum


class ErrorLevelEnum(Enum):
    """
    Enumeration of error levels with corresponding descriptions.

    ??? info
        This enumeration provides a set of predefined error levels, ranging from
        SUCCESS to CRITICAL, each representing the severity of the message or error.

    """

    SUCCESS = "SUCCESS"
    """Represents a successful operation."""

    DEBUG = "DEBUG"
    """Represents debug or diagnostic information."""

    INFO = "INFO"
    """Represents informational messages."""

    WARNING = "WARNING"
    """Represents warning messages indicating potential issues."""

    ERROR = "ERROR"
    """Represents error messages indicating failures."""

    CRITICAL = "CRITICAL"
    """Represents critical error messages indicating breaking failures."""
