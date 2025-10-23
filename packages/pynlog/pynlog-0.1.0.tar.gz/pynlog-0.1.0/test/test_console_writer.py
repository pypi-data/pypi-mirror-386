from unittest import TestCase, main
from io import StringIO
import sys


from pynlog import ConsoleWriter


class TestConsoleWriter(TestCase):
    def setUp(self) -> None:
        self.__writer = ConsoleWriter()

        self.__captured = StringIO()
        self.__sys_stdout = sys.stdout
        sys.stdout = self.__captured


    def test_one_write(self):
        message = "a test message"

        self.__writer.write(message)

        actual = self.__captured.getvalue().strip()
        expected = message
        self.assertEqual(actual, expected)

    
    def test_two_write(self):
        first_message = "first message"
        second_message = "second message"

        self.__writer.write(first_message)
        self.__writer.write(second_message)

        actual = self.__captured.getvalue().strip()
        expected = f"{first_message}\n{second_message}"
        self.assertEqual(actual, expected)

    
    def tearDown(self) -> None:
        sys.stdout = self.__sys_stdout


if __name__ == "__main__":
    main()