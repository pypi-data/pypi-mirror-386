import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from PyQt5 import QtWidgets
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
import tempfile

from src.galassify import initgui, utils

class DummyArgs:
    """Mocked args object matching GUI expected values."""
    def __init__(self):
        self.projectpath = os.getcwd()  # default current dir
        self.inputfile = "input.csv"
        self.config = "config.yml"
        self.savefile = "output.csv"
        self.path = "images/"
        self.init = False
        self.example = ""


class TestUiInitGui(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start a QApplication instance once for all tests."""
        cls.app = QtWidgets.QApplication(sys.argv)

    def setUp(self):
        """Patch utils and initialize the GUI."""
        patcher_ver = patch("src.galassify.utils.getVersion", return_value="1.0.0")
        patcher_ex = patch("src.galassify.utils.examples", {"ex1": {"help": "Example: test"}})
        patcher_msg = patch("PyQt5.QtWidgets.QMessageBox.information", return_value=None)

        self.addCleanup(patcher_ver.stop)
        self.addCleanup(patcher_ex.stop)
        self.addCleanup(patcher_msg.stop)

        self.mock_ver = patcher_ver.start()
        self.mock_examples = patcher_ex.start()
        self.mock_msg = patcher_msg.start()

        self.args = DummyArgs()
        from src.galassify import initgui  # local import so patching works
        self.Ui_InitGui = initgui.Ui_InitGui
        self.gui = self.Ui_InitGui(self.args)

    def tearDown(self):
        """Close the window after each test."""
        self.gui.close()

    def test_window_title_and_icon(self):
        """Check that window title and icon are set correctly."""
        self.assertEqual(self.gui.windowTitle(), "GALAssify 1.0.0")

    def test_textboxes_initialized(self):
        """Ensure text boxes contain argument defaults."""
        self.assertEqual(self.gui.tb_projectFolder.toPlainText(), self.args.projectpath)
        self.assertEqual(self.gui.tb_inputFile.toPlainText(), "input.csv")
        self.assertEqual(self.gui.tb_confFile.toPlainText(), "config.yml")
        self.assertEqual(self.gui.tb_outputFile.toPlainText(), "output.csv")
        self.assertEqual(self.gui.tb_imgFiles.toPlainText(), "images/")

    def test_example_selection_and_tracking(self):
        """Simulate example radio button selection."""
        rb = self.gui.examples["ex1"]["rb"]
        QTest.mouseClick(rb, Qt.LeftButton)
        self.assertEqual(self.gui.selectedExample, "ex1")

    def test_on_ok_button_sets_ret_and_updates_args(self):
        """Simulate clicking OK and ensure args updated."""
        # simulate user changes
        self.gui.tb_projectFolder.setText("new_project")
        self.gui.tb_inputFile.setText("new_input.csv")
        self.gui.tb_confFile.setText("new_config.yml")
        self.gui.tb_outputFile.setText("new_output.csv")
        self.gui.tb_imgFiles.setText("new_images/")

        # select example
        self.gui.rb_examples.setChecked(True)
        rb = self.gui.examples["ex1"]["rb"]
        rb.setChecked(True)

        # simulate OK
        self.gui.onOkeyButton()
        ret, args = self.gui.getResults()

        self.assertEqual(ret, 0)
        self.assertEqual(args.projectpath, "new_project")
        self.assertEqual(args.inputfile, "new_input.csv")
        self.assertEqual(args.config, "new_config.yml")
        self.assertEqual(args.savefile, "new_output.csv")
        self.assertEqual(args.path, "new_images/")
        self.assertEqual(args.example, "ex1")

    def test_on_cancel_button_sets_ret(self):
        """Simulate pressing cancel."""
        self.gui.onCancelButton()
        ret, args = self.gui.getResults()
        self.assertEqual(ret, 1)

    def test_on_project_folder_selected_makes_paths_absolute(self):
        """onProjectFolderSelected() should join relative paths with project folder."""
        self.gui.tb_projectFolder.setText("/tmp/project_dir")
        self.gui.args.projectpath = "/tmp/project_dir"
        self.gui.args.inputfile = "data/input.csv"
        self.gui.args.config = "conf/config.yml"
        self.gui.args.savefile = "results/output.csv"
        self.gui.args.path = "imgs/"

        self.gui.onProjectFolderSelected()

        self.assertTrue(self.gui.tb_inputFile.toPlainText().startswith("/tmp/project_dir"))
        self.assertTrue(self.gui.tb_confFile.toPlainText().startswith("/tmp/project_dir"))
        self.assertTrue(self.gui.tb_outputFile.toPlainText().startswith("/tmp/project_dir"))
        self.assertTrue(self.gui.tb_imgFiles.toPlainText().startswith("/tmp/project_dir"))

    def test_get_results_initial(self):
        """Initially, ret should be -1 before any user action."""
        ret, args = self.gui.getResults()
        self.assertEqual(ret, -1)
        self.assertIs(args, self.args)

    @patch("PyQt5.QtWidgets.QMessageBox.critical", return_value=None)
    def test_open_existing_with_missing_files(self, mock_critical):
        """If opening existing project and files are missing, show error and do not close."""
        # Ensure open-existing mode
        self.gui.rb_openExisting.setChecked(True)
        self.gui.rb_init.setChecked(False)
        self.gui.rb_examples.setChecked(False)

        # Set a fake project directory and non-existent files
        self.gui.tb_projectFolder.setText("/tmp/fake_project")
        self.gui.tb_inputFile.setText("nonexistent.csv")
        self.gui.tb_confFile.setText("nonexistent.yml")
        self.gui.tb_imgFiles.setText("nonexistent_dir")

        # Call the function under test
        self.gui.onOkeyButton()

        # QMessageBox.critical should have been called
        mock_critical.assert_called_once()
        # GUI should *not* have closed (ret stays -1)
        self.assertEqual(self.gui.ret, -1)

    @patch("PyQt5.QtWidgets.QMessageBox.critical", return_value=None)
    def test_open_existing_with_all_files_present(self, mock_critical):
        """If opening existing project and all files exist, GUI closes successfully."""
        # Create temporary files to simulate existing files
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "input.csv")
            f2 = os.path.join(tmpdir, "config.yml")
            f3 = os.path.join(tmpdir, "images")
            # Create fake files/directories
            open(f1, "w").close()
            open(f2, "w").close()
            os.mkdir(f3)

            self.gui.rb_openExisting.setChecked(True)
            self.gui.rb_init.setChecked(False)
            self.gui.rb_examples.setChecked(False)

            self.gui.tb_projectFolder.setText(tmpdir)
            self.gui.tb_inputFile.setText("input.csv")
            self.gui.tb_confFile.setText("config.yml")
            self.gui.tb_imgFiles.setText("images")

            self.gui.onOkeyButton()

            # Should NOT show error dialog
            mock_critical.assert_not_called()
            # GUI should close successfully
            self.assertEqual(self.gui.ret, 0)

if __name__ == "__main__":
    unittest.main()
