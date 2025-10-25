from ..formatter import Formatter
from ..enums import DateTimeFormat
from ...models import *
from ...config import LogConfig


class ConsoleFormatter(Formatter):
    def __init__(self):
        pass
    
    def format(self, log: Log) -> str:
        color = log.get_color().value if isinstance(log.get_color(), LogColors) else str(log.get_color())
        reset = LogColors.RESET.value
        level = log.get_level().value if hasattr(log.get_level(), "value") else str(log.get_level())
        date_time = log.get_date_time().strftime(LogConfig.LOG_DATE_TIME_FORMAT)
        message = log.get_message()
        return f"{color}[{level}]-[{date_time}]{reset}: {message}"

