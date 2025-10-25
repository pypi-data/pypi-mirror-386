from __future__ import annotations

from abc import ABC, abstractmethod

from logflow.models import Log


class Handler(ABC):
    """Base class for every log handler."""

    @abstractmethod
    def handle(self, log: Log) -> None:
        """Process a log produced by :class:`logFlow.logger.Logger`."""

        raise NotImplementedError