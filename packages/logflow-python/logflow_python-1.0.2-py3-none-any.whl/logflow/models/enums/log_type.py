from dataclasses import dataclass

from .log_colors import LogColors
from .log_level import LogLevel


@dataclass(frozen=True)
class LogType:
    """Mapping between a :class:`LogLevel` and the colour it should be displayed with."""

    log_level: LogLevel
    log_color: LogColors


class LogTypes:
    """Predefined collection of useful log types."""

    ERROR = LogType(LogLevel.ERROR, LogColors.ERROR)
    WARNING = LogType(LogLevel.WARNING, LogColors.WARNING)
    DEBUG = LogType(LogLevel.DEBUG, LogColors.DEBUG)
    INFO = LogType(LogLevel.INFO, LogColors.INFO)
    FATAL = LogType(LogLevel.FATAL, LogColors.FATAL)
    SUCCESS = LogType(LogLevel.SUCCESS, LogColors.SUCCESS)

