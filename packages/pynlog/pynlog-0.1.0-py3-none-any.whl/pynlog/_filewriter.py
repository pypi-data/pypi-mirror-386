from os import makedirs, path
from datetime import datetime
from re import compile


from pynlog._writer import Writer


class FileWriter(Writer):
    """
    A helper class used by Log to write log message to a file.

    This class inherits from `Writer` and provides a simple `write` method for
    writing log messages to a file. It also manages file creation and rotation
    based on size.

    Attributes:
        MAX_SIZE (int): The maximum size of a file (in bytes) before a new file
                        file is created. Defaults to 50 MB.
        EXT (str): The file extension used for log files. Defaults to ".log".

    Methods:
        create_file_name(now: datetime) -> str: Creates a filename based on the current datetime.
        write(message: str) -> None: Writes a log message to a file.
    """

    MAX_SIZE: int = 50 * 1024 * 1024
    """
    The maximum size (in bytes) before the writer rotates to a new file.
    Defaults to 50 MB.
    """

    EXT: str = ".log"
    """
    The file extension used for log files.
    Defaults to ".log".
    """

    def __init__(self, output_path: str = "logs") -> None:
        """
        Initializes a FileWriter instance.

        Args:
            output_path (str): The directory where log files will be written.
                                Defaults to "logs".
        """
        makedirs(output_path, exist_ok=True)
        self.__output_path = output_path
        self.__prev_filename = ""
        self.__file_prefix = ""
        self.__count = 0
        self.__ansi_escape = compile(r"\x1B\[[0-9;]*[A-Za-z]")

    
    def create_file_name(self, now: datetime) -> str:
        """
        Creates a unique filename based on the current datetime.

        Args:
            now (datetime): The current datetime.
        
        Returns:
            str: A unique filename including the file extension.
        """
        time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"log_{time_str}"

        if self.__file_prefix == file_name:
            self.__count += 1
            return f"log_{time_str}_{self.__count}{self.EXT}"
        
        self.__file_prefix = file_name
        self.__count = 0
        return f"log_{time_str}{self.EXT}"
            


    def write(self, message: str) -> None:
        """
        Writes a log message to a file. Handles file rotation
        when the file exceeds `MAX_SIZE`.

        Args:
            message (str): The log message to write.
        """
        if not self.__prev_filename or (path.exists(self.__prev_filename) and path.getsize(self.__prev_filename) >= self.MAX_SIZE):
            self.__prev_filename = self.__output_path + "/" + self.create_file_name(datetime.now())
        
        with open(self.__prev_filename, "a") as file:
            file.write(self.__ansi_escape.sub('', message) + "\n")
