from ..formatter import Formatter
from ...models import Log
from logflow.config import LogConfig
from ...formatters import DateTimeFormat

class FileFormatter(Formatter):
    def __init__(self):
        pass
    
    def format(self, log: Log) -> str:
        timestamp = log.get_date_time().strftime(LogConfig.LOG_DATE_TIME_FORMAT)
        return f"[{timestamp}] [{log.get_level().name}] {log.get_message()}"
