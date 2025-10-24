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


    def test_1_widgets_config(self):
        for tconf in self.config['form']:
            tconf:dict

            # check basic define params
            if 'id' in tconf.keys():
                id:str = tconf['id']

            name = id.capitalize()
            if 'name' in tconf.keys():
                name = tconf['name']

            if 'type' not in tconf.keys():
                continue

            # COMMENTBOX
            if tconf['type'] == 'text':
                self.assertTrue(id in self.window.tb.keys())

            if 'elements' in tconf.keys():
                nOfElements = len(tconf['elements'])

                # CHECKBOX
                if tconf['type'] == 'checkbox':
                    self.assertTrue(id in self.window.cb.keys())
                    self.assertEqual(len(self.window.cb[id].keys()), nOfElements)

                # RADIOBUTTON TYPE
                elif tconf['type'] == 'radiobutton':
                    self.assertTrue(id in self.window.rb.keys())
                    self.assertEqual(len(self.window.rb[id].keys()), nOfElements)


    def test_2_table_startup(self):
        # Ensure that the table starts with the first element selected
        currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
        self.assertEqual(currentIndex, 0)


    def test_3_table_PgDn(self):
        # Ensure that the table starts with the first element selected
        self.window.pb_next.click()
        currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
        self.assertEqual(currentIndex, 1)


    def test_4_table_PgUp(self):
        # Ensure that the table starts with the first element selected
        self.window.pb_prev.click()
        currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
        self.assertEqual(currentIndex, 0)


    def test_5_checkboxes(self):
        # For each checkbox group:
        for cb_group, cbs in self.window.cb.items():
            cols = list(self.window.cb[cb_group].keys())
            for cb_name, cb_widget in cbs.items():
                cb_columns = cols.copy()
                # Ensure that the cursor is in the first element
                self.window.fileList.selectRow(0)
                currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
                self.assertEqual(currentIndex, 0)

                # Check the current checkbox
                cb_widget.click()

                # Save the file
                self.window.pb_save.click()
                currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
                self.assertEqual(currentIndex, 1)

                # Read the output file
                output_df = pd.read_csv(self.savefile, usecols=cols)

                # Ensure that file only contains a single row
                self.assertEqual(len(output_df), 1)

                # Ensure 'large' tag is true
                self.assertTrue(output_df.loc[0, cb_name])

                # Ensure all other tags are false
                cb_columns.remove(cb_name)
                for col in cb_columns:
                    self.assertFalse(output_df.loc[0, col])

                # Come back to the first element
                self.window.fileList.selectRow(0)
                currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
                self.assertEqual(currentIndex, 0)

                # Uncheck the current checkbox
                cb_widget.click()

                # Save the file with the current checkbox unchecked
                self.window.pb_save.click()
                currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
                self.assertEqual(currentIndex, 1)

                # Read the output file again
                output_df = pd.read_csv(self.savefile, usecols=cols)

                # Ensure that file only contains a single row
                self.assertEqual(len(output_df), 1)

                # Ensure all tags are false
                for col in cols:
                    self.assertFalse(output_df.loc[0, col])


    def test_6_radiobuttons(self):
        # For each radiobutton group:
        for rb_group, rbs in self.window.rb.items():
            for rb_name, rb_widget in rbs.items():
                # Ensure that the cursor is in the first element
                self.window.fileList.selectRow(0)
                currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
                self.assertEqual(currentIndex, 0)

                # Check the current radiobutton
                rb_widget.click()

                # Save the file
                self.window.pb_save.click()
                currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
                self.assertEqual(currentIndex, 1)

                # Read the output file
                output_df = pd.read_csv(self.savefile, usecols=[rb_group, ])

                # Ensure that file only contains a single row
                self.assertEqual(len(output_df), 1)

                # Ensure rb_group tag is the saved one
                self.assertEqual(output_df.loc[0, rb_group], rb_name)


    def test_7_textbox(self):
        # For each textbox widget:
        for tb_name, widget in self.window.tb.items():
            # Ensure that the cursor is in the first element
            self.window.fileList.selectRow(0)
            currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
            self.assertEqual(currentIndex, 0)

            # Generate a random comment
            random_comment = ''.join(random.choice('abcdefghi1234') for _ in range(30))

            # Write the random comment
            QTest.keyClicks(self.window.tb[tb_name], random_comment)

            # Save the file
            self.window.pb_save.click()
            currentIndex = self.window.fileList.selectionModel().selectedRows()[0].row()
            self.assertEqual(currentIndex, 1)

            # Read the output file
            output_df = pd.read_csv(self.savefile, usecols=[tb_name, ])

            # Ensure that file only contains a single row
            self.assertEqual(len(output_df), 1)

            # Ensure 'morphology' tag is the saved one
            self.assertEqual(output_df.loc[0, tb_name], random_comment)


if __name__ == '__main__':
    unittest.main()
