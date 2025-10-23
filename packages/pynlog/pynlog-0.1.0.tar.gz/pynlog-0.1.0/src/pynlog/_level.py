from enum import IntEnum


class Level(IntEnum):
    """
    Defines the log levels used by the logger.

    These levels represent the severity of a log message, influencing how
    the messages are handled and displayed.

    Attributes:
        DEBUG (int): Represents the most verbose level of logging, typically used for debugging.
        INFO (int): Represents general informational messages.
        SUCCESS (int): Represents a successful operation or event.
        WARNING (int): Represents a potential problem or unexpected situation.
        ERROR (int): Represents an error that occurred.
    """
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4