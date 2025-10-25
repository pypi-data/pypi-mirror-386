from logflow.formatters import DateTimeFormat
from ..formatter import Formatter
from logflow.config import LogConfig
from logflow.models import Log

class DictFormatter(Formatter):
    def __init__(self):
        pass

    def format(self, log: Log) -> dict:
        log_dict: dict = {
            "level": log.get_level().value,
            "message": log.get_message(),
            "timestamp": log.get_date_time().strftime(LogConfig.LOG_DATE_TIME_FORMAT)
        }
        return log_dict
