from __future__ import annotations

import sys
from typing import Callable, Protocol, TextIO, Union

from ..handler import Handler
from ...formatters import ConsoleFormatter
from ...models import Log




class ConsoleHandler(Handler):
    """Handler that prints logs to a text stream (stdout by default)."""

    def __init__(self):
        self.__formatter = ConsoleFormatter()

    def handle(self, log: Log) -> None:
        message = self.__formatter.format(log)  # type: ignore[attr-defined]
        print(message)