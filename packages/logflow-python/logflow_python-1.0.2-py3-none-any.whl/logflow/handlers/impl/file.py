from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

from ..handler import Handler
from ...config import LogConfig
from ...formatters.impl import FileFormatter 
from ...models import Log


class FileHandler(Handler):
    """Persists logs to a file on disk."""

    def __init__(
        self,
        path: str | Path = LogConfig.LOG_FILE_PATH,
        mode: str = "a",
        encoding: Optional[str] = "utf-8",
    ) -> None:
        self._path = Path(path)
        self._formatter: FileFormatter = FileFormatter()
        self._mode = mode
        self._encoding = encoding
        self.__date = datetime.date.today()

    def handle(self, log: Log) -> None:
        message = self._formatter.format(log)  
        self._path = Path(LogConfig.LOG_FILE_PATH).with_name(
            f"log_{self.__date.strftime('%Y_%m_%d')}.txt"
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open(self._mode, encoding=self._encoding) as file:
            file.write(f"{message}\n")

