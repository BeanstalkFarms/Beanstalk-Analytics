import os 
import argparse 
from pathlib import Path 

import yaml 


def create_env_file(yml_path, env_var_names): 
    """Create environment variable file for use with gcloud commands 

    1. Filter environment variables included in file 
    2. Convert existing environment file into .yml form 
    """
    with Path(yml_path).open("w") as f:
        yaml.safe_dump(
            {k: v for k, v in os.environ.items() if k in env_var_names}, stream=f
        )

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(
        description=(
            'Create environment file in yml form for use with gcloud cli commands. '
            'Takes environment variables from the context that this script is run in.'
        )
    )
    parser.add_argument(
        '--file', help='The name of the file to create. Must end in .yml'
    )
    parser.add_argument(
        '--env-vars', 
        help='The name of the file to create. Must end in .yml',
        nargs="+"
    )
    args = parser.parse_args()
    file = args.file.strip()
    env_vars = args.env_vars
    assert file.endswith(".yml"), "File must end with .yml"
    create_env_file(file, args.env_vars)