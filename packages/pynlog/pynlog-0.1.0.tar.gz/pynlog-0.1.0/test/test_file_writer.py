from unittest import TestCase, main
from os import path, listdir
from datetime import datetime
from shutil import rmtree
from time import sleep


from pynlog import FileWriter


class TestFileWriter(TestCase):
    __OUTPUT_PATH = "out/logs"


    def setUp(self) -> None:
        self.__writer = FileWriter(self.__OUTPUT_PATH)

    
    def __read_file(self) -> str:
        files = [path.join(self.__OUTPUT_PATH, file) for file in listdir(self.__OUTPUT_PATH)]
        files = [file for file in files if path.isfile(file)]
        if not files:
            raise FileNotFoundError("No files found in output folder")
        
        last_file = max(files, key=path.getctime)

        with open(last_file, "r") as file:
            return file.read()

    
    def test_output_folder_exists(self):
        assert path.exists(self.__OUTPUT_PATH)
    

    def test_create_filename(self):
        now = datetime.now()
        actual = self.__writer.create_file_name(now)

        time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        expected = f"log_{time_str}.log"

        self.assertEqual(actual, expected)
    

    def test_change_extension(self):
        self.__writer.EXT = ".txt"
        now = datetime.now()
        actual = self.__writer.create_file_name(now)

        time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        expected = f"log_{time_str}.txt"

        self.assertEqual(actual, expected)
    

    def test_write_no_file(self):
        message = "test_write_no_file"

        self.__writer.write(message)
        actual = self.__read_file()

        expected = f"{message}\n"
        self.assertEqual(actual, expected)

    
    def test_write_new_file(self):
        self.__writer.MAX_SIZE = 1

        first_message = "test_write_new_file_1"

        self.__writer.write(first_message)
        actual = self.__read_file()
        expected = f"{first_message}\n"
        self.assertEqual(actual, expected)

        sleep(0.1)

        second_message = "test_write_new_file_2"
        self.__writer.write(second_message)
        actual = self.__read_file()
        expected = f"{second_message}\n"
        self.assertEqual(actual, expected)

        files = [path.join(self.__OUTPUT_PATH, file) for file in listdir(self.__OUTPUT_PATH)]
        files = [file for file in files if path.isfile(file)]
        self.assertEqual(len(files), 2)    

    def tearDown(self) -> None:
        rmtree(self.__OUTPUT_PATH)


if __name__ == "__main__":
    main()
