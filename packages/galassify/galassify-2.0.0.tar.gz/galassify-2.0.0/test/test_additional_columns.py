import os, sys
import unittest
import random
import shutil, tempfile
import importlib
from PyQt5.QtTest import QTest
import src.galassify
from src.galassify import gui, utils
from unittest.mock import patch
from pathlib import Path
import argparse
import pandas as pd
import json
import random

class TestGui(unittest.TestCase):
    def setUp(self):
        # Import refreshed libraries (skip already initialised globals)
        importlib.reload(utils)

        # Create a temporary directory
        self.galassifyPath = os.path.dirname(src.galassify.__file__)
        self.test_dir = tempfile.mkdtemp()
        self.app = gui.QtWidgets.QApplication(sys.argv)

        # Galassify basic configuration
        self.path = os.path.join(self.galassifyPath, 'img/')
        self.file_config = os.path.join(self.galassifyPath, 'config')
        self.savefile = os.path.join(self.test_dir, 'output.csv')
        self.inputfile = os.path.join(self.test_dir, 'files/galaxies.csv')
        os.system(f"mkdir -p {os.path.dirname(self.inputfile)}")
        os.system(f"cp -f {os.path.join(self.galassifyPath, 'files/galaxies.csv')} {os.path.dirname(self.inputfile)}")
        self.group = []
        self.testargs = argparse.Namespace(init=False,
                                            example='',
                                            path=self.path,
                                            config=self.file_config,
                                            savefile=self.savefile,
                                            list=False,
                                            inputfile=self.inputfile,
                                            group=self.group)

        # Open the input file for adding additional columns
        self.input_df = pd.read_csv(self.inputfile)

        # Populate a new column with random data
        self.rand_col_name = ''.join(random.choice('abcdefghi1234') for _ in range(30))
        length = len(self.input_df)
        self.input_df[self.rand_col_name] = length*[random.randint(0, 100), ]

        # Save the file
        self.input_df.to_csv(self.inputfile, index=False)

        # Parse configuration
        with open(self.file_config, 'r') as f:
            self.config:dict = json.loads(f.read())

        # Parte simulated arguments
        utils.args = self.testargs
        self.selectedFiles, self.selectedGroups = utils.getFiles()

        # Create window
        self.window = gui.Ui(self.selectedFiles, self.selectedGroups)


    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)


    def test_1_additional_column(self):
        # Test that all the data in the additional column is displayed

        # Ensure that the additional column is the displayed columns
        label = ""
        for column in range(self.window.fileList.columnCount()):
            label = self.window.fileList.horizontalHeaderItem(column).text()
            if label == self.rand_col_name:
                break
        self.assertEqual(label, self.rand_col_name)

        # For each row in table:
        for i in range(self.window.fileList.rowCount()):
            # Ensure that the cursor is in the i-th element
            self.window.fileList.selectRow(i)
            currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
            self.assertEqual(currentIndex, i)

            # Compare the displayed random value with the precomputed one
            itemText = self.window.fileList.item(currentIndex, column).text()
            randColText = str(self.input_df[self.rand_col_name].iloc[i])
            self.assertEqual(itemText, randColText)


if __name__ == '__main__':
    unittest.main()
