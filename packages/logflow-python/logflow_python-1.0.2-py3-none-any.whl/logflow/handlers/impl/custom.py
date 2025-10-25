from __future__ import annotations

from typing import Callable, Protocol, Union

from ..handler import Handler
from ...formatters import ConsoleFormatter
from ...models import Log


class _FormatterProtocol(Protocol):
    def format(self, log: Log) -> str: ...


FormatterType = Union[_FormatterProtocol, Callable[[Log], str]]


class CustomHandler(Handler):
    """Allows plugging an arbitrary callback into the logging pipeline."""

    def __init__(
        self,
        callback: Callable[[str, Log], None],
        *,
        formatter: FormatterType | None = None,
    ) -> None:
        self._callback = callback
        self._formatter: FormatterType = formatter or logFormater

    def handle(self, log: Log) -> None:
        if hasattr(self._formatter, "format"):
            message = self._formatter.format(log)  # type: ignore[attr-defined]
        else:
            message = self._formatter(log)  # type: ignore[operator]

        self._callback(message, log)

