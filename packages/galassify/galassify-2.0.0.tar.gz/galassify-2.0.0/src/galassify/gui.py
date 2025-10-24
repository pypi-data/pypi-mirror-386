"""
GUI (:mod:`galassify.gui`)
==========================

This module contains the main GUI functionality and helper fuctions.

Classes
-------

Ui
"""
from pathlib import Path
import json
import pandas as pd
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QObject, QEvent, QSize, QCoreApplication
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMessageBox

from . import utils, widgets


class Ui(QtWidgets.QMainWindow):
    """
    The main GUI class, containing all widgets instances and connections
    between all their signals and slots.

    Parameters
    ----------
    df : pd.DataFrame
        Input data to present to the user.
    selectedGroups : list
        If the data can be grouped by a column value, this parameter lists
        which groups will be displayed in the GUI.
    """
    def __init__(self, df:pd.DataFrame, selectedGroups:list):
        super(Ui, self).__init__()
        uic.loadUi(str(utils.getPackageResource('gui.ui')), self)

        self.title = 'GALAssify ' + utils.getVersion()
        self.setWindowIcon(
            QIcon(
                str(utils.getPackageResource('res/window_icon.png'))
            )
        )

        # Load data frame and make it accessible along the class:
        # self.df = df # do this later
        self.groups = selectedGroups
        self.has_groups = self.groups is not None

        # Find buttons:
        pb_prev = self.findChild(QtWidgets.QPushButton, 'pb_prev')
        pb_prev.clicked.connect(self.prev_row)
        pb_next = self.findChild(QtWidgets.QPushButton, 'pb_next')
        pb_next.clicked.connect(self.next_row)
        self.pb_save = self.findChild(QtWidgets.QPushButton, 'pb_save')
        self.pb_save.clicked.connect(self.save_row)
        # self.pb_clear = self.findChild(QtWidgets.QPushButton, 'pb_clear')
        # self.pb_clear.clicked.connect(self.clear_morphology_rb)

        # Find actions in Menu bar:
        act_exit = self.findChild(QtWidgets.QAction, 'act_exit')
        act_exit.triggered.connect(self.exit)
        act_allSavedData = self.findChild(QtWidgets.QAction, 'act_allSavedData')
        act_allSavedData.changed.connect(lambda: self.toggleAIDVisibility(act_allSavedData))

        # Find Splitters:
        mainSplitter = self.findChild(QtWidgets.QSplitter, 'mainSplitter')
        mainSplitter.splitterMoved.connect(self.splitterResizeEvent)

        # For next release: Hidable progress bar:
            # Find Groupboxes:
            #self.gb_galList = self.findChild(QtWidgets.QGroupBox, 'gb_galList')
            #print(self.gb_galList)
            #self.progress = QtGui.QProgressBar(self)

        # Import config
        try:
            file_config = utils.args.config
            with open(file_config, 'r') as f:
                config:dict = json.loads(f.read())
                if not 'form' in config.keys():
                    err_str = "ERROR:\t'form' key not found in config file. "\
                        "Please, check if this is an old configuration file "\
                        "from an older version of GALAssify.\n"\
                        "If needed, use one of the included examples to "\
                        "generate a valid one."
                    raise RuntimeError(err_str)
            
        except Exception as e:
            print(e.__str__())
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText(e.__str__())
            msg.setWindowTitle("Error")
            msg.exec_()
            exit(-1)

        # Create right gui
        wcols = 3 # no. cols in each row
        wcount = 0 # pointer to current col
        policy = QtWidgets.QSizePolicy.Policy
        gb_img:QtWidgets.QWidget = self.findChild(QtWidgets.QGroupBox, 'gb_img')

        splitter_img = QtWidgets.QSplitter(Qt.Horizontal)
        if 'filename' in df.columns and 'fits' in df.columns:
            splitter_img.splitterMoved.connect(self.splitterResizeEvent)

        splitter_main = QtWidgets.QSplitter(Qt.Vertical)
        splitter_main.splitterMoved.connect(self.splitterResizeEvent)

        splitter_main.addWidget(splitter_img)

        gb_img.layout().addWidget(splitter_main)

        if 'fits' in df.columns:
            # Get fits display configuration
            if 'display' in config:
                if 'fits' in config['display']:
                    display_opts = config['display']['fits']
            # Add clickable image widget
            widget = widgets.ClickableImage(img_type='FITS', display_opts=display_opts)
            splitter_img.addWidget(widget)
            #gb_img.layout().addWidget(widget, 0, 0, 1, wcols/2) # Full row width
            wcount += wcols
            # Save widget:
            self.widget_fitsimg = widget

        if 'filename' in df.columns:
            # Add image container widget
            widget = None
            if 'display' in config:
                if 'bitmap' in config['display']:
                    if config['display']['bitmap'] == 'clickable':
                        widget = widgets.ClickableImage(img_type='BITMAP')
            if widget == None:
                widget = widgets.StaticImage()
            splitter_img.addWidget(widget)
            #gb_img.layout().addWidget(widget, wcount//wcols, wcount%wcols, 1, wcols/2) # Full row width
            wcount += wcols
            # Save widget:
            self.defaultImgPath = utils.getPackageResource('res/image_not_found.png')
            self.widget_bitmapimg = widget

        # Instances to widget saves
        self.rbg = {} # buttongroups
        self.rb = {} # radiobuttons
        # self.rbTypes, self.rbNames = [], []
        self.cb = {} # checkboxs
        # self.cbColumns, self.cbNames = [], []
        self.tb = {} # textbox

        # Add dynamic widgets
        frame = QtWidgets.QFrame()
        frame.setLayout(QtWidgets.QGridLayout())
        splitter_main.addWidget(frame)

        for tconf in config['form']:
            tconf:dict
            # cols = 2 # default cols inside each widget
            # count = 0 # pointer to current col inside widget
            # self._cols = cols
            # self._count = count
            try:
                # check basic define params
                if 'id' in tconf.keys():
                    id:str = tconf['id']

                name = id.capitalize()
                if 'name' in tconf.keys():
                    name = tconf['name']

                if 'type' not in tconf.keys():
                    print(f"type of {id}:{name} not specified")
                    continue

                # size policy
                if wcount%wcols == 0: # first column
                    wpol = QtWidgets.QSizePolicy(policy.Preferred, policy.Preferred)
                elif wcount%wcols == wcols-1: # last column
                    wpol = QtWidgets.QSizePolicy(policy.Maximum, policy.Preferred)
                else:
                    wpol = QtWidgets.QSizePolicy(policy.Minimum, policy.Preferred)

                # COMMENTBOX
                if tconf['type'] == 'text':
                    gb = widgets.CommentBox(self, tconf, wpol)
                # CHECKBOX
                elif tconf['type'] == 'checkbox':
                    gb = widgets.CheckBoxGroup(self, tconf, wpol)
                # RADIOBUTTON TYPE
                elif tconf['type'] == 'radiobutton':
                    gb = widgets.RadioButtonGroup(self, tconf, wpol)
                else:
                    print(f"{tconf['type']} not implemented")

                frame.layout().addWidget(gb, wcount//wcols, wcount%wcols)
                wcount += 1
            except:
                raise

        # Dynamic COLUMNS
        utils.IDS['FILE'] = list(df.columns)

        utils.IDS['WIDGET'] = []
        if 'fits' in df.columns:
            utils.IDS['WIDGET'].extend(['fits_coords'])

        if hasattr(self, 'widget_bitmapimg'):
            if isinstance(self.widget_bitmapimg, widgets.ClickableImage):
                utils.IDS['WIDGET'].extend(['img_points'])

        utils.IDS['TB'] = list(self.tb.keys())
        for _, cb in self.cb.items():
            utils.IDS['CB'].extend(list(cb.keys()))

        utils.IDS['RBG'] = list(self.rbg.keys())
        for _, rb in self.rb.items():
            utils.IDS['RB'].extend(list(rb.keys()))
        utils.IDS['RB'].extend([""])

        utils.COLUMNS = utils.IDS['FILE'] + utils.IDS['WIDGET'] + utils.IDS['RBG'] + utils.IDS['CB'] + utils.IDS['TB']
        for v in ['ra', 'dec']:
            if v in utils.COLUMNS:
                utils.COLUMNS.remove(v)

        utils.COLUMNS.extend(['processed'])
        utils.COLUMNS.extend(['fullpath'])
        if 'ra' in df.columns and 'dec' in df.columns:
            utils.COLUMNS.extend(['ra', 'dec'])

        ## OLD
        # Find checkboxes:
        # self.cbColumns = utils.getCheckBoxesColumns()
        # self.cbNames = ['cb_' + x for x in self.cbColumns]
        # self.cb = {}
        # for i, cb in enumerate(self.cbNames):
        #     self.cb[self.cbColumns[i]] = self.findChild(QtWidgets.QCheckBox,
        #                                                 self.cbNames[i])

        # Find radio buttons:
        # self.rbTypes = utils.getRadioButtonsMorphology()
        # self.rbNames = ['rb_' + x for x in self.rbTypes]
        # self.rb = {}
        # for i, cb in enumerate(self.rbNames):
        #     self.rb[self.rbTypes[i]] = self.findChild(QtWidgets.QRadioButton,
        #                                                 self.rbNames[i])

        # find comment box:
        # self.commentBox = self.findChild(QtWidgets.QPlainTextEdit,
        #                                  'commentBox')
        # self.commentBox.installEventFilter(self) # Set enter as save row

        # Find image frame:
        # self.imageLabel = self.findChild(QtWidgets.QLabel, 'imageLabel')
        # # self.imageLabel.setScaledContents(True)
        # self.imageLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # self.defaultImgPath = Path("res") / Path("Cavity.png")
        # # self.showImage(self.defaultImgPath)
        # # Show image with updated windows size:
        # self.showImage(self.defaultImgPath)

        # Find table:
        self.fileList = self.findChild(QtWidgets.QTableWidget, 'fileList')
        # Fill the list:
        self.df = utils.expand_df(df)
        self.fillList()

        # Draw GUI:
        self.show()

        # self.load_row() # not needed first row loaded on fillList
        self.showImage(self.imgPath) # img appears streched, so refresh img

    # List helpers:

    def create_table_item(self, value, role=Qt.DisplayRole):
        """
        Create a table item with a given value.

        Parameters
        ----------
        value : any
            Value to be setted in the item.
        role : int, optional
            Used by the view to indicate to the model which type
            of data it needs, by default Qt.DisplayRole

        Returns
        -------
        QtWidgets.QTableWidgetItem
            QTableWidget Item ready to be embedded in a QT table.
        """
        item = QtWidgets.QTableWidgetItem()
        item.setData(role, value)
        return item

    def fillList(self, showAllSavedData:bool = False) -> None:
        """
        Initialise the main file table in the GUI by setting the headers,
        columns, rows, and other properties.

        Parameters
        ----------
        showAllSavedData : bool, optional
            If True, the already classified data will be displayed.
            If False, all data marked as classified will be hidden.
            By default False.
        """
        header_full = ['Group', 'Galaxy', 'Processed', 'Ra', 'Dec', 'Filename', 'Fits'] # base header
        header_valids =[h.capitalize() for h in utils.IDS['FILE'] + ['Processed']] # input file cols + 'Processed'
        additional_cols = list(set(h for h in utils.IDS['FILE']) - set(h.lower() for h in header_full)) # Additional columns in input csv
        header = [h for h in header_full if h in header_valids] + additional_cols # contruct header

        #self.fileList.setRowCount(len(self.df.index))
        self.fileList.setColumnCount(len(header))
        self.fileList.setHorizontalHeaderLabels(header)
        self.fileList.horizontalHeaderItem(header.index('Processed')).setTextAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Make table not editable:
        self.fileList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.fileList.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.fileList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        # Call function on new row selected:
        self.fileList.itemSelectionChanged.connect(self.load_row)

        # I know, I know! This is not the Jedi way. It works anyway.
        # I'll do this better in next release:
        for i in range(self.fileList.rowCount()):
            self.fileList.removeRow(i)

        self.fileList.setRowCount(len(self.df.index))

        for i, row in self.df.iterrows():
            c = 0
            # Place group data in integer format:
            if self.has_groups:
                self.fileList.setItem(i, c, self.create_table_item(row['group']))
                c += 1
            # Place galaxy data in integer format:

            self.fileList.setItem(i, c, self.create_table_item(row['galaxy']))
            c += 1
            # Set Icon in the row:
            self.fileList.setCellWidget(i, c, self.getIconCell(row['processed']))
            c += 1
            #Set RA and Dec data:
            if 'ra' in row and 'dec' in row:
                self.fileList.setItem(i, c, self.create_table_item(float(row['ra'])))
                c += 1
                self.fileList.setItem(i, c, self.create_table_item(float(row['dec'])))
                c += 1
            # Place filename in the row:
            if 'filename' in row:
                self.fileList.setItem(i, c, self.create_table_item(str(row['filename'])))
                c += 1
            # Place fits in the row:
            if 'fits' in row:
                self.fileList.setItem(i, c, self.create_table_item(str(row['fits'])))
                c += 1
            # Place data in additional columns
            for ac in additional_cols:
                self.fileList.setItem(i, c, self.create_table_item(str(row[ac])))
                c += 1

            if self.has_groups:
                if (not showAllSavedData) and (row['group'] not in self.groups):
                    self.fileList.hideRow(i)

        # Order by RA coordinate:
        self.fileList.setSortingEnabled(True)
        if self.has_groups:
            self.fileList.sortItems(3, Qt.AscendingOrder)
        else:
            self.fileList.sortItems(2, Qt.AscendingOrder)

        # Do the resize of the columns by content:
        self.fileList.resizeColumnsToContents()

        # Start with table selected:
        self.fileList.setFocus()

        # Start in the first visible row when GUI is presented:
        for i in range(self.fileList.rowCount()):
            if not self.fileList.isRowHidden(i):
                self.fileList.selectRow(i)
                break


    # Button methods:

    def save_row(self) -> None:
        """
        Save button slot. Saves the current selected row in the output file.
        """
        index = self.fileList.selectionModel().selectedRows()[0].row()
        try:
            # if self.has_groups:
            #     fn = self.fileList.item(index, 5).text()
            # else:
            #     fn = self.fileList.item(index, 4).text()

            # Identify row by filename (better than index)
            # item_index = self.df['filename'] == fn
            if self.has_groups:
                grp = self.fileList.item(index, 0).text()
                gal = self.fileList.item(index, 1).text()
                item_index = self.df.index[(self.df['group']==grp) & (self.df['galaxy']==gal)]
            else:
                gal = self.fileList.item(index, 0).text()
                item_index = self.df.index[self.df['galaxy']==gal]

            self.df.loc[item_index, 'processed'] = True
            if self.has_groups:
                self.fileList.setCellWidget(index, 2,
                                            self.getIconCell(True))
            else:
                self.fileList.setCellWidget(index, 1,
                                            self.getIconCell(True))

            for id, bg in self.rbg.items():
                selected = ''
                if bg.checkedButton() is not None:
                    idChecked:str = bg.checkedButton().objectName()
                    selected = idChecked.split('_',1)[-1]
                    # refactor rbTypes and rbNames?
                    #selected = self.rbTypes[self.rbNames.index(idChecked)]
                self.df.loc[item_index, id] = selected
            # for radio in self.rbTypes:
            #     if(self.rb[radio].isChecked()):
            #         self.df.loc[item_index, 'morphology'] = radio
            #         break
            #     else:
            #         self.df.loc[item_index, 'morphology'] = utils.getMorphology()[-1]

            for id, cb in self.cb.items():
                for eid, wcb in cb.items():
                    self.df.loc[item_index, eid] = wcb.isChecked()
            # for column in self.cbColumns:
            #     self.df.loc[item_index, column] = self.cb[column].isChecked()

            for id, tb in self.tb.items():
                self.df.loc[item_index, id] = tb.toPlainText().replace('\n', '')
            # self.df.loc[item_index, 'comment'] = self.commentBox.toPlainText().replace('\n', '')

            if hasattr(self, 'widget_fitsimg'):
                self.df.at[item_index.item(), 'fits_coords'] = self.widget_fitsimg.get_coords()  # not working with .loc

            if hasattr(self, 'widget_bitmapimg'):
                if isinstance(self.widget_bitmapimg, widgets.ClickableImage):
                    self.df.at[item_index.item(), 'img_points'] = self.widget_bitmapimg.get_points()

            self.fileList.selectRow(index+1)

            utils.save_df(self.df)

        #except (AttributeError, KeyError):
        except (KeyError) as e:
            print(f"WARNING:\tEmpty item. [{e}]")
        #   imgPath = self.defaultImgPath


    def load_row(self) -> None:
        """
        Slot called when a new row is selected. Loads all the data (image, fits,
        and classification) of the selected item into the classification panel
        of the GUI.
        """
        index = self.fileList.selectionModel().selectedRows()[0].row()
        try:
            if self.has_groups:
                grp = self.fileList.item(index, 0).text()
                gal = self.fileList.item(index, 1).text()
                item_index = (self.df['group']==grp) & (self.df['galaxy']==gal)
            else:
                gal = self.fileList.item(index, 0).text()
                item_index = self.df['galaxy']==gal

            item = self.df.loc[item_index]
            if 'fullpath' in item:
                self.imgPath = item['fullpath'].item()
            else:
                self.imgPath = None

            if 'fits_coords' in item:
                self.fitsCoords = item['fits_coords'].item()
            else:
                self.fitsCoords = None

            if 'img_points' in item:
                self.imgPoints = item['img_points'].item()
            else:
                self.imgPoints = None

            windowTitle = ''
            if self.has_groups:
                grp = str(item['group'].item())
                windowTitle += f"Grp: {grp} | "
            gal = str(item['galaxy'].item())
            windowTitle += f"Gal: {gal} | {self.title}"
            self.setWindowTitle(windowTitle)

            if self.has_groups:
                self.fileList.setCellWidget(index, 2,
                                            self.getIconCell(item['processed'].item()))
            else:
                self.fileList.setCellWidget(index, 1,
                                            self.getIconCell(item['processed'].item()))

            # radiobuttons
            for id, bg in self.rbg.items():
                bg.clear_ButtonGroup()
                # self.clear_ButtonGroup(bg)
                selected = item[id].item()
                if selected in self.rb[id].keys():
                    # idChecked = self.rbNames[self.rbTypes.index(selected)] # refactor rbTypes and rbNames?
                    self.rb[id][selected].setChecked(True)

            # for radio in self.rbTypes:
            #     if(item['morphology'].item() == radio):
            #         self.rb[radio].setChecked(True)

            # checkboxes
            for id, cb in self.cb.items():
                for eid, wcb in cb.items():
                    wcb.setChecked(item[eid].item())
            # for cb in self.cbColumns:
            #     self.cb[cb].setChecked(item[cb].item())

            # textboxes
            for id, tb in self.tb.items():
                comment = item[id].item()
                if pd.notnull(comment):
                    tb.setPlainText(str(comment))
                else:
                    tb.setPlainText('')
            # comment = item['comment'].item()
            # if not pd.isnull(comment):
            #     self.commentBox.setPlainText(str(comment))
            # else:
            #     self.commentBox.setPlainText('')

            if hasattr(self, 'widget_fitsimg'):
                fname = Path(utils.args.path) / Path(item['fits'].item())
                self.widget_fitsimg.load_file(fname, coords=self.fitsCoords)

        except (AttributeError, KeyError) as e:
            print(f"WARNING:\tEmpty item. [{e}]")
            self.imgPath = self.defaultImgPath
            self.setWindowTitle(self.title)
            for _, cb in self.cb.items():
                for _, wcb in cb.items():
                    wcb.setChecked(False)
            # for cb in self.cbColumns:
            #     self.cb[cb].setChecked(False)

        self.showImage(self.imgPath)

    def next_row(self) -> None:
        """
        Move one line forward in the file list.
        """
        index = self.fileList.selectionModel().selectedRows()[0].row()
        self.fileList.selectRow(index+1)


    def prev_row(self) -> None:
        """
        Move one line backwards in the file list.
        """
        index = self.fileList.selectionModel().selectedRows()[0].row()
        self.fileList.selectRow(index-1)


    # Actions helpers

    def exit(self) -> None:
        """
        Exits the GUI.
        """
        QCoreApplication.quit()

    def toggleAIDVisibility(self, act:QtWidgets.QAction) -> None:
        showAllSavedData = act.isChecked()
        if not self.has_groups:
            return
        for i in range(self.fileList.rowCount()):
            group = self.fileList.item(i, 0).text()
            if (not showAllSavedData) and (group not in self.groups):
                self.fileList.hideRow(i)
            else:
                self.fileList.showRow(i)

    # Image helpers:

    def showImage(self, imageFile:str) -> None:
        """
        Shows the given image file in the classification panel.

        If not found, a default image is shown.

        Parameters
        ----------
        imageFile : str
            Path to the file to be displayed.
        """
        if hasattr(self, 'widget_bitmapimg'):
            if imageFile and Path(imageFile).is_file():
                fname = str(imageFile)
            else:
                fname = str(self.defaultImgPath)

            if isinstance(self.widget_bitmapimg, widgets.ClickableImage):
                self.widget_bitmapimg.load_file(fname, points=self.imgPoints)
            else:
                self.widget_bitmapimg.set_pixmap(QPixmap(fname))

        # if hasattr(self, 'widget_fitsimg'):
        #     self.widget_fitsimg.canvas.draw()

    def getIconCell(self, active:bool) -> QtWidgets.QWidget:
        """
        Create and format a QtWidget with an icon to be embedded in a cell of
        the file list.

        Parameters
        ----------
        active : bool
            If True, a green check icon is embedded.
            If False, a red cross mark icon is embedded.

        Returns
        -------
        QtWidgets.QWidget
            QtWidget with the embedded icon.
        """
        iconLabel = QtWidgets.QLabel()
        icon_true = str(utils.getPackageResource('res/icon_true.png'))
        icon_false = str(utils.getPackageResource('res/icon_false.png'))
        iconSize = QSize(12, 12)

        if active:
            icon = icon_true
        else:
            icon = icon_false

        iconLabel.setMaximumSize(iconSize)
        iconLabel.setScaledContents(True)
        iconLabel.setPixmap(QPixmap(icon))

        cell_widget = QtWidgets.QWidget()
        lay_out = QtWidgets.QHBoxLayout(cell_widget)
        lay_out.addWidget(iconLabel)
        lay_out.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_out.setContentsMargins(0, 0, 0, 0)
        cell_widget.setLayout(lay_out)
        return cell_widget

    # Keyboard shortcuts helpers

    def eventFilter(self, obj:QObject, event:QEvent) -> bool:
        """
        Filters the keyboard events triggered by the user to capture and
        process some events before the default Qt event filter.

        Parameters
        ----------
        obj : QObject
            Object that triggers the event.
        event : QEvent
            Event triggered by the object.

        Returns
        -------
        bool
            If True, all events were captured.
            Else, there are still events to process.
        """
        if event.type() == QEvent.KeyPress: # and obj is self.commentBox:
            if event.key() == (Qt.Key.Key_Return or Qt.Key.Key_Enter): # and self.commentBox.hasFocus():
                # If TextBox move focus
                for _, tb in self.tb.items():
                    if tb.hasFocus():
                        tb.parent().focusNextChild()
                        #tb.clearFocus()
                        #self.fileList.setFocus()
                        return True
                # save if not in TextBox
                self.pb_save.animateClick()
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event:QEvent) -> None:
        """
        Function called when a key is pressed.

        Currently, only ESC key is captured. When the user press ESC, the file lists
        clears the selected item.

        Parameters
        ----------
        event : QEvent
            Event triggered by the Qt event listener.
        """
        key = event.key()
        # if key == Qt.Key_F1 and not self.commentBox.hasFocus():
        #     self.commentBox.setFocus()

        # if key == Qt.Key_Escape and self.commentBox.hasFocus():
        #     self.commentBox.setPlainText('')
        #     self.fileList.setFocus()

        if key == Qt.Key.Key_Escape:
            for _, tb in self.tb.items():
                if tb.hasFocus():
                    tb.setPlainText('')
            self.fileList.setFocus()

    # Resizing helpers

    def resizeEvent(self, event:QEvent) -> None:
        """
        Function called when the user resizes the GUI window.

        Asks the GUI to redraw the image of the selected row to draw it
        fitted to the new windows size.

        Parameters
        ----------
        event : QEvent
            Event triggered by the Qt event listener.
        """
        # Re-draw image:
        if hasattr(self, 'widget_bitmapimg'):
            if isinstance(self.widget_bitmapimg, widgets.StaticImage):
                self.widget_bitmapimg.set_pixmap(QPixmap(str(self.imgPath)))
        # self.showImage(self.imgPath)

    def splitterResizeEvent(self, pos, index) -> None:
        """
        Slot called when the user resizes the GUI window content by sliding the
        central QSlider.

        Asks the GUI to redraw the image of the selected row to draw it fitted to the new windows size.

        Parameters
        ----------
        pos : any
            New position of the splitter.
        index : any
            Index of the splitter handle.
        """
        # Re-draw image:
        self.showImage(self.imgPath)
