import os
import json 
import logging 
import time 
from functools import wraps
from typing import Dict, Tuple, List 
from pathlib import Path 

import nbformat
import functions_framework
from nbclient import NotebookClient
from google.cloud import storage 


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def log_runtime(fn): 
    @wraps(fn)
    def wrapped(*args, **kwargs): 
        start_time = time.time()
        rval = fn(*args, **kwargs)
        end_time = time.time()
        run_secs = end_time - start_time 
        logger.info(f"Runtime of {fn.__name__} was {run_secs} seconds.")
        return rval 
    return wrapped 


class StorageClient: 

    def __init__(self) -> None:
        self.client = storage.Client(project="tbiq-beanstalk-analytics")
        self.bucket = self.client.bucket(os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"])

    @log_runtime
    def upload(self, name: str, data: str) -> None: 
        blob = self.bucket.blob(name)
        blob.upload_from_string(data, retry=None)
        return 


class NotebookRunner: 

    def __init__(self): 
        self.path_notebooks = Path('./notebooks-processed')
        self.ntbk_name_path_map: Dict[str, str] = {
            # Allows for case insensitive matchine of chart names 
            nb_path.stem.lower(): nb_path 
            for nb_path in self.path_notebooks.iterdir() 
            if nb_path.suffix == '.ipynb'
        }
        self.storage_client = StorageClient()

    @property
    def names(self) -> List[str]: 
        return self.ntbk_name_path_map.keys()

    def exists(self, nb_name: str) -> bool: 
        return nb_name in self.ntbk_name_path_map 

    @log_runtime
    def execute(self, nb_name: str) -> Tuple[str, Dict]: 
        """Execute notebook and extract output. 
            
            Args: 
                nb_name: The key for the notebook. 
            Returns: 
                nb_name: The name of the notebook.
                nb_output_json: The data output of the notebook. 
        """
        nb_path: Path = self.ntbk_name_path_map[nb_name]
        nb_node = nbformat.read(str(nb_path), as_version=4)
        nb_client = NotebookClient(
            nb_node, 
            timeout=600, 
            kernel_name='python3', 
            resources={'metadata': {'path': str(self.path_notebooks)}}
        )
        # nb is a dict with structure defined here: https://nbformat.readthedocs.io/en/latest/format_description.html
        nb = nb_client.execute()
        match nb: 
            case {
                "cells": [
                    *prev_cells, 
                    {
                        "outputs": [
                            *prev_outputs, 
                            {
                                "output_type": "execute_result",
                                "data": {"application/json": nb_output_json}
                            }
                        ]
                    }
                ]
            }:
                # Extract data from last output of the last cell of the notebook 
                return nb_name, nb_output_json 
        raise ValueError("Notebook executed but output form was incorrect.")

    @log_runtime
    def execute_upload_multi(self, nb_names: List[str]): 
        """Executes one or more notebooks and uploads their outputs to GCP storage."""
        for nb_name in nb_names:  
            logging.info(f"Executing notebook {nb_name}.")
            nb_name, nb_output_json = self.execute(nb_name)
            logging.info(f"Executed notebook {nb_name}. Writing output.")
            self.storage_client.upload(
                f"{nb_name}.json", json.dumps(nb_output_json)
            )
            logging.info(f"Wrote output of notebook {nb_name}.")


nb_runner = NotebookRunner()


@functions_framework.http
def beanstalk_analytics_handler(request):
    """Top level server router 
    
    Matches incoming requests to one or more jupyter notebook(s). 
    Executes the notebook(s) and writes their outputs to a GCP bucket. 
    
    Notebook output is a JSON object representing a compiled vega spec 
    that can be rendered as is on the client side. 
    """
    # Determine what notebook(s) should be executed 
    nb_names = None 
    match ((name := request.args.get("name", None)) and name.lower()): 
        case nb_name if nb_runner.exists(nb_name):
            nb_names = [nb_name]
        case "*":
            nb_names = nb_runner.names
        case None: 
            return "No name specified", 404 
        case _: 
            return (
                f"Chart with name {name} does not exist. "
                f"Valid options are {nb_runner.names}."
            ), 404 
    try:
        nb_runner.execute_upload_multi(nb_names)
        return "Success", 200
    except BaseException as e:
        err_msg = str(e) or "Internal Server Error"
        logging.error(err_msg)
        return err_msg, 500
