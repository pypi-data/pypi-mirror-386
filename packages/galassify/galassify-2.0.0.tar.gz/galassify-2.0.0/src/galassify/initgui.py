# -*- coding: utf-8 -*-

import os, sys
from functools import partial
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QObject, QEvent, QSize, QCoreApplication
from PyQt5.QtGui import QPixmap, QIcon

from . import utils

def opengui(args):
    """
    Opens a small GUI to select options graphically instead of using CLI args.
    Gets the current CLI args (or de default values if not specified) and allows
    the user to change them before passing it to the main execution.

    Parameters
    ----------
    args : argparse.Namespace
        Unprocessed CLI args to be modified in this GUI.

    Returns
    -------
    args : argparse.Namespace
        Args that include the values entered in the CLI plus the modifications
        done by the user graphically.
    """
    initapp = QtWidgets.QApplication(sys.argv)
    initwindow = Ui_InitGui(args)
    initapp.exec_()
    return initwindow.getResults()

class Ui_InitGui(QtWidgets.QMainWindow):
    """
    The main initial GUI class. When instantiated, it gets the values of the
    args that the user can modify graphically and represents them interactively.

    Parameters
    ----------
    args : argparse.Namespace
        Unprocessed CLI args to be modified in this GUI.
    """
    def __init__(self, args):
        super(Ui_InitGui, self).__init__()
        uic.loadUi(str(utils.getPackageResource('res/initgui.ui')), self)

        self.args = args
        self.title = 'GALAssify ' + utils.getVersion()
        self.ret = -1 # -1: Exit not expected. 0: OK button. 1: Cancel button.
        
        self.setWindowTitle(self.title)
        self.setWindowIcon(
            QIcon(
                str(utils.getPackageResource('res/window_icon.png'))
            )
        )

        self.lb_headerImage.setPixmap(QPixmap(str(utils.getPackageResource('res/GALAssify_GUI.png'))))

        # Fill examples dynamically
        self.examplesGroup = QtWidgets.QButtonGroup(self)
        self.examplesGroup.setExclusive(True)  # ensures only one example can be selected

        self.examples = utils.examples.copy()
        self.selectedExample = ''
        self.gb_examples_layout = QtWidgets.QGridLayout(self.gb_examples)
        for i, (ex_k, ex_v) in enumerate(self.examples.items()):
            rb = QtWidgets.QRadioButton(str(ex_k), self.gb_examples)
            if (self.args.example == ex_k) or \
                (self.args.example == '' and i == 0):
                rb.setChecked(True)
                self.selectedExample = str(ex_k)
            
            rb.clicked.connect(partial(self.onExampleSelection, ex_k))
            self.gb_examples_layout.addWidget(rb, i, 0, 1, 1)

            sanitised_help = str(ex_v['help']).split(':')[1].strip()
            help_text = QtWidgets.QLabel(sanitised_help)
            self.gb_examples_layout.addWidget(help_text, i, 1, 1, 1)
            ex_v['rb'] = rb
            self.examplesGroup.addButton(rb)

        # Fill text boxes
        self.tb_projectFolder.setText(self.args.projectpath)
        self.tb_inputFile.setText(self.args.inputfile)
        self.tb_confFile.setText(self.args.config)
        self.tb_outputFile.setText(self.args.savefile)
        self.tb_imgFiles.setText(self.args.path)

        # Link radio buttons with each corresponding groupbox
        rbgb_pairs = [[self.rb_init, self.gb_init],
                      [self.rb_examples, self.gb_examples],
                      [self.rb_openExisting, self.gb_openExisting]]
        for r, g in rbgb_pairs:
            if isinstance(g, QtWidgets.QGroupBox):
                g.setEnabled(False)
                r.toggled.connect(g.setEnabled)
            else:
                g(False)
                r.toggled.connect(g)

        # Set browse buttons functionality
        pbtb_links = [{"button":self.pb_projectFolder, "dest":self.tb_projectFolder, "allowMultiple":False, "filt":None, "existing":False, "directory":True, "onSelected":self.onProjectFolderSelected},
                     {"button":self.pb_inputFile, "dest":self.tb_inputFile, "allowMultiple":False, "filt":"CSV File (*.csv *.CSV);; All Files (*)", "existing":True, "directory":False},
                     {"button":self.pb_confFile, "dest":self.tb_confFile, "allowMultiple":False, "filt":None, "existing":True, "directory":False},
                     {"button":self.pb_outputFile, "dest":self.tb_outputFile, "allowMultiple":False, "filt":"CSV File (*.csv *.CSV);; All Files (*)", "existing":False, "directory":False},
                     {"button":self.pb_imgFiles, "dest":self.tb_imgFiles, "allowMultiple":False, "filt":None, "existing":False, "directory":True},
                    ]


        for pbtb_i in pbtb_links:
            pbtb_i["button"].clicked.connect(partial(self.open_file_dialog, **pbtb_i))

        # Set radiobuttons according to input args
        if self.args.init:
            self.rb_init.setChecked(True)
        elif self.args.example != '':
            self.rb_examples.setChecked(True)
            self.examples[args.example]['rb'].setChecked(True)
        else:
            self.rb_openExisting.setChecked(True)

        # Connect Cancel and OK buttons
        self.buttonBox.accepted.connect(self.onOkeyButton)
        self.buttonBox.rejected.connect(self.onCancelButton)

        # Correct paths when the project folder is not the current directory
        if self.args.projectpath != os.getcwd():
            self.onProjectFolderSelected()

        # Draw GUI:
        self.show()

    def onOkeyButton(self):
        """
        Slot triggered when the OK button is pushed. Saves all displayed values
        within text browsers. Additionally, in the case of selecting an existing
        project, checks if minimal necessary files exist. In the case of
        initialising a project or deploying an example, a small info help
        dialogue is displayed.
        """
        exit_gui = False
        self.args.projectpath = self.tb_projectFolder.toPlainText()

        # Init
        self.args.init = self.rb_init.isChecked()
        
        # Example
        if not self.rb_examples.isChecked():
            self.selectedExample = ''
        self.args.example = self.selectedExample

        # Existing
        self.args.path = self.tb_imgFiles.toPlainText()
        self.args.config = self.tb_confFile.toPlainText()
        self.args.savefile = self.tb_outputFile.toPlainText()
        self.args.inputfile = self.tb_inputFile.toPlainText()

        # Info dialog about init project and example options:
        if self.rb_init.isChecked() or self.rb_examples.isChecked():            
            sub_msg = "Template" if self.rb_init.isChecked() else "Example"
            msg = f"{sub_msg} files will be generated in:\n\"{self.args.projectpath}\"."
            msg += "\n\nNext time, you can directly open the project by executing the following command:"
            msg += f"\n\ngalassify -i {self.args.inputfile} -s {self.args.savefile} -p {self.args.path}"
            msg += "\n\nIf needed, you can download catalogue images by executing:"
            msg += f"\n\nget_images -i {self.args.inputfile} -p {self.args.path}"
            button = QtWidgets.QMessageBox.information(
                self,
                "Generating files",
                msg,
            )
            exit_gui = True

        # If opening an existing project, check that necessary files exist:
        else:
            files = [self.args.inputfile, self.args.path, self.args.config]
            not_found = []
            test_files = True
            for file in files:
                fl = os.path.join(self.args.projectpath, file) if not os.path.isabs(file) else file
                if not os.path.exists(fl):
                    not_found.append(fl)

            if len(not_found) > 0:
                msg = "The following files were not found:\n\n"
                msg += "\n".join(not_found)
                msg += "\n\nPlease, specify them or try initialising a project or selecting an example."
                button = QtWidgets.QMessageBox.critical(
                    self,
                    "Files not found",
                    msg,
                )
            else:
                exit_gui = True

        if exit_gui:
            self.ret = 0
            self.close()

    def closeEvent(self, event):
        """
        Simply digests the close event.

        Parameters
        ----------
        event : QtGui.QCloseEvent
            Event to be accepted.
        """
        event.accept()

    def onCancelButton(self):
        """
        Sets the return value and closes the init gui.
        """
        self.ret = 1
        self.close()

    def onExampleSelection(self, *msg):
        """
        Saves the example selected by the user.

        Parameters
        ----------
        msg : list
            List of selected examples. As radio buttons only allow one selection,
            only the first option is taken.
        """
        self.selectedExample = msg[0]

    def open_file_dialog(self, button=None, dest=None, allowMultiple=False, filt=None, existing=False, directory=False, onSelected=None):
        """
        Opens a dialog to chose files and folders. Then, fills the corresponding
        text boxes with the chosen path to the selected element.

        Parameters
        ----------
        button : QtWidgets.QPushButton, optional
            Button from which the signal was triggered. Not used in this method.
        dest : QtWidgets.QTextBrowser
            Text browser to update when user selects a folder or an element.
        allowMultiple : bool, optional
            Allow the user to select only one element (False) or several (True).
        filt : str, optional
            List of allowed extensions when selecting a file, separated by ";;".
            Example: "CSV File (*.csv *.CSV);; All Files (*)"
        existing : bool, optional
            Force user to select an existing file (True) or allow it to chose a
            filename and a path for a new file to be created (False).
        directory : bool, optional
            Force user to only select a directory (True) or a file (False).
        onSelected : method, optional
            Optional method to call whenever a file or folder is chosen.
        """
        dialog = QtWidgets.QFileDialog(self)
        fileMode = None
        if directory:
            fileMode = QtWidgets.QFileDialog.FileMode.Directory
        elif existing:
            if allowMultiple:
                fileMode = QtWidgets.QFileDialog.FileMode.ExistingFiles
            else:
                fileMode = QtWidgets.QFileDialog.FileMode.ExistingFile
        else:
            fileMode = QtWidgets.QFileDialog.FileMode.AnyFile
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)

        dialog.setFileMode(fileMode)
        if filt:
            dialog.setNameFilter(filt)

        if dialog.exec():
            filenames = dialog.selectedFiles()
            if filenames:
                txt = str(filenames) if allowMultiple else str(filenames[0])
                dest.setText(txt)
        
        if onSelected:
            onSelected()
    
    def onProjectFolderSelected(self):
        """
        Method called each time a new project folder is chosen
        """
        tb_args_pairs = [[self.tb_inputFile, self.args.inputfile],
                        [self.tb_confFile, self.args.config],
                        [self.tb_outputFile, self.args.savefile],
                        [self.tb_imgFiles, self.args.path]]

        for tb, arg in tb_args_pairs:
            if not os.path.isabs(arg):
                tb.setText(os.path.join(self.tb_projectFolder.toPlainText(), arg))

    def getResults(self):
        """
        Gets the results of the execution of the initial GUI.

        Returns
        -------
        ret: int
            Return value of the execution of the initial GUI. Possible values:
            -1: Exit not expected.
             0: User pushed OK button.
             1: User pushed Cancel button.
        args: argparse.Namespace
            Args that include the values entered in the CLI plus the modifications
            done by the user graphically.
        """
        return self.ret, self.args
