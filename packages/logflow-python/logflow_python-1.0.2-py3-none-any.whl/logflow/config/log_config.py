import platform
from logflow.formatters import DateTimeFormat

os_name: str = platform.system()

_filepath = os_name.lower() == 'windows' and 'C:\\Logs\\app.log' or '/var/log/app.log'

class LogConfig:
    CONSOLE_LOGGING_ENABLED = True
    FILE_LOGGING_ENABLED = True
    LOG_FILE_PATH = _filepath
    LOG_DATE_TIME_FORMAT = DateTimeFormat.ISO 