import sys 
import subprocess 
import shutil 
import os 
import shlex
from contextlib import contextmanager
from pathlib import Path 

import yaml 
from dotenv import dotenv_values

from create_serverless_code import create_serverless_code

environ = dotenv_values()

PATH_SERVERLESS_CODE_DEPLOY = Path(environ['PATH_SERVERLESS_CODE_DEPLOY'])
GCLOUD_DEPLOY_ENV_FILE = '.env.yml'


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
    

if __name__ == '__main__': 

    create_serverless_code()

    cmd = rf"""gcloud functions deploy beanstalk_analytics_handler \
    --region=us-east1 \
    --runtime=python310 \
    --source={PATH_SERVERLESS_CODE_DEPLOY} \
    --entry-point=beanstalk_analytics_handler \
    --env-vars-file={GCLOUD_DEPLOY_ENV_FILE} \
    --ignore-file=../.gcloudignore \
    --trigger-http \
    --allow-unauthenticated
    """
    
    with create_env_file(GCLOUD_DEPLOY_ENV_FILE): 
        subprocess.run(
            [c.strip() for c in shlex.split(cmd)], stderr=sys.stderr, stdout=sys.stdout
        )
