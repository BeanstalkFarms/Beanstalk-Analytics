import sys 
import subprocess 
import shutil 
import os 
import shlex
from contextlib import contextmanager
from pathlib import Path 

import yaml 
import nbformat
from nbformat.v4 import new_code_cell, new_notebook
from dotenv import dotenv_values

environ = dotenv_values()

SERVERLESS_DEPLOY_PATH = Path(environ['SERVERLESS_DEPLOY_PATH'])
GCLOUD_DEPLOY_ENV_FILE = '.env.yml'


@contextmanager
def copy_requirements_file(): 
    """Copy requirements file from root directory to serverless directory 

    Remove file once context closes 
    """
    fpath_new = str(SERVERLESS_DEPLOY_PATH / Path("requirements.txt"))
    shutil.copyfile("requirements.txt", fpath_new)
    yield 
    os.remove(fpath_new)


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
    for fpath in path_notebooks.iterdir(): 
        if fpath.suffix == '.ipynb': 
            nb = nbformat.read(fpath, as_version=4)
            src = '\n'.join(
                [c['source'] for c in nb['cells'] if c['cell_type'] == 'code']
            )
            new_fpath = path_notebooks_processed / fpath.name 
            new_nb = new_notebook(cells=[new_code_cell(cell_type="code", source=src)])
            print(f"Converting {str(fpath):<50} -> {new_fpath}")
            nbformat.write(new_nb, new_fpath)


@contextmanager
def create_env_file(yml_path): 
    """GCloud only accepts env files in yaml form
    
    We filter the environment variables so only a subset 
    of them are actually deployed with the function. 

    Remove file once context closes 
    """
    keys = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "NEXT_PUBLIC_STORAGE_BUCKET_NAME",
        "SUBGRAPH_URL",
    ]
    with Path(yml_path).open("w") as f:
        yaml.safe_dump({k: v for k, v in environ.items() if k in keys}, stream=f)
    yield 
    os.remove(yml_path)
    

"""
------------- PRE-DEPLOY PIPELINE FOR SERVERLESS FUNCTION --------------------
"""

cmd = rf"""gcloud functions deploy beanstalk_analytics_handler \
--region=us-east1 \
--runtime=python310 \
--source={SERVERLESS_DEPLOY_PATH} \
--entry-point=beanstalk_analytics_handler \
--env-vars-file={GCLOUD_DEPLOY_ENV_FILE} \
--ignore-file=../.gcloudignore \
--trigger-http \
--allow-unauthenticated
"""

process_notebooks() 
with (
    copy_requirements_file(), 
    create_env_file(GCLOUD_DEPLOY_ENV_FILE),
): 
    subprocess.run(
        [c.strip() for c in shlex.split(cmd)], stderr=sys.stderr, stdout=sys.stdout
    )
