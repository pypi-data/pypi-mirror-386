from unittest import TestCase, main
from io import StringIO
import sys


from pynlog import Log, Formatter, Level, Writer, LogEntry


class FakeFormatter(Formatter):
    def format(self, entry: LogEntry) -> str:
        return f"{entry.level.name} {entry.message}"


class TestLog(TestCase):
    def setUp(self):
        self.__formatter = Log.FORMATTER
        Log.FORMATTER = FakeFormatter()
        Log.MIN_LEVEL = Level.DEBUG

        self.__captured = StringIO()
        self.__sys_stdout = sys.stdout
        sys.stdout = self.__captured

    
    def test_debug_log(self):
        message = "message"
        Log.d(message)

        actual = self.__captured.getvalue().strip()
        expected = "DEBUG message"
        self.assertEqual(actual, expected)
    

    def test_info_log(self):
        message = "message"
        Log.i(message)

        actual = self.__captured.getvalue().strip()
        expected = "INFO message"
        self.assertEqual(actual, expected)


    def test_success_log(self):
        message = "message"
        Log.s(message)

        actual = self.__captured.getvalue().strip()
        expected = "SUCCESS message"
        self.assertEqual(actual, expected)
    

    def test_warning_log(self):
        message = "message"
        Log.w(message)

        actual = self.__captured.getvalue().strip()
        expected = "WARNING message"
        self.assertEqual(actual, expected)
    

    def test_error_log(self):
        message = "message"
        Log.e(message)

        actual = self.__captured.getvalue().strip()
        expected = "ERROR message"
        self.assertEqual(actual, expected)
    

    def test_change_formatter(self):
        class TempFormatter(Formatter):
            def format(self, entry: LogEntry) -> str:
                return "formatter changed"
        
        Log.FORMATTER = TempFormatter()
        Log.d("any message")

        actual = self.__captured.getvalue().strip()
        expected = "formatter changed"
        self.assertEqual(actual, expected)

    
    def test_change_min_level(self):
        message = "first message"
        Log.d(message)

        actual = self.__captured.getvalue().strip()
        expected = "DEBUG first message"
        self.assertEqual(actual, expected)

        Log.MIN_LEVEL = Level.INFO
        
        message = "second message"
        Log.d(message)

        actual = self.__captured.getvalue().strip()
        expected = "DEBUG first message\nDEBUG second message"
        self.assertNotEqual(actual, expected)

        message = "third message"
        Log.s(message)

        actual = self.__captured.getvalue().strip()
        expected = "DEBUG first message\nSUCCESS third message"
        self.assertEqual(actual, expected)
    

    def test_add_writer(self):
        class FakeWriter(Writer):
            def write(self, message: str) -> None:
                print(message)
        
        Log.WRITERS["fake_writer"] = FakeWriter()
        self.assertEqual(len(Log.WRITERS.values()), 3)

        Log.WRITERS.pop("fake_writer")


    def tearDown(self) -> None:
        sys.stdout = self.__sys_stdout
        Log.FORMATTER = self.__formatter


if __name__ == "__main__":
    main()
