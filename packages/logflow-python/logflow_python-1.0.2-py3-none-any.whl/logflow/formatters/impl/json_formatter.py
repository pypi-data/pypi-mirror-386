from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ..enums import DateTimeFormat
from ..formatter import Formatter
from ...models import Log
from ...config import LogConfig


class JsonFormatter(Formatter):
    def __init__(
        self,
        indent: Optional[int] = None
    ):
        self._indent = indent

    def format(self, log: Log) -> str:
        payload: Dict[str, Any] = {
            "level": log.get_level().value if hasattr(log.get_level(), "value") else str(log.get_level()),
            "message": log.get_message(),
            "date_time": log.get_date_time().strftime(LogConfig.LOG_DATE_TIME_FORMAT),
        }

        return json.dumps(payload, indent=self._indent)

