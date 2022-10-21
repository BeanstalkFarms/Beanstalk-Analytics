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


logger = logging.getLogger(__name__)


def create_serverless_code(): 

    DIR_ROOT = Path(os.environ['PATH_PROJECT']).absolute()
    DIR_SRC = Path(os.environ['PATH_SERVERLESS_CODE_DEV']).absolute()
    DIR_DST = Path(os.environ['PATH_SERVERLESS_CODE_DEPLOY']).absolute()
    RPATH_NOTEBOOKS = Path(os.environ['RPATH_NOTEBOOKS'])
    RPATH_NOTEBOOKS_TEST = Path(os.environ['RPATH_NOTEBOOKS_TEST'])

    # More sanity checks to protect the filesystem lol 
    assert str(DIR_ROOT).endswith("beanstalk-data-playground")
    assert str(DIR_SRC).startswith(str(DIR_ROOT))
    assert str(DIR_DST).startswith(str(DIR_ROOT))
    
    # Remove existing build directory
    if DIR_DST.exists(): 
        safe_rmtree(DIR_DST)
    
    # Re-create build directory 
    shutil.copytree(str(DIR_SRC), str(DIR_DST))

    # Process notebooks, consolidating all source code into single cell
    for rpath in [RPATH_NOTEBOOKS, RPATH_NOTEBOOKS_TEST]: 
        path_notebooks = DIR_DST / rpath
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
        logging.basicConfig(level=logging.CRITICAL)
    else: 
        logging.basicConfig(level=logging.INFO)
    create_serverless_code()
    
