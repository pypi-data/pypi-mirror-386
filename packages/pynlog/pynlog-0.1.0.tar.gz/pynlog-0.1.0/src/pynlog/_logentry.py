from dataclasses import dataclass
from datetime import datetime


from pynlog._level import Level


@dataclass
class LogEntry:
    """
    Data class representing a single log entry.

    This class encapsulates the essential information for a log message,
    including its level, source, and content.

    Attributes:
        level (Level): The log level. Represents the severity of the log message.
        caller (str): The name or identifier of the component that generated the log message.
        message (str): The content of the log message.
        time (datetime): The timestamp of the log entry. Defaults to the current time.
    """
    level: Level
    caller: str
    message: str

    time: datetime = datetime.now()