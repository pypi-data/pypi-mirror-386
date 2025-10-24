#! /usr/bin/python3
"""
GALAssify (:mod:`galassify.galassify`)
======================================

Main module.
"""
import os, sys
from PyQt5 import QtWidgets

from . import utils, gui, initgui
from galassify import __version__

def main():
    """
    Main execution.

    Actions:
    - Get input args
    - Run: gui | cmd menu
    """
    args = utils.getOptions(__version__)
    if args.gui:
        ret, utils.args = initgui.opengui(args)
        if ret != 0:
            return
    
    run_gui_flag = False
    os.chdir(utils.args.projectpath)
    if utils.args.init:
        utils.init_flag()
    elif args.example != '':
        utils.example_flag(utils.args.example)
        run_gui_flag = utils.args.gui
    elif utils.exist_basic_files():
        run_gui_flag = True
    else:
        utils.run_menu()

    if run_gui_flag:
        run_gui(args)


def run_gui(args) -> None:
    """
    Run application.

    Parameters
    ----------
    args : argparser.Namespace
        Parsed cmd arguments
    """
    selectedFiles, selectedGroups = utils.getFiles()
    if len(selectedFiles) > 0:
        if args.list:
            print(selectedFiles.filename)
        else:
            print(f"INFO:\t{str(len(selectedFiles))} galaxies found in selected group(s).")
            df = selectedFiles # utils.expand_df(selectedFiles)
            app = QtWidgets.QApplication(sys.argv)
            window = gui.Ui(df, selectedGroups)
            app.exec_()
    else:
        print('ERROR:\tNo files found with the given arguments.')
        print('HINT:\tDid you populate your .csv file?')


if __name__ == '__main__':
    sys.exit(main())
