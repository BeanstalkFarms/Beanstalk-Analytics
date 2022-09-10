import shutil 
import os 
from pathlib import Path 

from dotenv import load_dotenv


assert load_dotenv()

PATH_PROJECT = Path(os.environ['PATH_PROJECT'])


def safe_rmtree(path, **kwargs): 
    # don't fuck around with this function lads 
    path = Path(os.path.abspath(path))
    if not str(path).startswith(str(PATH_PROJECT.absolute())) or path == PATH_PROJECT: 
        raise ValueError(
            f"\nsafe_rmtree detected that the directory you wanted to delete\n{path}\n"
            f"exists outside of or is the specified project path\n{PATH_PROJECT}"
        )
    shutil.rmtree(path, **kwargs)
