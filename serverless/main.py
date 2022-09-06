import os
import json 
from typing import Dict, Tuple 
from pathlib import Path 

import nbformat
import functions_framework
from nbclient import NotebookClient
from google.cloud import storage


class StorageClient: 

    def __init__(self) -> None:
        self.client = storage.Client()
        self.bucket = self.client.bucket(os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"])

    def upload(self, name: str, data: str) -> None: 
        blob = self.bucket.blob(name)
        blob.upload_from_string(data)
        return 


class NotebookMultiplexer: 

    def __init__(self): 
        self.path_notebooks = Path('./notebooks-processed')
        self.notebook_names: Dict[str, str] = {
            # Allows for case insensitive matchine of chart names 
            fpath.stem.lower(): fpath.stem for fpath in self.path_notebooks.iterdir() 
            if fpath.suffix == '.ipynb'
        }

    def names(self): 
        return self.notebook_names.keys()

    def exists(self, nb_key: str): 
        return nb_key in self.notebook_names 

    def execute(self, nb_key: str) -> Tuple[str, Dict]: 
        """Execute notebook and extract output. 
            
            Args: 
                nb_key: The key for the notebook. 
            Returns: 
                nb_name: The name of the notebook.
                data: The data output of the notebook. 
        """
        nb_name = self.notebook_names[nb_key]
        nb_node = nbformat.read(
            str(self.path_notebooks / Path(f"{nb_name}.ipynb")), as_version=4
        )
        nb_client = NotebookClient(
            nb_node, timeout=600, kernel_name='python3', 
            resources={'metadata': {'path': str(self.path_notebooks)}}
        )
        # nb is a dict with structure defined here: https://nbformat.readthedocs.io/en/latest/format_description.html
        nb = nb_client.execute()
        last_cell = nb['cells'] and nb['cells'][-1]
        output = last_cell and last_cell['outputs'] and last_cell['outputs'][-1]
        match output:
            case {"data": {"application/json": data}}: 
                return nb_name, data   
        raise ValueError("Notebook executed but output form was incorrect.")


storage_client = StorageClient()
notebooks = NotebookMultiplexer()


@functions_framework.http
def beanstalk_analytics_handler(request):
    """Top level server router 
    
    Matches incoming requests to a jupyter notebook. 
    Executes the notebook and writes the output to a GCP bucket. 
    Notebook output is a JSON object representing a compiled vega spec 
    that can be rendered as is on the client side. 
    """
    match ((name := request.args.get("name", None)) and name.lower()): 
        case nb_key if notebooks.exists(nb_key):
            try:
                nb_name, data = notebooks.execute(nb_key)
                storage_client.upload(f"{nb_name}.json", json.dumps(data))
                return "Success", 200
            except BaseException as e:
                return str(e), 500 
        case None: 
            err_msg = "No name specified"
        case _: 
            err_msg = f"Chart with name {name} does not exist. Valid options are {notebooks.names()}."
    return err_msg, 404
