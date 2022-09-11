"""Creates a directory containing code to deploy as a google cloud function. """
import os 
import re 
import shutil
import logging 
import argparse 
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_notebook

from safe_rmtree import safe_rmtree
from utils_serverless.utils import PATH_NOTEBOOKS  # bro you thought I was just gonna rawdog shutil.rmtree ?????


logger = logging.getLogger(__name__)


def create_serverless_code(): 

    DIR_ROOT = Path(os.environ['PATH_PROJECT'])
    DIR_SRC = Path(os.environ['PATH_SERVERLESS_CODE_DEV'])
    DIR_DST = Path(os.environ['PATH_SERVERLESS_CODE_DEPLOY'])
    PATH_NOTEBOOKS = Path(os.environ['PATH_NOTEBOOKS'])
    
    # Empty the serverless code directory (and create anew) if it exists 
    if DIR_DST.exists(): 
        safe_rmtree(DIR_DST)
    os.makedirs(DIR_DST)

    shutil.copytree()

    # Copy directories 
    for src, dst, dir_name in [
        (DIR_SRC, DIR_DST, PATH_NOTEBOOKS), 
        (DIR_SRC, DIR_DST, "utils_notebook"), 
        (DIR_SRC, DIR_DST, "utils_serverless"), 
    ]: 
        shutil.copytree(str(src / dir_name), str(dst / dir_name))

    # Copy files 
    for src, dst, file_name, in [
        (DIR_SRC, DIR_DST, "main.py"), 
        (DIR_SRC, DIR_DST, "tbiq-beanstalk-analytics-bca7893d8291.json"), 
        (DIR_ROOT, DIR_DST, "requirements.txt"),
    ]: 
        shutil.copyfile(str(src / file_name), str(dst / file_name))

    # Process notebooks, consolidating all source code into single cell
    path_notebooks = DIR_DST / PATH_NOTEBOOKS
    for fpath in filter(lambda p: p.suffix == '.ipynb', path_notebooks.iterdir()): 
        nb = nbformat.read(fpath, as_version=4)
        src = '\n'.join(
            [c['source'] for c in nb['cells'] if c['cell_type'] == 'code']
        )
        new_nb = new_notebook(cells=[new_code_cell(cell_type="code", source=src)])
        nbformat.write(new_nb, str(fpath))
        logging.info(f"Processed notebook {fpath}")


if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument('--quiet', action="store_true")
    args = parser.parse_args()
    if args.quiet: 
        logger.setLevel(level=logging.CRITICAL)
    else: 
        logger.setLevel(level=logging.INFO)
    create_serverless_code()
    
