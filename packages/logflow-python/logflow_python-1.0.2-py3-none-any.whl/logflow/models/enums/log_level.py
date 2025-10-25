from enum import Enum


class LogLevel(str, Enum):
    """Log level names used by :class:`LogType`."""

    SUCCESS = "Success"
    INFO = "Info"
    DEBUG = "Debug"
    WARNING = "Warning"
    ERROR = "Error"
    FATAL = "Fatal"

