import os 
import re 
import shutil
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_notebook
from dotenv import load_dotenv

from safe_rmtree import safe_rmtree

if __name__ == "__main__": 

    assert load_dotenv()

    DIR_PATH_SERVERLESS_CODE = Path(os.environ['DIR_PATH_SERVERLESS_CODE'])
    DIR_PATH_SERVERLESS_CODE_ORIGIN = Path(os.environ['DIR_PATH_SERVERLESS_CODE_ORIGIN'])

    # Empty the serverless code directory (and create anew) if it exists 
    safe_rmtree(DIR_PATH_SERVERLESS_CODE)
    os.mkdir(DIR_PATH_SERVERLESS_CODE)

    # Copy directories 
    for dir_name in [
        "notebooks/prod", 
        "utils_notebook", 
        "utils_serverless",
    ]: 
        shutil.copytree(
            str(DIR_PATH_SERVERLESS_CODE_ORIGIN / dir_name), 
            str(DIR_PATH_SERVERLESS_CODE / dir_name), 
        )

    # Copy files 
    for file_name in [
        "main.py", 
        "tbiq-beanstalk-analytics-bca7893d8291.json"
    ]: 
        shutil.copyfile(
            str(DIR_PATH_SERVERLESS_CODE_ORIGIN / file_name), 
            str(DIR_PATH_SERVERLESS_CODE / file_name), 
        )

    # Process notebooks, consolidating all source code into single cell
    path_notebooks = DIR_PATH_SERVERLESS_CODE / "notebooks/prod"
    for fpath in filter(lambda p: p.suffix == '.ipynb', path_notebooks.iterdir()): 
        nb = nbformat.read(fpath, as_version=4)
        src = '\n'.join(
            [c['source'] for c in nb['cells'] if c['cell_type'] == 'code']
        )
        new_nb = new_notebook(cells=[new_code_cell(cell_type="code", source=src)])
        nbformat.write(new_nb, str(fpath))
        print(f"Processed notebook {fpath}")

    # cleanup any unnecessary files / directories copied over 
    dir_patterns = [r"__pycache__", r'.*\.egg-info'] 
    for (dirpath, dirnames, filenames) in os.walk(str(DIR_PATH_SERVERLESS_CODE), topdown=False): 
        for p in dir_patterns: 
            if re.fullmatch(p, Path(dirpath).name): 
                print(f"Removing {dirpath}")
                safe_rmtree(dirpath)
