"""
Widgets (:mod:`galassify.widgets`)
==================================

This module contains various widget classes to be loaded in the GUI.

Classes
-------

ClickableImage
StaticImage
CheckBoxGroup
RadioButtonGroup
CommentBox


Helper Classes
--------------

BaseWidgetGroup
CustomButtonGroup

"""
import typing
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import pandas as pd
import numpy as np

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
    )
from matplotlib.figure import Figure
from matplotlib.image  import imread

from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.visualization import ImageNormalize, BaseInterval, MinMaxInterval, PercentileInterval, ZScaleInterval, AsinhStretch, SqrtStretch, HistEqStretch
import warnings

from . import utils


policy = QtWidgets.QSizePolicy.Policy

ds9 = None

def tests_import_pyds9() -> None:
    """
    Import ds9 if installed
    """
    global ds9
    try:
        import pyds9 as ds9
    except ImportError:
        print("Module pyds9 not found. DS9 interface is disabled.")

class ClickableImage(QtWidgets.QWidget):
    """
    An interactive image (FITS or BITMAP) widget with point annotations.

    Needs to be added to the canvas in GUI.
    Image can be annotated with points that are saved in the output file.

    Parameters
    ----------
    has_toolbar : bool, optional
        Whether to add toolbar to the widget or not, by default True.
    img_type : str, optional
        Image type: 'FITS' for *.fits files. BITMAP for *.jpeg, *.png, or another image files. By default, 'FITS'.
    """

    def __init__(self, has_toolbar:bool = True, img_type:str = 'FITS', display_opts={}, *args, **kwargs):
        super(ClickableImage, self).__init__(*args, **kwargs)

        self.display_opts = display_opts
        self.setMinimumSize(150,170)
        self.setSizePolicy(QtWidgets.QSizePolicy(policy.Expanding, policy.Expanding))
        #self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        # Create internal canvas
        layout = QtWidgets.QGridLayout(self)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.isfits = True if img_type == 'FITS' else False
        self.button = QtWidgets.QPushButton(None)
        self.button.setSizePolicy(QtWidgets.QSizePolicy(policy.Maximum, policy.Fixed))
        self.button.setText("Open in ds9")

        tests_import_pyds9()

        if ds9:
            self.button.clicked.connect(self.callback_ds9)
        else:
            self.button.setEnabled(False)
            self.button.setToolTip('''Package <b>\'pyds9\'</b> not found.
                Install it for using this feature.''')

        if has_toolbar:
            self.toolbar = NavigationToolbar(self.canvas, coordinates=False)
            layout.addWidget(self.toolbar, 0, 0, 1, 1)
            layout.addWidget(self.button, 0, 1, 1, 1)

        layout.addWidget(self.canvas, 1, 0, 1, 2)
        self.canvas.mpl_connect('button_press_event', self.callback_button_press)

    # funtionality
    def load_file(self, file:str, coords:list = None, points:list = None) -> None:
        """
        Change current file (and its annotated points/coordinates) in the widget instance.

        Used when changing from one row to the next one.

        Parameters
        ----------
        file : str
            BITMAP or FITS file to be loaded in the widget.
        coords : list, optional
            List of previously made annotation on FITS image (ra,dec) tuples, by default None.
        points : list, optional
            List of previously made annotation on BITMAP image (x,y) tuples, by default None.
        """
        self.add_image(file)

        if self.isfits:
            if coords is None or len(coords)==0:
                return
            hdu = self.projection
            for coord in coords:
                ra, dec = coord
                point = SkyCoord(ra, dec, unit=(u.deg, u.deg)).to_pixel(self.projection)
                self.add_point(point)
        else:
            if not points or \
                not isinstance(points, list):
                return
            for point in points:
                self.add_point(point)

    def add_image(self, path_img:str) -> None:
        """
        Load the image file 'path_img' and update the canvas.

        Parameters
        ----------
        path_img : str
            Path of the file to be loaded.
        """
        self.path_img = path_img

        try:
            if self.isfits:
                with fits.open(self.path_img) as hdul:
                    self.projection = WCS(hdul[0].header)
                    data = hdul[0].data
                
            else:
                #with open(self.path_img) as img:
                self.projection = None
                data = imread(self.path_img)

        except OSError as e:
            print(e)
            return

        # Add main axes
        if hasattr(self, 'ax'):
            self.ax.remove()
        self.ax = self.figure.add_axes([0,0,1,1], projection=self.projection)
        self.ax.set_axis_off()

        # Add image
        if self.isfits:
            # Normalise FITS image
            normalize = ImageNormalize(data, interval=PercentileInterval(99.5), stretch=AsinhStretch())
            origin = 'lower'
        else:
            normalize = None
            origin = 'upper'
        self.ax.imshow(data,
                       origin=origin,
                       norm=normalize,
                       aspect='equal',
                       **self.display_opts)

        # Create point arrays and scatter plot
        self.coords = np.empty([0,2], dtype=float)
        self.points = np.empty([0,2], dtype=int)
        self._scatter = self.ax.scatter(None, None, color='r', marker='2')

        # Update canvas
        self.canvas.draw_idle()

    def update_points(self) -> None:
        """
        Refresh canvas after adding/removing points.
        """
        # print(self.coords, self.points)
        self._scatter.set_offsets(self.points)
        self.canvas.draw_idle()

    def add_point(self, point: list) -> None:
        """
        Add a point to the canvas.

        Parameters
        ----------
        point : list
            [x,y] point to be added.
        """
        if self.isfits:
            hdu = self.projection
            coords = hdu.pixel_to_world(point[0], point[1])
            point_deg = np.round([coords.ra.deg, coords.dec.deg], 6)
            self.coords = np.insert(self.coords, 0, point_deg, axis=0)

        self.points = np.insert(self.points, 0, point, axis=0)
        self.update_points()

    def delete_point(self, point: list) -> None:
        """
        Delete a point from the canvas.

        Parameters
        ----------
        point : list
            [x,y] point to be added.
        """
        if self.points.size == 0:
            return
        # find nearest point from the click by euclidean distance
        idx_min = np.sum((self.points-point)**2, axis=1, keepdims=True).argmin(axis=0)

        if self.isfits:
            self.coords = np.delete(self.coords, idx_min, axis=0)

        self.points = np.delete(self.points, idx_min, axis=0)
        self.update_points()

    def get_coords(self) -> list:
        """
        Convert coords list of lists to list of tuples and return

        Returns
        -------
        list
            List of coord tuples.
        """
        return [tuple(c) for c in self.coords.tolist()]

    def get_points(self) -> list:
        """
        Convert points list of lists to list of tuples and return

        Returns
        -------
        list
            List of point tuples.
        """
        return [tuple(p) for p in self.points.tolist()]

    # button callbacks
    def callback_button_press(self, event) -> None:
        """
        Callback to be used when clicking the FITS image.

        Used for adding and deleting points.
        """
        x, y = event.xdata, event.ydata
        if x is None or y is None: # out of bounds
            return
        point = [x, y]
        if event.dblclick and event.button == 1: # left doubleclick
            self.add_point(point)
        elif event.dblclick and event.button == 3: # right doubleclick
            self.delete_point(point)

    def callback_ds9(self) -> None:
        """
        Callback to be used when clicking open DS9 button.

        Opens DS9 with the FITS file.
        """
        if ds9:
            if hasattr(self, 'ds9'):
                ds9.ds9_xpans() # if not called, opening new after closing one fails (dont know why :D)
            try:
                self.ds9 = ds9.DS9(wait=20) # Open ds9 (this assumes no ds9 instance is yet running)
                if self.isfits:
                    self.ds9.set(f"file '{self.path_img}'") # Load file
                    # Change the colormap and scaling
                    self.ds9.set('cmap viridis')
                    self.ds9.set('scale log')
                else:
                    self.ds9.set(f"jpeg '{self.path_img}'") # Load file

                self.ds9.set('zoom to fit') # Zoom to fit
            except ValueError as e:
                print(f"ERROR:\tpyds9 exception: {e.__str__()}")
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Error: pyds9 exception")
                msg.setInformativeText(e.__str__())
                msg.setWindowTitle("Error")
                msg.exec_()


class StaticImage(QtWidgets.QLabel):
    """
    A static image widget.

    Needs to be added to the canvas in GUI.
    """

    def __init__(self, *args, **kwargs):
        super(StaticImage, self).__init__(*args, **kwargs)

        self.setObjectName("imageLabel")
        self.setMinimumSize(100,100)
        self.setSizePolicy(QtWidgets.QSizePolicy(policy.Expanding, policy.Expanding))
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """
        Set widget pixel map with loaded image size.

        Parameters
        ----------
        pixmap : QPixmap
            Qt pixmap of the image
        """
        w = self.width()
        h = self.height()
        self.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))


class BaseWidgetGroup(QtWidgets.QGroupBox):
    """
    A base class to be used with widget groups.

    This is used as parent groupbox widget to contain child widgets like:
        checkboxes, radiobuttons or comments.

    Parameters
    ----------
    wconf : dict
        Widget configuration.
    wpolicy : QtWidgets.QSizePolicy
        Widget size policy. See QSizePolicy for more info.

    Raises
    ------
    KeyError
        Missing elements in the wconf dict.
    """

    def __init__(self, wconf:dict, wpolicy:QtWidgets.QSizePolicy) -> QtWidgets.QGroupBox:
        cols = 2 # default cols inside each widget
        count = 0 # pointer to current col inside widget

        if 'id' not in wconf.keys():
            raise KeyError('id is mandatory')
        # check basic define params

        id:str = wconf['id']

        name = id.capitalize()
        if 'name' in wconf.keys():
            name:str = wconf['name']

        # if 'type' not in wconf.keys():
        #     print(f"type of {id}:{name} not specified")
        #     continue

        # # size policy
        # if wcount%wcols == 0: # first column
        #     wpol = QtWidgets.QSizePolicy(policy.Preferred, policy.Preferred)
        # elif wcols-(wcount%wcols) == 1: # last column
        #     wpol = QtWidgets.QSizePolicy(policy.Maximum, policy.Preferred)
        # else:
        #     wpol = QtWidgets.QSizePolicy(policy.Minimum, policy.Preferred)

        super(BaseWidgetGroup, self).__init__(name)

        self.setObjectName(f"gb_{id}")
        self.setSizePolicy(wpolicy)
        #gb.setMinimumSize(50, 150)
        self.setLayout(QtWidgets.QGridLayout())

        self._id = id
        self._cols = cols
        self._count = count

    def addToolTip(self, widget: QtWidgets.QWidget, element:dict) -> None:
        """
        Add tooltip description to the input widget.

        Parameters
        ----------
        widget : QtWidgets.QWidget
            Widget instance to use.
        element : dict
            Widget config dict.
        """
        try:
            widget.setToolTip(f"{element['description']}")
        except KeyError as e:
            print(f"KeyError: {e}")

    def addTexts(widget:any, element:dict) -> None:
        """
        Must be implemented in each 'child' to add texts like id, name or shorcut.

        Parameters
        ----------
        widget : QtWidgets.QWidget
            Widget instance to use.
        element : dict
            Widget configuration dict.
        """
        warnings.warn("Implemented in each child")

class CheckBoxGroup(BaseWidgetGroup):
    """
    A checkbox group widget.

    Needs to be added to the canvas in GUI.

    Parameters
    ----------
    parent : QtWidgets.QMainWindow
        Parent of the widget.
    wconf : dict
        Widget configuration.
    wpolicy : QtWidgets.QSizePolicy
        Widget size policy.
    """

    def __init__(self, parent, wconf:dict, wpolicy:QtWidgets.QSizePolicy, *args, **kwargs):
        super(CheckBoxGroup, self).__init__(wconf, wpolicy, *args, **kwargs)

        cols = self._cols
        count = self._count

        if 'ncolumns' in wconf.keys():
            cols = wconf['ncolumns']

        id = self._id
        if 'elements' in wconf and len(wconf['elements']) > 0:
            parent.cb[id] = {}

        for element in wconf['elements']:
            try:
                eid = element['id']
                wid = f"cb_{eid}"
                # add checkbox
                widget = QtWidgets.QCheckBox(None)
                widget.setObjectName(wid)
                widget.setSizePolicy(QtWidgets.QSizePolicy(policy.Minimum, policy.Fixed))
                self.addTexts(widget, element)
                self.addToolTip(widget, element)

                self.layout().addWidget(widget, count//cols, count%cols)
                count += 1
                # save widget
                parent.cb[id][eid] = widget
                # self.cbColumns.append(eid)
                # self.cbNames.append(wid)

            except KeyError as e:
                print(f"KeyError: {e}")

    def addTexts(self, widget: QtWidgets.QCheckBox, element:dict) -> None:
        """
        Add texts to the input widget (id, name, shortcut).

        Parameters
        ----------
        widget : QtWidgets.QCheckBox
            Widget instance to use.
        element : dict
            Widget configuration dict.
        """
        id, name, shortcut = None, None, None
        try:
            id, name, shortcut = element['id'], element['name'], element['shortcut']
        except KeyError as e:
            if name is None:
                name = id.capitalize()
            print(f"KeyError: {e}")
        finally:
            if shortcut is None:
                widget.setText(name)
            else:
                widget.setText(f"[{shortcut}] {name}")
                widget.setShortcut(shortcut)


class CustomButtonGroup(QtWidgets.QButtonGroup):
    """
    A custom button group widget used for RadioButtonGroup.

    Parameters
    ----------
    id : str
        Group identifier.
    """

    def __init__(self, id) -> None:
        super().__init__()
        self.setObjectName(f"gbb_{id}")

    def clear_ButtonGroup(self) -> None:
        """Clears the selected button group selection.
        """
        if self.checkedButton() is not None:
            self.setExclusive(False)
            self.checkedButton().setChecked(False)
            self.setExclusive(True)


class RadioButtonGroup(BaseWidgetGroup):
    """
    A radiobutton group widget.

    Needs to be added to the canvas in GUI.

    Parameters
    ----------
    parent : QtWidgets.QMainWindow
        Parent of the widget.
    wconf : dict
        Widget configuration.
    wpolicy : QtWidgets.QSizePolicy
        Widget size policy.
    """

    def __init__(self, parent, wconf:dict, wpolicy:QtWidgets.QSizePolicy, *args, **kwargs):
        super(RadioButtonGroup, self).__init__(wconf, wpolicy, *args, **kwargs)

        cols = self._cols
        count = self._count

        if 'ncolumns' in wconf.keys():
            cols = wconf['ncolumns']*2 # *2 -> shortcut and name in 2 rows

        id = self._id
        gbb = CustomButtonGroup(id)

        if 'elements' in wconf and len(wconf['elements']) > 0:
            parent.rb[id] = {}
        for element in wconf['elements']:
            element:dict
            try:
                eid = element['id']
                wid = f"rb_{eid}"
                # radiobutton
                widget = QtWidgets.QRadioButton(None)
                widget.setObjectName(wid)
                widget.setSizePolicy(QtWidgets.QSizePolicy(policy.Minimum, policy.Fixed))
                self.addTexts(widget, element)
                self.addToolTip(widget, element)

                gbb.addButton(widget)
                self.layout().addWidget(widget, count//cols, count%cols)
                count += 1
                # save widget
                parent.rb[id][eid] = widget
                # self.rbTypes.append(eid)
                # self.rbNames.append(wid)

                # shortcut label
                if 'shortcut' in element.keys():
                    widget = QtWidgets.QLabel(None)
                    widget.setSizePolicy(QtWidgets.QSizePolicy(policy.Preferred, policy.Preferred))
                    widget.setText(f"[{element['shortcut']}]")
                    self.layout().addWidget(widget, count//cols, count%cols)
                count += 1
            except KeyError as e:
                print(f"KeyError: {e}")

        if 'add_clear' in wconf.keys() and wconf['add_clear'] is True:
            widget = QtWidgets.QPushButton(None)
            widget.setObjectName(f"pb_clear_{id}")
            widget.setSizePolicy(QtWidgets.QSizePolicy(policy.Minimum, policy.Fixed))

            text = "Clear"
            if 'clear_shortcut' in wconf.keys():
                shortcut = wconf['clear_shortcut']
                text += f" [{shortcut}]"
            widget.setText(text)
            if shortcut is not None:
                widget.setShortcut(shortcut)
            widget.clicked.connect(gbb.clear_ButtonGroup)
            self.layout().addWidget(widget, count//cols, count%cols, 1, cols)

        parent.rbg[id] = gbb

    def addTexts(self, widget: QtWidgets.QRadioButton, element:dict) -> None:
        """
        Add texts to the input widget (id, name, shortcut).

        Parameters
        ----------
        widget : QtWidgets.QRadioButton
            Widget instance to use.
        element : dict
            Widget configuration dict.
        """
        id, name, shortcut = None, None, None
        try:
            id, name, shortcut = element['id'], element['name'], element['shortcut']
        except KeyError as e:
            if name is None:
                name = id.capitalize()
            print(f"KeyError: {e}")
        finally:
            widget.setText(name)
            if shortcut is not None:
                widget.setShortcut(shortcut)


class CommentBox(BaseWidgetGroup):
    """
    A text box widget.

    Needs to be added to the canvas in GUI.

    Parameters
    ----------
    parent : QtWidgets.QMainWindow
        Parent of the widget.
    wconf : dict
        Widget configuration.
    wpolicy : QtWidgets.QSizePolicy
        Widget size policy.
    """

    def __init__(self, parent, wconf:dict, wpolicy:QtWidgets.QSizePolicy, *args, **kwargs):
        super(CommentBox, self).__init__(wconf, wpolicy, *args, **kwargs)
        # configure internal widget
        widget = QtWidgets.QPlainTextEdit(None)
        widget.setObjectName(f"tb_{self._id}")
        widget.setSizePolicy(QtWidgets.QSizePolicy(policy.Expanding, policy.Preferred))

        self.addTexts(widget, wconf)
        widget.installEventFilter(parent) # Set enter as save

        self.layout().addWidget(widget)
        # add to parents textbox list
        parent.tb[self._id] = widget

    def addTexts(self, widget: QtWidgets.QPlainTextEdit, element:dict) -> None:
        """
        Add texts to the input widget (shortcut).

        Parameters
        ----------
        widget : QtWidgets.QPlainTextEdit
            Widget instance to use.
        element : dict
            Widget configuration dict.
        """
        shortcut = None
        try:
            shortcut = element['shortcut']
        except KeyError as e:
            print(f"KeyError: {e}")
        finally:
            if shortcut is None:
                widget.setPlaceholderText("Press [Enter] to save, and [Esc] to discard.")
            else:
                widget.setPlaceholderText(f"Press [{shortcut}] to insert comments. Press [Enter] to save, and [Esc] to discard.")
                # add shortcut
                ws = QtWidgets.QShortcut(shortcut, widget)
                ws.activated.connect(widget.setFocus)
