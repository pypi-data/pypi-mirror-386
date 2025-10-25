from __future__ import annotations

from typing import Iterable, List, Sequence

from logflow.handlers import ConsoleHandler, Handler, FileHandler
from logflow.models import Log, LogType
from logflow.config import LogConfig


class Logger:
    """Small utility orchestrating handlers to process logs."""

    def __init__(self, handlers: Sequence[Handler] | None = None):
        self.__handlers: List[Handler] = []
        if handlers:
            self.add_handlers(handlers)
        else:
            if LogConfig.CONSOLE_LOGGING_ENABLED:
                self.__handlers.append(ConsoleHandler())
            if LogConfig.FILE_LOGGING_ENABLED:
                self.__handlers.append(FileHandler())

    def add_handler(self, handler: Handler) -> None:
        if handler not in self.__handlers:
            self.__handlers.append(handler)

    def add_handlers(self, handlers: Iterable[Handler]) -> None:
        for handler in handlers:
            self.add_handler(handler)

    def remove_handler(self, handler: Handler) -> None:
        self.__handlers.remove(handler)

    def clear_handlers(self) -> None:
        self.__handlers.clear()

    def get_handlers(self) -> Sequence[Handler]:
        return tuple(self.__handlers)

    def log(self, log: Log) -> None:
        for handler in list(self.__handlers):
            handler.handle(log)

    def log_message(self, log_type: LogType, message: str) -> Log:
        log = Log(log_type, message)
        self.log(log)
        return log
            
