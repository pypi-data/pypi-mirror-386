"""
Utilities (:mod:`galassify.utils`)
==================================

This module contains various utility functions and parameters.
"""
import os, sys
import re
import glob
import argparse
from pathlib import Path
import warnings
from typing import Union
import json

import pandas as pd
from PyConsoleMenu import SelectorMenu

try:
    # Using pkg_resources (deprecated in python 3.12)
    import pkg_resources
    module_path = pkg_resources.resource_filename(__name__, '')
except ImportError:
    # Using importlib_resources python 3.12+
    from importlib.resources import files as irfiles
    module_path = irfiles(__name__)

### OPTION PARSER UTILS

args = None
VERSION = ''
importData = pd.DataFrame()
groups = pd.DataFrame()


def getOptions(version: str) -> argparse.Namespace:
    """
    Parse the arguments given by the user.

    If any error is detected, or -h / --help is asked, a help guide is displayed and the program exits.

    Returns
    -------
    Namespace
        Returns parsed command-line arguments.
    """
    global args
    global VERSION

    parser = argparse.ArgumentParser(prog='GALAssify', description="GALAssify: Tool to manually classify galaxies.")
    parser.add_argument('--version', action='version', version='%(prog)s ' + version,
                        help="Prints software version and exit.\n")

    parser.add_argument('--init', action='store_true',help='Generate a basic config file, and the basic folder structure.')

    parser.add_argument('--gui', action='store_true',help='Force a fully graphical operation.')

    parser.add_argument('--example', type=example_type, default='', help='Run a galassify (basic or fits) example.')

    parser.add_argument('-p', '--path', default='img/',
                        help="Path to image files.\n")

    parser.add_argument('-c', '--config', default='config',
                        help="Config json file to load.\n")

    #parser.add_argument('-f', '--filename', nargs='+',
    #                    required=not('-p' in sys.argv
    #                    or '--path' in sys.argv
    #                    or '--version' in sys.argv), type=dir_file,
    #                    help="Image or list to classify. Not required if path or path + group are given.\n")

    parser.add_argument('-s', '--savefile',
                        #required=not('--version' in sys.argv),
                        default='output.csv',
                        help="CSV file to load and export changes. If does not exists, a new one is created.\n")
    parser.add_argument("-l", "--list", action="store_true",
                        help="List selected files only and exit.\n")

    parser.add_argument('-i', '--inputfile', default='files/galaxies.csv',
                        help="""Galaxy database file in *.csv format.
                        Minimum required columns: ['galaxy'].
                        Recommended columns: ['group', 'galaxy', 'ra', 'dec', 'filename' and/or 'fits']""")

    parser.add_argument('projectpath', metavar='PROJECTPATH', nargs='?',
                        #required=(('--init' in sys.argv) or ('--example' in sys.argv)),
                        default=os.getcwd(),
                        help="Path where init blank projects or deploy one of the embedded examples")

    parser.add_argument('group', metavar='GROUP', nargs='*',
                        help="Group number. Selects images with name format: img_<group>_*.png\n")

    args = parser.parse_args()

    # Small hack to detect if the first positional argument is
    # project path or a group.
    if not os.path.isdir(args.projectpath):
        args.group.insert(0, args.projectpath)
        args.projectpath = os.getcwd()

    VERSION = version
    return args

def exist_basic_files(projectpath=None):
    """
    Checks if the basic needed files and folders exists.

    Returns
    -------
    bool
        Returns True if the basic files exists. Else, False is returned.
    """
    if projectpath is None:
        if hasattr(args, 'projectpath') and \
            args.projectpath is not None:
            projectpath = args.projectpath
        else:
            projectpath = os.getcwd()

    files = [args.inputfile, args.path, args.config]
    test_files = True
    for file in files:
        fl = os.path.join(args.projectpath, file) if not os.path.isabs(file) else file
        if not Path(fl).exists():
            test_files = False
    return test_files

def init_flag():
    """
    Generates a basic initial files and folders in the user selected directory.
    """
    global args
    print("INFO:\tGenerating the necessary files...")
    try:
        os.system(f"cp '{getPackageResource('config')}' config")
        os.system("mkdir -p files img/fits")
        os.system('echo "group,galaxy,ra,dec,filename,fits" >> files/galaxies.csv')
        print("INFO:\tThe necessary files were created.")
        print("INFO:\tNow, complete de input files and open GALAssify with: galassify -i files/galaxies.csv -s files/output.csv -p img/ ")
    except:
        pass

def getVersion():
    """
    Gets the current GALAssify version.

    Returns
    -------
    str
        Current GALAssify version.
    """
    global VERSION
    return VERSION

def getPackageResource(relative_path) -> str:
    """
    Get the absolute path to a resource file.
    """
    global module_path

    return os.path.join(module_path, relative_path)

def getFiles() -> tuple:
    """
    Reads the input arguments and manages the groups given by the user and
    the input files.

    Returns
    -------
    pandas.DataFrame
        Dataframe containing all the files selected by the user.

    list
        List containing all the groups selected by the user.
    """
    global args
    global groups
    # files = []
    selectedGroups = []
    selectedFiles = pd.DataFrame(columns = groups.columns)

    imgpath = args.path

    if imgpath:
        fname = args.inputfile
        file = Path(fname)
        if file.is_file():
            groups = readInputFile(fname)
        else:
            groups = createInputFile(imgpath, fname)

        availableGroups = None
        if 'group' in groups.columns:
            availableGroups = groups.group.unique()
            print(f"INFO:\tAvailable groups: {str(availableGroups)}")

            inputGroups = args.group
            if len(inputGroups) > 0:
                for group in inputGroups:
                    if group in availableGroups:
                        selectedFiles = pd_concat(selectedFiles, groups[groups.group == group])
                        selectedGroups.append(group)
                    else:
                        print(f'WARNING:\tGroup {group} not available.')
            else:
                print('INFO:\tNo group selected. Using all available by default.')
                selectedFiles = groups.copy()
                selectedGroups = availableGroups
        else:
            print('INFO:\tNo group in input file. Using all galaxies by default.')
            selectedFiles = groups.copy()
            selectedGroups = availableGroups

        #else:
        #    formats = ['*.png']

        #for format in formats:
        #    for entry in Path(args.path).glob(format):
        #        files.append(entry)

    #elif args.filename:
    #    for entry in args.filename:
    #        files.append(Path(entry))

    #else:
    #    files = []
    return selectedFiles, selectedGroups

INPUTCOLUMNS = ['group','galaxy','ra','dec','filename']

def readInputFile(fname:str) -> pd.DataFrame:
    """
    Reads and parses the input galaxy database file.

    Parameters
    ----------
    fname : str
        Path to galaxy database file in \*.csv format.

    Returns
    -------
    pd.DataFrame
        Pandas dataframe containing the read galaxy database file.
    """
    print(f"INFO:\tReading from '{fname}' file... ", end='', flush=True)
    df = pd.read_csv(fname,
                     converters={
                            'group': str,
                            'galaxy': str,
                            'ra': float,
                            'dec': float,
                         }
                    )
    sortby=[]
    if 'galaxy' in df.columns:
        sortby.insert(0, 'galaxy')
    if 'group' in df.columns:
        sortby.insert(0, 'group')
    df = df.sort_values(by=sortby)

    if 'filename' in df.columns:
        not_found = sum(df['filename']=='')
    else:
        not_found = 0
    #     imgpath = Path(args.path)
    #     df['filename'] = ''
    #     for i, row in df.iterrows():
    #         if 'group' in df.columns:
    #             imgfile = f'img_{row.group}_{row.galaxy}.*'
    #         else:
    #             imgfile = f'img_*_{row.galaxy}.*'
    #         image = glob.glob(f"{imgpath.absolute()}/{imgfile}")
    #         if len(image)>0:
    #             df.loc[i, 'filename'] = image[0]

    if not_found >0:
        print(f'\nWARNING: {not_found} images where not found. Check if the provided path is correct. Or download the images using the provided tool.')
    else:
        print('Done!')
    return df

def createInputFile(imgpath:str, fname:str) -> pd.DataFrame:
    """
    Creates a galaxy database file in \*.csv format for a given path containing
    images with the format "img_<group>_<galaxy>.<extension>".

    Parameters
    ----------
    imgpath : str
        Path to image folder.
    fname : str
        filename of the newly generated galaxy database.

    Returns
    -------
    pd.DataFrame
        Dataframe containing the newly generated database.
    """
    print(f'INFO:\tCreating {fname} file... ', end='', flush=True)
    df = pd.DataFrame(columns=INPUTCOLUMNS)
    if imgpath:
        for file in Path(imgpath).glob('img_*_*.*'):
            entry = {
                        'group': int(file.stem.split('_')[1]),
                        'galaxy': int(file.stem.split('_')[2]),
                        'ra':float(0),
                        'dec':float(0),
                        'filename': str(file.name),
                    }
            df = pd_concat(df, entry)
            #groups = groups.append(entry, ignore_index=True)
    # if groups not defined
    if sum(df["group"] == '-') == len(df):
        df.drop("group", axis=1, inplace=True)
        INPUTCOLUMNS.remove("group")
    # sort
    sortby=[]
    if 'galaxy' in df.columns:
        sortby.insert(0, 'galaxy')
    if 'group' in df.columns:
        sortby.insert(0, 'group')
    df = df.sort_values(by=sortby)

    df.to_csv(fname, columns=INPUTCOLUMNS, index=False)
    print('Done!')
    return df

### EXAMPLES UTILS

examples = {
    'basic':{
        "file":"files/galaxies.csv",
        "help":"BASIC\t(--example basic ):\tExample of basic image classification"
        },
    'click':{
        "file":"files/galaxies.csv",
        "help":"CLICK\t(--example click ):\tDisplayed images allows zooming and annotating points with double-click",
        "config":{"display":{"bitmap":"clickable"}},
        },
    'fitsimg':{
        "file":"files/galaxies_fits.csv",
        "help":"FITS\t(--example fits  ):\tExample of displaying both FITS and bitmap image for classification",
        },
    'onlyfits':{
        "file":"files/galaxies_fitsonly.csv",
        "help":"ONLYFITS\t(--example onlyfits):\tClassification displaying only FITS image",
        "config":{"display":{"fits":{"cmap":"plasma"}}},
        }
}

def example_type(type_text):
    """
    Simple parser of the example selected by the user.

    Parameters
    ----------
    type_text : str
        Type of the selected example. Can be 'basic', 'click', 'fitsimg', 'onlyfits' or be empty.

    Raises
    ------
    argparse.ArgumentTypeError
        Raised when no valid example type was given.
    """
    if len(type_text) != 0 and type_text not in list(examples.keys()):
        raise argparse.ArgumentTypeError(f"readable_example_type: \"{type_text}\" is not a valid example type.")
    return type_text

def run_menu():
    selec = "main"
    while selec == "main":
        selec = load_menu()
        if selec == "init":
            init_flag()
        elif selec == "exit":
            break
        elif selec == "main":
            continue
        else:
            example_flag(selec)


def load_menu() -> int:
    """
    Command-line menu to initialize the tool.

    Gives the user an easy way to initialize the tool with the following options:
    - INIT
    - EXAMPLE: 'basic', 'click', 'fitsimg', 'onlyfits'

    Returns
    -------
    str
        Selected option
    """
    select_option = "main"

    options = ["INIT (--init):\tGenerate a basic config file, and the basic folder structure.",
               "EXAMPLE (--example):\tGenerate project files based on the included examples.",
               "EXIT"]
    menu_help_str = "GALAssify: A tool to manually classify galaxies."
    menu_help_str += f"\n\nProject files were not found in the current working directory: {args.projectpath}"
    menu_help_str += f"\nUse keyboard arrows to select one of the following options below and press [Enter]:\n"
    menu = SelectorMenu(options, title=menu_help_str)
    ans = menu.input()
    if ans.index == 0:
        select_option = "init"
    elif ans.index == 1:
        options_examples = [i["help"] for i in examples.values()] + ["BACK"]
        menu_examples = SelectorMenu(options_examples,
                              title="GALAssify Example: Generate project files based on the included examples.\n")
        ans_examples = menu_examples.input()
        if ans_examples.index < (len(options_examples) - 1):
            select_option = list(examples.keys())[ans_examples.index]
        else:
            # Return to main menu
            select_option = "main"

    elif ans.index==2:
        # Exit gratefully
        select_option = "exit"

    return select_option

def example_flag(type_example):
    """
    Copies example initial files and folders in the user selected directory.
    """
    print("INFO:\tGenerating the necessary files...")
    try:
        # Copy common files
        config_path = args.config if os.path.isabs(args.config) \
                    else os.path.join(args.projectpath, args.config)
        img_path = args.path if os.path.isabs(args.path) \
                    else os.path.join(args.projectpath, args.path)
        inputfile_path = args.inputfile if os.path.isabs(args.inputfile) \
                    else os.path.join(args.projectpath, args.inputfile)
        savefile_path = args.savefile if os.path.isabs(args.savefile) \
                    else os.path.join(args.projectpath, args.savefile)
        
        os.system(f"cp -f '{getPackageResource('config')}' {config_path}")

        # If the example requires an specific configuration, update it:
        if "config" in examples[type_example]:
            with open(config_path, 'r') as f:
                config:dict = json.loads(f.read())
                config.update(examples[type_example]["config"])
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        os.system(f"mkdir -p '{os.path.dirname(inputfile_path)}'")

        # Copy and create example-specific files
        if type_example not in examples.keys():
            print("ERROR: Unrecognised example number")
            return

        inputFile = examples[type_example]['file']
        os.system(f"cp -f '{getPackageResource(inputFile)}' '{inputfile_path}'")
        galaxies = pd.read_csv(getPackageResource(inputFile))
        img_base_path = "img"
        routes = {'filename': img_base_path, 'fits': os.path.join(img_base_path, "fits")}
        for route in routes.items():
            os.system(f"mkdir -p '{route[1]}'")
            if route[0] in galaxies.columns:
                for row in galaxies.iterrows():
                    element = row[1][route[0]]
                    element_dir = getPackageResource(os.path.join(img_base_path, element))
                    os.system(f"cp -f '{element_dir}' '{os.path.join(img_path, element)}'")

        print("INFO:\tThe necessary files were created.")
        print(f"INFO:\tNow, open GALAssify with: galassify -i {inputfile_path} -s {savefile_path} -p {img_path}")
        print(f"INFO:\tIf needed, you can download catalogue images by executing: get_images -i {inputfile_path} -p {img_path}")
    except Exception as e:
        print(f"ERROR: Error while creating the necessary files: {e}")

### PANDAS UTILS

COLUMNS = ["filename", "group", "galaxy", "morphology", "large", "tiny", "faceon",
           "edgeon", "star", "calibration", "recentre", "duplicated",
           "member", "hiiregion", "yes", "no", "comment", "processed",
           "fullpath", "ra", "dec"]

IDS = {
    'FILE':[],
    'TB':[],
    'CB':[],
    'RB':[],
    'RBG':[]
}

def getColumns() -> list:
    """
    Return columns

    Returns
    -------
    list
        List of columns
    """
    return COLUMNS

def getExportableColumns():
    """
    Returns the exportable columns of the program.

    Returns
    -------
    list
        List of columns (strings).
    """
    return COLUMNS[:-4]

def getRadioButtonGroups():
    """
    Returns the groups of radio buttons.

    Returns
    -------
    list
        List of groups (strings).
    """
    return IDS['RBG']

def getRadioButtonsNames():
    """
    Returns the name of radio buttons.

    Returns
    -------
    list
        List of names (strings).
    """
    return IDS['RB']

def getCheckBoxesColumns():
    """
    Returns the columns of check boxes.

    Returns
    -------
    list
        List of columns (strings).
    """
    return IDS['CB']

def getTextBoxes():
    """
    Returns the list of columns related with the text boxes.

    Returns
    -------
    list
        List of columns (strings).
    """
    return IDS['TB']


def checkColumnsMismatch(importDataColumns):
    """
    Detects if a given list of columns fits the exportable columns of this program.

    Parameters
    ----------
    importDataColumns : list
        List of columns to be checked

    Returns
    -------
    bool
        True if a mismatch is detected. False if all columns are exportable.
    """
    mismatch = False
    setID = set(importDataColumns)
    setEC = set(getExportableColumns())
    if not ( setID == setEC ):
        print('WARNING:\tColumn mismatch:')
        print("\t(-) → Missing columns in CSV:", list(setEC.difference(setID)))
        print("\t(+) → Additional columns in CSV:", list(setID.difference(setEC)), '\n')
        print("\tMaybe you are using an old savefile. Missing columns will be CREATED.")
        print("\tAdditional columns will be ERASED if you make any change.")
        mismatch = True

    return mismatch


def expand_df(selectedFiles:pd.DataFrame) -> pd.DataFrame:
    """
    Expands an existing Dataframe with the galaxy database given by the program
    arguments.

    Parameters
    ----------
    selectedFiles : pd.Dataframe
        Dataframe to be updated with the galaxy database.

    Returns
    -------
    pd.Dataframe
        Updated input dataframe.
    """
    global args
    global importData
    global groups
    if Path(args.savefile).is_file():
        importData = pd.read_csv(args.savefile,
                                 converters={
                                                'group': str,
                                                'galaxy': str,
                                            }
                                )

        if 'fits_coords' in importData.columns:
            importData['fits_coords'] = importData['fits_coords'].fillna("[]").apply(lambda x: eval(x))

        if 'img_points' in importData.columns:
            importData['img_points'] = importData['img_points'].fillna("[]").apply(lambda x: eval(x))

        if checkColumnsMismatch(importData.columns.values):
            print("\tHint: Additional columns in savefile is common when configuration changed after the savefile was written.")
            print("\tTry:")
            print("\t\t- Restoring the configuration,")
            print("\t\t- Removing the savefile, or")
            print("\t\t- Removing manually the reported additional column in the savefile.")

        importData['processed'] = True
        importData['fullpath'] = ''
        if 'ra' in groups.columns and 'dec' in groups.columns:
            importData['ra'] = 0.0
            importData['dec'] = 0.0

        # I know there is a best way to implement it, maybe in next release
        try:
            # Saved and selected data:
            for i, row in selectedFiles.iterrows():
                item = importData.loc[importData.galaxy == row.galaxy]
                # If selected row is imported in savefile:
                if (item.size > 0):
                    if 'filename' in importData.columns:
                        file = Path(args.path) / Path(row['filename'])
                        importData.loc[importData.galaxy == row.galaxy, 'fullpath'] = file.absolute()
                    if 'ra' in importData.columns and 'dec' in importData.columns:
                        importData.loc[importData.galaxy == row.galaxy, 'ra'] = row.ra
                        importData.loc[importData.galaxy == row.galaxy, 'dec'] = row.dec
                # If selected row is not in savefile:
                else:
                    importData = pd_concat(importData, newEntry(row))

            # Add the full path to imported but unselected data:
            processedUnselectedData = importData[importData.fullpath == '']
            for i, row in processedUnselectedData.iterrows():
                if 'filename' in importData.columns:
                    file = Path(args.path) / Path(row['filename'])
                    importData.loc[importData.galaxy == row.galaxy, 'fullpath'] = file.absolute()
                if 'ra' in importData.columns and 'dec' in importData.columns:
                    ra = groups.loc[groups.galaxy == row.galaxy].ra.item()
                    dec = groups.loc[groups.galaxy == row.galaxy].dec.item()
                    importData.loc[importData.galaxy == row.galaxy, 'ra'] = ra
                    importData.loc[importData.galaxy == row.galaxy, 'dec'] = dec

        except KeyError as e:
            print(f"ERROR:\tError while parsing CSV. [{e}]")

    else:
        importData = pd.DataFrame(columns=COLUMNS)
        for i, row in selectedFiles.iterrows():
            importData = pd_concat(importData, newEntry(row))

    return importData


def newEntry(row:pd.Series) -> dict:
    """
    Generates a new entry to be inserted in the file list used by the GUI.

    Parameters
    ----------
    row : pd.Series
        Pandas Series containing the information to be inserted in the new generated entry.

    Returns
    -------
    dict
        Generated entry.
    """
    entry = {}

    if 'group' in row:
        entry.update({'group': row.group})

    if 'galaxy' in row:
        entry.update({'galaxy': row.galaxy})

    if 'fits' in row:
        entry.update({'fits': row.fits})
        entry.update({'fits_coords': []})

    # ID needed? to separate widget groups?
    for i, rbgCol in enumerate(getRadioButtonGroups()):
        entry.update({rbgCol: getRadioButtonsNames()[-1]}) # default value

    for i, cbCol in enumerate(getCheckBoxesColumns()):
        entry.update({cbCol: False})

    for i, tbCol in enumerate(getTextBoxes()):
        entry.update({tbCol: ''})

    entry.update({'processed': False})

    if 'filename' in row:
        file = Path(args.path) / Path(row['filename'])
        entry.update({'fullpath': file.absolute()})
        entry.update({'filename': file.name}) # default value

        if 'img_points' in COLUMNS:
            entry.update({'img_points': []})
    else:
        entry.update({'fullpath': ''})

    if 'ra' in row and 'dec' in row:
        entry.update({
            'ra': row.ra,
            'dec': row.dec
        })

    default_cols = ['group',
                    'galaxy',
                    'filename',
                    'fits',
                    'ra',
                    'dec'
                    ]

    additional_cols = set(row.keys()) - set(default_cols)

    for ac in additional_cols:
        entry.update({ac: row[ac] })

    return entry


def save_df(df:pd.DataFrame) -> None:
    """
    Save or update the input galaxy database with a given Dataframe in a CSV format.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to be saved.
    """
    global args
    global importData

    # Concatenate items in CSV with our processed items:
    processedItems = pd_concat(importData.loc[df['processed'] == True],
                               df.loc[df['processed'] == True])
    # processedItems = pd.concat([importData.loc[df['processed'] == True],
    #                            df.loc[df['processed'] == True]])

    # Remove old values, keep last ones:

    s_cols = ['galaxy']
    if 'group' in processedItems.columns:
        s_cols.insert(0,'group')
    exportData = processedItems.drop_duplicates(s_cols, keep='last').sort_values(by=s_cols)

    # Export final dataframe:
    exportData.to_csv(args.savefile, columns=getExportableColumns(),
                          index=False)

def pd_concat(df: pd.DataFrame, data: Union[pd.DataFrame, list, dict]) -> pd.DataFrame:
    """ Concats data to the given dataframe

    Parameters
    ----------
    df: pandas.Dataframe
        Pandas dataframe to use

    data: list, dict or pandas.Dataframe
        Data to be concatenated to the input pandas Dataframe.
        - List of the values to be concatenated (order of input values and Dataframe columns must match).
        - Dict of the 'key\:values', where keys match the Dataframe columns (if not, values are put to NaN).
        - pandas.Dataframe where columns (should) match the input Dataframe (if not, new columns are created or values are put to NaN).
    
    Returns
    -------
    pandas.DataFrame
        Dataframe containing both input Dataframes merged.
    """
    # check if data is list
    df_data = pd.DataFrame()
    if type(data) == list:
        if len(data) != len(df.columns):
            raise Exception('ERROR: Input data [list] length is not equal to input dataframe')
        df_data = pd.DataFrame([data], columns=df.columns)
    elif type(data) == dict:
        if len(data) != len(df.columns):
            warnings.warn('Input data [dict] missing input dataframe keys. Missing values inserted as NaN')
            print(list(data.keys()))
            print(list(df.columns))
        df_data = pd.DataFrame([data])
    elif type(data) == pd.DataFrame:
        if not df.empty:
            cmp_df_data = list(df.keys()[~df.keys().isin(data.keys())])
            cmp_data_df = list(data.keys()[~data.keys().isin(df.keys())])
            if len(cmp_df_data) > 0:
                warnings.warn(f'Input data missing input dataframe column. {cmp_df_data}')
            if len(cmp_data_df) > 0:
                warnings.warn(f'Input data column(s) not in input dataframe. {cmp_data_df}')
        df_data = data
    df = pd.concat([df, df_data], ignore_index=True) if len(df) > 0 else df_data
    return df
