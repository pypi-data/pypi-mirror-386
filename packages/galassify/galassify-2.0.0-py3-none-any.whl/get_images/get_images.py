"""
Image downloader (:mod:`get_images.get_images`)
==============================================================

A tool to download galaxy images from SDSS, DESI...

Written by Simon, adapted by MrManlu & Andoni
"""
import os, sys
import argparse
from pathlib import Path
from io import BytesIO

import pandas as pd

import requests
from PIL import Image

VERSION = "0.2"

SDSS_supported_DR = range(12, 20)
DESI_supported_DR = range(5, 10)

def download_desi(fname:str, raval:float, decval:float, size:int, datarelease:int=8, parameters:dict=None) -> (int, str):
    """Cutout.
    Download DESI/DECaLS images using ra and dec of a specific Data Release (Default is DR8)
    We have considered 0.1 ''/pix, it can be modified changing the scale value or the width/height in params dictionary.
    The parameter "fname" correspond with the SIG name.
    """
    
    BASE_URL = "https://www.legacysurvey.org/viewer/jpeg-cutout"
    layers = {
        9: "ls-dr9",
        8: "ls-dr8",
        7: "decals-dr7",
        6: "mzls+bass-dr6",
        5: "decals-dr5",
    }
    params = {
        'ra': raval,
        'dec': decval,
        'width': size,
        'height': size,
        'pixscale': 0.35,
        #'zoom': 14,
        'layer': layers[datarelease]
    }

    if parameters:
        params.update(parameters)

    r = requests.get(BASE_URL, params=params, timeout=10)
    if r.status_code == 200:
        Image.open(BytesIO(r.content)).save(fname)
    return r.status_code, r.reason

# Define functions
def download_sdss(fname:str, raval:float, decval:float, size:int, datarelease:int=12, parameters:dict=None) -> (int, str):
    """Cutout.
    Download SDSS images using ra and dec of a specific Data Release (Default is DR12)
    We have considered 0.35 ''/pix, it can be modified changing the scale value or the width/height in url_1 variable.
    The parameter "fname" correspond with the SIG name.
    """
    BASE_URL = f"http://skyserver.sdss.org/dr{datarelease}/SkyserverWS/ImgCutout/getjpeg"
    params = {
        "TaskName": "Skyserver.Chart.Image",
        "ra": raval,
        "dec": decval,
        "width": size,
        "height": size,
        "scale": 0.35,
        "opt": "G",
        "query": None,
        "Grid": "on"
    }

    if parameters:
        params.update(parameters)

    r = requests.get(BASE_URL, params=params, timeout=10)
    if r.status_code == 200:
        Image.open(BytesIO(r.content)).save(fname)
    return r.status_code, r.reason

def is_valid_file(arg):
    if not os.path.exists(arg):
        raise argparse.ArgumentTypeError(f"The file {arg} does not exist. Please, specify an existing one.")
    return arg

def get_args():
    """
    Parse the arguments given by the user.

    If any error is detected, or -h / --help is asked, a help guide is displayed and the program exits.
    """
    parser = argparse.ArgumentParser(prog='get_images', description="GALAssify image downloader.")

    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION,
                        help="Prints software version and exit.\n")
    parser.add_argument('-p', '--path', type=is_valid_file, default='img',
                        help="Path to save image files.\n")
    parser.add_argument('-i', '--inputfile', type=is_valid_file, required=True,
                        help="Galaxy database file in *.csv format.\n")
    parser.add_argument('-o', '--outputfile', type=str, default=None,
                        help="""Output galaxy database file in *.csv format containing
                        the path to the downloaded images. If not specified, the
                        paths will be written in the input CSV file.""")
    parser.add_argument('-s', '--size', type=int, default=512,
                        help="Size of the edges (in pixels) of the downloaded images.\n")
    parser.add_argument('-r', '--survey', type=str, default="SDSS",
                        help="Select the desired survey. Currently available: \"SDSS\", \"DESI\".")
    parser.add_argument('-d', '-dr', '--dr', '--datarelease', type=int, default=12,
                        help="Data release number.")

    return parser.parse_args()

def check_DR(datarelease, survey):
    if survey == "sdss":
        drs = SDSS_supported_DR
    elif survey == "desi":
        drs = DESI_supported_DR
    
    max_dr, min_dr = max(drs), min(drs)

    if datarelease > max_dr or datarelease < min_dr:
        print(f"WARNING: Supported {survey.upper()} datareleases: {list(drs)}")
        print(f"Defaulting to DR{max_dr}")
        datarelease = max_dr
    
    return datarelease

def main():
    """
    Main program
    """
    # Params
    args = get_args()
    path = Path(args.path)
    inputfile = Path(args.inputfile)
    size = args.size
    outputfile = args.outputfile
    survey = args.survey.lower()
    # Read catalogue
    galaxies = pd.read_csv(inputfile)

    # List of processed queries with error
    error_queries_n = 0

    download_fcn = None
    # Select the survey
    if survey == "sdss":
        download_fcn = download_sdss
        
    elif survey == "desi":
        download_fcn = download_desi

    datarelease = check_DR(args.dr, survey)

    # Download images
    n = len(galaxies)
    print(f"Downloading images from {survey.upper()} for {n} galaxies")
    try:
        for index, row in galaxies.iterrows():
            id = row['galaxy']
            group = '-'
            if 'group' in galaxies.columns:
                group = row['group']

            fname = f"{path}/img_{group}_{id}.jpeg"
            status, reason = download_fcn(fname, row['ra'], row['dec'], size, datarelease=datarelease)
            if status != 200:
                error_queries_n += 1
                error_msg = f"Error downloading object #{id} from group {group}"
                error_msg += f"(R.A. {row['ra']}, DEC {row['dec']}). "
                error_msg += f"Status code: {status}. Reason: {reason}."
                print(error_msg)
                continue
            galaxies.loc[index, 'filename'] = f"img_{group}_{id}.jpeg"

            if index % 10 == 0:
                print(f"Remaining {n-index}")
    except KeyError as e:
        print(f"KeyError: {e}")

    file = Path(outputfile) if outputfile else inputfile
    galaxies.to_csv(file, index=None)
    print("Done!")

    if error_queries_n > 0:
        print(f"Error processing {error_queries_n} file(s). See log above.")

if __name__ == '__main__':
    sys.exit(main())
