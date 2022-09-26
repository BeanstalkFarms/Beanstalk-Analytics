import logging
import json 
from pathlib import Path 
import argparse 
from collections import defaultdict

from utils_serverless.utils import NotebookRunner

# disable logs 
logging.basicConfig(level=logging.CRITICAL)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(
        description='Run one or more notebooks.'
    )
    parser.add_argument(
        '--names', 
        help='The names of the notebooks to execute',
        nargs="+"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Flag that indicates that all notebooks should be run"
    )
    parser.add_argument(
        '--output-dir', 
        help='Output directory where notebook outputs are written'
    )
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    if not output_path.exists() and output_path.is_dir(): 
        raise ValueError("Output path did not exist or was not dir")

    nb_runner = NotebookRunner()
    nb_names = nb_runner.names if args.all else args.names 
    for nb_name in nb_names: 
        print(f"Executing {nb_name}")
        nb_output = nb_runner.execute(nb_name)
        nb_path = output_path / Path(f"{nb_name}.json")
        with nb_path.open("w") as f: 
            f.write(json.dumps(nb_output))
