from pynlog._writer import Writer


class ConsoleWriter(Writer):
    """
    A helper class used by Log to write messages to the console.

    This class inherits from `Writer` and provides a simple `write` method for
    displaying log messages.

    Attributes:
        None

    Methods:
        write(message: str) -> None: Writes a message to the console.
    """
    
    def write(self, message: str) -> None:
        """
        Writes a message to the console.

        Args:
            message (str): The message to write.
        """
        print(message)
