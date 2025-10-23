from pynlog._formatter import Formatter
from pynlog._writer import Writer
from pynlog._consolewriter import ConsoleWriter
from pynlog._filewriter import FileWriter
from pynlog._level import Level
from pynlog._utility import get_caller
from pynlog._logentry import LogEntry

class Log:
    """
    A static logging utility class.

    This class provides static methods for logging messages at
    different levels. It is not meant to be instantiated, instead call
    its static methods directly.

    By default, it logs to console and to a file. The minimum level is DEBUG.

    Attributes:
        MIN_LEVEL (LEVEL): The minimum logging level to be logged, default is DEBUG.
        FORMATTER (Formatter): The formatter used to format the log message.
        WRITERS (dict[str, Writer]): A dictionary of writers to write to. The keys are names
                                        of the writers, and the values are Writer instances.
                                        the default writers are "console_writer" and
                                        "file_writer". You can remove each writer by popping
                                        it with the corresponding key name.
        
    Methods:
        d(message: str) -> None: Logs a debug message.
        i(message: str) -> None: Logs an info message. 
        s(message: str) -> None: Logs a success message.
        w(message: str) -> None: Logs a warning message.
        e(message: str) -> None: Logs an error message.
    """

    MIN_LEVEL: Level = Level.DEBUG
    """
    The minimum logging level to be logged, default is DEBUG. Messages with a level lower
    than this will not be logged.
    """

    FORMATTER: Formatter = Formatter()
    """
    The formatter used to format the log message. THis object handles converting the
    LogEntry into a human-readable string.
    """

    WRITERS: dict[str, Writer] = {
        "console_writer": ConsoleWriter(),
        "file_writer": FileWriter()
    }
    """
    A dictionary of writers to write to. The keys are names of the writers, and the values are
    Writer instances. The default writers are "console_writer" and "file_writer".
    
    If required, you can remove each writer by popping it with the keys "console_writer" and "file_writer".
    """

    @staticmethod
    def __log(level: Level, message: str) -> None:
        """
        Main method that handles the core logic for logging.

        This method checks if the given loggin level is greater than or equal to the minimum
        logging level `MIN_LEVEL`. If it is, it creates a LogEntry, formats the entry using
        the formatter, and writes the formatted message to each of the configured writers.

        Args:
            level (Level): The logging level.
            message (str): The message to log.
        """
        if level < Log.MIN_LEVEL:
            return

        caller = get_caller()
        entry = LogEntry(level, caller, message)

        formatted_message = Log.FORMATTER.format(entry)
        for writer in Log.WRITERS.values():
            writer.write(formatted_message)


    @staticmethod
    def d(message: str) -> None:
        """
        Logs a debug message.
            
        Args:
            message (str): The message to log.
        """
        Log.__log(Level.DEBUG, message)


    @staticmethod
    def i(message: str) -> None:
        """
        Logs a info message.
            
        Args:
            message (str): The message to log.
        """
        Log.__log(Level.INFO, message)
    

    @staticmethod
    def s(message: str) -> None:
        """
        Logs a success message.
            
        Args:
            message (str): The message to log.
        """
        Log.__log(Level.SUCCESS, message)
    

    @staticmethod
    def w(message: str) -> None:
        """
        Logs a warning message.
            
        Args:
            message (str): The message to log.
        """
        Log.__log(Level.WARNING, message)
    

    @staticmethod
    def e(message: str) -> None:
        """
        Logs a error message.
            
        Args:
            message (str): The message to log.
        """
        Log.__log(Level.ERROR, message)
