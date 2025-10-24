import os, sys
import unittest
import shutil, tempfile
import importlib
from src.galassify import utils
from unittest.mock import patch
from pathlib import Path
import argparse

class TestUtils(unittest.TestCase):

    #def test_get_options(self):
    #    testargs = ["main", "--list"]
    #    with patch.object(sys, 'argv', testargs):
    #        result = utils.getOptions('')
    #    print(result)

    def setUp(self):
        # Import refreshed libraries (skip already initialised globals)
        importlib.reload(utils)

        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Galassify basic configuration
        self.path = os.path.join(self.test_dir, 'img/')
        self.file_config = os.path.join(self.test_dir, 'config')
        self.savefile = os.path.join(self.test_dir, 'output.csv')
        self.inputfile = os.path.join(self.test_dir, 'files/galaxies.csv')

        self.group = []
        self.testargs = argparse.Namespace(init=False,
                                            example='',
                                            path=self.path,
                                            config=self.file_config,
                                            savefile=self.savefile,
                                            list=False,
                                            inputfile=self.inputfile,
                                            group=self.group)

        # Parte simulated arguments
        utils.args = self.testargs

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_exist_basic_files(self):
        os.chdir(self.test_dir)
        result = utils.exist_basic_files()
        self.assertFalse(result)

        os.mkdir('files')
        result = utils.exist_basic_files()
        self.assertFalse(result)

        Path('files/galaxies.csv').touch()
        result = utils.exist_basic_files()
        self.assertFalse(result)

        os.mkdir('img')
        result = utils.exist_basic_files()
        self.assertFalse(result)

        Path('config').touch()
        result = utils.exist_basic_files()
        self.assertTrue(result)

        # Cleanup
        os.remove('config')
        os.rmdir('img')
        os.remove('files/galaxies.csv')
        os.rmdir('files')
        os.chdir('../')


if __name__ == '__main__':
    unittest.main()
