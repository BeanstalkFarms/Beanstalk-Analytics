import os 
import shutil
from pathlib import Path

from dotenv import load_dotenv

from process_notebooks import process_notebooks

if __name__ == "main": 
    assert load_dotenv()
    DIR_PATH_SERVERLESS_CODE = Path(os.environ['DIR_PATH_SERVERLESS_CODE'])
    DIR_PATH_SERVERLESS_CODE_ORIGIN = Path(os.environ['DIR_PATH_SERVERLESS_CODE_ORIGIN'])

    # Empty the serverless code directory (and create anew) if it exists 
    shutil.rmtree(DIR_PATH_SERVERLESS_CODE)
    os.mkdir(DIR_PATH_SERVERLESS_CODE)

    # Copy directories 
    for dir_name in [
        "notebooks/prod", 
        "utils_notebook", 
        "utils_serverless",
    ]: 
        shutil.copytree(
            str(DIR_PATH_SERVERLESS_CODE_ORIGIN.join(dir_name)), 
            str(DIR_PATH_SERVERLESS_CODE.join(dir_name)), 
        )

    # Copy files 
    for file_name in [
        "main.py", 
        "tbiq-beanstalk-analytics-bca7893d8291.json"
    ]: 
        shutil.copyfile(
            str(DIR_PATH_SERVERLESS_CODE_ORIGIN.join(file_name)), 
            str(DIR_PATH_SERVERLESS_CODE.join(file_name)), 
        )

    # Process the notebooks written to the target directory 
    process_notebooks()
    # Remove the raw notebooks written to the target directory 
    # as the cloud function only requires the processed versions. 
    # shutil.rmtree(str(DIR_PATH_SERVERLESS_CODE.join("notebooks-prod")))