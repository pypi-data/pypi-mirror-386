from enum import Enum

class DateTimeFormatMasks(Enum):
    """Enum for standard datetime formats."""
    ISO = "%Y-%m-%dT%H:%M:%S"
    US = "%m/%d/%Y %I:%M %p"
    EU = "%d/%m/%Y %H:%M"
    SIMPLE = "%Y-%m-%d"
    FULL = "%A, %B %d, %Y %H:%M:%S"
    SHORT_TIME = "%H:%M"

class DateTimeFormat:
    """Class to hold different datetime format options."""
    ISO = DateTimeFormatMasks.ISO.value
    US = DateTimeFormatMasks.US.value
    EU = DateTimeFormatMasks.EU.value
    SIMPLE = DateTimeFormatMasks.SIMPLE.value
    FULL = DateTimeFormatMasks.FULL.value
    SHORT_TIME = DateTimeFormatMasks.SHORT_TIME.value
    CUSTOM = "CUSTOM"  # Placeholder for user-defined format