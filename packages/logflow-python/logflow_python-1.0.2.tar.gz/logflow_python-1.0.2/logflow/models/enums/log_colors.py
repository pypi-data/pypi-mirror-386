from enum import Enum

from colorama import Fore


class LogColors(str, Enum):
    """Color palette used by the built-in formatters."""

    ERROR = Fore.LIGHTRED_EX
    INFO = Fore.LIGHTBLUE_EX
    DEBUG = Fore.LIGHTCYAN_EX
    SUCCESS = Fore.LIGHTGREEN_EX
    WARNING = Fore.LIGHTYELLOW_EX
    FATAL = Fore.LIGHTMAGENTA_EX
    RESET = Fore.RESET

