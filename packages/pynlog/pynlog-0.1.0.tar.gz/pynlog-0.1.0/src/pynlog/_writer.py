from abc import ABC, abstractmethod


class Writer(ABC):
    """
    Abstract base class for writing log messages. Concreate subclasses
    should implement the `write` method.
    """

    @abstractmethod
    def write(self, message: str) -> None:
        """
        Writes a log message. This method should be implemented by
        subclasses.

        Args:
            message (str): The log message to write.
        """
        raise NotImplementedError("Subclasses must implement the write method.")
