import sys 
import subprocess 
import shutil 
import os 
import shlex
from contextlib import contextmanager
from pathlib import Path 

import yaml 
from dotenv import dotenv_values

from process_notebooks import process_notebooks

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
