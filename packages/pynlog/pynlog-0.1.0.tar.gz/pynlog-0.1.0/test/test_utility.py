from unittest import TestCase, main


from pynlog._utility import truncate, get_caller


class TestTruncate(TestCase):
    """
    Runs tests for the function truncate from _utility.py
    """
    def test_short_truncate(self):
        actual = truncate("short_string")
        expected = "short_string            "
        self.assertEqual(actual, expected)
    

    def test_long_truncate(self):
        actual = truncate("very_very_very_very_long_string")
        expected = "...very_very_long_string"
        self.assertEqual(actual, expected)


class TestGetCaller(TestCase):
    """
    Runs tests for the function get_caller from _utility.py
    """
    def test_short_no_class_name(self):
        def short_name():
            return get_caller(1)
        
        actual = short_name()
        expected = "short_name              "
        self.assertEqual(actual, expected)

    
    def test_long_no_class_name(self):
        def very_very_very_very_long_name():
            return get_caller(1)
        
        actual = very_very_very_very_long_name()
        expected = "...y_very_very_long_name"
        self.assertEqual(actual, expected)
    

    def test_short_with_class_name(self):
        class Sample:
            def short_name(self):
                return get_caller(1)
        
        actual = Sample().short_name()
        expected = "Sample.short_name       "
        self.assertEqual(actual, expected)


    def test_long_with_class_name(self):
        class Sample:
            def very_very_very_very_long_name(self):
                return get_caller(1)
        
        actual = Sample().very_very_very_very_long_name()
        expected = "...y_very_very_long_name"
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    main()
