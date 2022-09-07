import os
import json 
import logging 
import time 
from functools import wraps
from typing import Dict, Tuple, List, Optional
from pathlib import Path 

import nbformat
from nbclient import NotebookClient
from google.cloud import storage 


logger = logging.getLogger(__name__)


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

    def __init__(self, storage_client: Optional[StorageClient] = None): 
        self.path_notebooks = Path('./notebooks-processed')
        self.ntbk_name_path_map: Dict[str, str] = {
            # Allows for case insensitive matchine of chart names 
            nb_path.stem.lower(): nb_path 
            for nb_path in self.path_notebooks.iterdir() 
            if nb_path.suffix == '.ipynb'
        }
        self.storage_client = storage_client

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
                return nb_name, nb_output_json 
        raise ValueError("Notebook executed but output form was incorrect.")

    @log_runtime
    def execute_upload_many(self, nb_names: List[str]): 
        """Executes one or more notebooks and uploads their outputs to GCP storage."""
        for nb_name in nb_names:  
            logging.info(f"Executing notebook {nb_name}.")
            nb_name, nb_output_json = self.execute(nb_name)
            logging.info(f"Writing output for notebook {nb_name}.")
            if self.storage_client: 
                self.storage_client.upload(
                    f"{nb_name}.json", json.dumps(nb_output_json)
                )
