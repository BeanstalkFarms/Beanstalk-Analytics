import os
import json 
import logging 
import time 
import datetime 
from functools import wraps
from typing import Dict, Tuple, List, Optional
from pathlib import Path 

import nbformat
from nbclient import NotebookClient
from google.api_core.exceptions import NotFound
from google.cloud import storage 
from googleapiclient import discovery
import google.auth 


logger = logging.getLogger(__name__)

BUCKET_NAME = os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"]
CREDENTIALS, PROJECT_ID = google.auth.load_credentials_from_file(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])


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
        self.client = storage.Client(project=PROJECT_ID, credentials=CREDENTIALS)
        self.bucket = self.client.bucket(BUCKET_NAME)

    def get_blob(self, name: str, cur_dtime: datetime.datetime): 
        blob = self.bucket.blob(name)
        exists = True 
        try: 
            # ensures object metadata present, as blob doesn't load everything
            blob.reload()
            obj_dtime = blob.time_created
            age_seconds = (cur_dtime - obj_dtime).total_seconds()
        except NotFound as e: 
            exists = False 
            age_seconds = None 
        return blob, exists, age_seconds

    @log_runtime
    def upload(self, blob, data: str) -> None: 
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
