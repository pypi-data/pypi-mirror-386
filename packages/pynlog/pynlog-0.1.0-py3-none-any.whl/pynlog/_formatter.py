from datetime import datetime


from pynlog._level import Level
from pynlog._logentry import LogEntry


class Formatter:
    """
    Formats log entries into human-readable strings.

    This class handles alignment, color codes, and timestamp insertion to create
    well-formatted log messages.

    Attributes:
        DEBUG (str): Color code prefix for DEBUG level logs.
        INFO (str): Color code prefix for INFO level logs.
        SUCCESS (str): Color code prefix for SUCCESS level logs.
        WARNING (str): Color code prefix for WARNING level logs.
        ERROR (str): Color code prefix for ERROR level logs.
        END (str): Color code suffix to reset colors to default.
    
    Methods:
        format(entry: LogEntry) -> str: Formats a LogEntry into a string.
    """

    DEBUG: str = "\033[35m"
    """
    Color code prefix for DEBUG level logs.
    """

    INFO: str = "\033[36m"
    """
    Color code prefix for INFO level logs.
    """

    SUCCESS: str = "\033[32m"
    """
    Color code prefix for SUCCESS level logs.
    """
    
    WARNING: str = "\033[33m"
    """
    Color code prefix for WARNING level logs.
    """
    
    ERROR: str = "\033[31m"
    """
    Color code prefix for ERROR level logs.
    """
    
    END: str = "\033[0m"
    """
    Color code suffix to reset colors to default.
    """

    @property
    def __COLORS(self) -> dict[Level, str]:
        """
        Returns a dictionary mapping log levels to their corresponding color codes.

        Returns:
            dict[Level, str]: A dictionary of LogLevels to color code strings.
        """
        return {
            Level.DEBUG: self.DEBUG,
            Level.INFO: self.INFO,
            Level.SUCCESS: self.SUCCESS,
            Level.WARNING: self.WARNING,
            Level.ERROR: self.ERROR,
        }
    

    def __get_color(self, level: Level) -> str:
        """
        Determines the color code based on the log level.

        Args:
            level (Level): The log level.

        Returns:
            str: The corresponding color code string. Returns self.END if no color is assigned.
        """
        if level in self.__COLORS:
            return self.__COLORS[level]
        return self.END


    def format_time(self, time: datetime) -> str:
        """
        Formats a datetime object into a string representation.

        Args:
            time (datetime): The datetime object to format.

        Returns:
            str: A formatted string representing the datetime. Example: "2025-10-22 18:05:01.123".
        """
        return time.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(time.microsecond / 1000):03d}"


    def format(self, entry: LogEntry) -> str:
        """
        Formats a LogEntry into a human-readable string.

        Args:
            entry (LogEntry): The LogEntry object to format.
        
        Returns:
            str: The formatted log message.
        """
        time_str = self.format_time(entry.time)
        tag_str = f"[{entry.level.name}]"
        return f"[{time_str}] {self.__get_color(entry.level)}{tag_str:<10}{self.END} {entry.caller}: {entry.message}"