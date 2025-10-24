# Developer Guide
This developer guide aims to walk a new developer on how to set up their
environment to be able to contribute to this project.

## Setting up development environment
To set up your system for development of the operator, follow the steps below:
1. Clone this repository:

    ```bash
    git clone git@gitlab.com:astrogal/GALAssify.git
    ```
2. Go to the local repository folder:

    ```bash
    cd galassify
    ```
3. Create a virtual environment Using a virtual environment is recommended to
execute this tool:

    ```bash
    python3 -m venv .env
    source .env/bin/activate
    ```

4. Install the dependencies (including recommended packages):

    ```bash
    pip install .[ds9]
    ```

5. Test that the programs can run successfully:
   1. GALAssify
      ```bash
      python3 -m src.galassify.galassify --example basic
      python3 -m src.galassify.galassify
      ```
   2. get_images
      ```bash
      python3 -m src.galassify.galassify --example basic
      python3 -m src.get_images.get_images -i files/galaxies.csv -p img/
      ```

## Project structure
This is a top level overview of the project folders:
```bash
$ pwd
galassify
$ tree -dL 5 .
.
├── doc
│   ├── instructions
│   └── paper
├── src
│   ├── galassify
│   │   ├── files
│   │   ├── img
│   │   │   ├── fits
│   │   │   └── nog
│   │   └── res
│   └── get_images
└── test

12 directories
```
A simple explanation of each folder can be found below:
- `doc`: Includes all the project-related available documentation and
  information.
  - `doc/instructions`: Sources to generate a simple user manual poster.
  - `doc/paper`: Sources to generate an article featuring this project.
- `src`: Parent folder of both standalone modules: GALAssify and get_images_lss
  - `src/galassify`: Sources of the GALAssify module, containing all the `*.py`
    files and resources needed to run this module.
    - `src/galassify/files`, `src/galassify/img`: Example files.
    - `src/galassify/res`: Resources (e.g. such as the system icon).
  - `src/get_images`: Sources of the get_images module, containing all
    the `*.py` files and resources needed to run this module.
- `test`: Folder containing all the tests used both by developers and by GitLab
  CI.

## Debugging

In order to check that the basic functionality of the GUI is not broken before
commit changes, it is strongly recommended to run all the tests locally. The
complete tests suite can be executed by doing:
```bash
python3 -m unittest
```
It everything is OK, a message like the following one should appear:
```python
....
----------------------------------------------------------------------
Ran 10 tests in 1.398s

OK
```
Otherwise, please double check the new integrated code and run the tests again
before commit.

Thank you!