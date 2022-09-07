import shutil 
from pathlib import Path 

import nbformat
from nbformat.v4 import new_code_cell, new_notebook
from dotenv import dotenv_values


environ = dotenv_values()


def process_notebooks(): 
    """Processes jupyter notebooks 

    - Combines all code cells into single code cell 
        - This removes intermediate data outputs within the notebook 
        when executing the serverless function, saving significant memory.
    - This code should be run automatically before deploying serverless function
    """
    path_notebooks = Path(environ['NOTEBOOK_DIR_PATH'])
    path_notebooks_processed = Path(environ['NOTEBOOK_PROCESSED_DIR_PATH'])

    # Clear processed notebooks directory 
    if path_notebooks_processed.exists(): 
        shutil.rmtree(path_notebooks_processed)
    # Copy tree rooted at notebooks directory. We want to retain 
    # all other non-notebook files as dependencies. 
    shutil.copytree(path_notebooks, path_notebooks_processed)

    # Overwrite copied notebooks with processed notebooks. 
    count = 0 
    for fpath in path_notebooks.iterdir(): 
        if fpath.suffix == '.ipynb' and (count := count + 1): 
            nb = nbformat.read(fpath, as_version=4)
            # Consolidate all source code (in-order) contained within the notebook 
            # into a single cell. 
            src = '\n'.join(
                [c['source'] for c in nb['cells'] if c['cell_type'] == 'code']
            )
            new_fpath = path_notebooks_processed / fpath.name 
            new_nb = new_notebook(cells=[new_code_cell(cell_type="code", source=src)])
            divider = '-' * (10 + max(len(str(fpath)), len(str(new_fpath))))
            print(
                (divider + '\n' if count == 1 else '') +
                f"{'Original':<10}{fpath}\n{'New':<10}{new_fpath}\n{divider}"
            )
            nbformat.write(new_nb, new_fpath)


if __name__ == '__main__': 
    process_notebooks()