import shutil 
import os 
from pathlib import Path 

from dotenv import load_dotenv


assert load_dotenv()

PROJECT_PATH = Path(os.environ['PROJECT_PATH'])


def safe_rmtree(path, **kwargs): 
    # don't fuck around with this function lads 
    path = Path(os.path.abspath(path))
    if not str(path).startswith(str(PROJECT_PATH.absolute)) or path == PROJECT_PATH: 
        raise ValueError(
            f"\nsafe_rmtree detected that the directory you wanted to delete\n{path}\n"
            f"exists outside of or is the specified project path\n{PROJECT_PATH}"
        )
    shutil.rmtree(path, **kwargs)
