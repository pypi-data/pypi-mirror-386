from __future__ import annotations

from datetime import datetime
from typing import Dict

from .enums import LogColors, LogLevel, LogType


class Log:
    """Container describing a single log event."""

    def __init__(self, log_type: LogType, message: str, date_time: datetime | None = None):
        if date_time is None:
            date_time = datetime.now()

        self.__color: LogColors = log_type.log_color
        self.__level: LogLevel = log_type.log_level
        self.__message: str = message
        self.__date_time: datetime = date_time

    def get_color(self) -> LogColors:
        return self.__color

    def get_level(self) -> LogLevel:
        return self.__level

    def get_message(self) -> str:
        return self.__message

    def get_date_time(self) -> datetime:
        return self.__date_time

    def set_date_time(self, date_time: datetime) -> None:
        self.__date_time = date_time

    def to_dict(self) -> Dict[str, str]:
        """Serialise the log into a JSON friendly dictionary."""

        return {
            "level": self.__level.value,
            "message": self.__message,
            "date_time": self.__date_time.isoformat(),
        }

    def __repr__(self) -> str:
        return f"Log(level={self.__level.value!r}, message={self.__message!r}, date_time={self.__date_time.isoformat()!r})"
