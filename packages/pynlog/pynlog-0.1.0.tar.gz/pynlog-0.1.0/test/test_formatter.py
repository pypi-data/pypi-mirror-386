from unittest import TestCase, main
from datetime import datetime


from pynlog import Formatter, LogEntry, Level


class TestFormatter(TestCase):
    def setUp(self) -> None:
        self.__formatter = Formatter()
        self.__now = datetime.now()
    

    def __get_time_str(self) -> str:
        return self.__now.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(self.__now.microsecond / 1000):03d}"
    

    def test_format_time(self):
        time = datetime(2025, 10, 22, 16, 55, 1, 102000)
        actual = self.__formatter.format_time(time)
        expected = "2025-10-22 16:55:01.102"
        self.assertEqual(actual, expected)

    
    def test_debug_format(self):
        entry = LogEntry(Level.DEBUG, "test_debug_format", "testing debug format", self.__now)
        actual = self.__formatter.format(entry)

        time_str = self.__get_time_str()
        expected = f"[{time_str}] {self.__formatter.DEBUG}[DEBUG]   {self.__formatter.END} test_debug_format: testing debug format"
        self.assertEqual(actual, expected)


    def test_info_format(self):
        entry = LogEntry(Level.INFO, "test_info_format", "testing info format", self.__now)
        actual = self.__formatter.format(entry)

        time_str = self.__get_time_str()
        expected = f"[{time_str}] {self.__formatter.INFO}[INFO]    {self.__formatter.END} test_info_format: testing info format"
        self.assertEqual(actual, expected)

    
    def test_success_format(self):
        entry = LogEntry(Level.SUCCESS, "test_success_format", "testing success format", self.__now)
        actual = self.__formatter.format(entry)

        time_str = self.__get_time_str()
        expected = f"[{time_str}] {self.__formatter.SUCCESS}[SUCCESS] {self.__formatter.END} test_success_format: testing success format"
        self.assertEqual(actual, expected)
    

    def test_warning_format(self):
        entry = LogEntry(Level.WARNING, "test_warning_format", "testing warning format", self.__now)
        actual = self.__formatter.format(entry)

        time_str = self.__get_time_str()
        expected = f"[{time_str}] {self.__formatter.WARNING}[WARNING] {self.__formatter.END} test_warning_format: testing warning format"
        self.assertEqual(actual, expected)

    
    def test_error_format(self):
        entry = LogEntry(Level.ERROR, "test_error_format", "testing error format", self.__now)
        actual = self.__formatter.format(entry)

        time_str = self.__get_time_str()
        expected = f"[{time_str}] {self.__formatter.ERROR}[ERROR]   {self.__formatter.END} test_error_format: testing error format"
        self.assertEqual(actual, expected)
    

    def test_change_color(self):
        self.__formatter.ERROR = "change_error"

        entry = LogEntry(Level.ERROR, "test_change_color", "testing change color format", self.__now)
        actual = self.__formatter.format(entry)

        time_str = self.__get_time_str()
        expected = f"[{time_str}] {self.__formatter.ERROR}[ERROR]   {self.__formatter.END} test_change_color: testing change color format"
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    main()
