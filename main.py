import os
import json
from pathlib import Path 

import nbformat
import functions_framework
from nbclient import NotebookClient
from google.cloud import storage


path_notebooks = Path('./notebooks')
notebook_names = {
    # Allows for case insensitive matchine of chart names 
    fpath.stem.lower(): fpath.stem for fpath in path_notebooks.iterdir() 
    if fpath.suffix == '.ipynb'
}


class StorageClient: 

    def __init__(self) -> None:
        self.client = storage.Client()
        self.bucket = self.client.bucket(os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"])

    def upload(self, name: str, data: str) -> None: 
        blob = self.bucket.blob(name)
        blob.upload_from_string(data)
        return 


storage_client = StorageClient()


def handler(nb_name: str): 
    # Setup notebook client. 
    nb = nbformat.read(
        str(path_notebooks.joinpath(f"{nb_name}.ipynb")), as_version=4
    )
    client = NotebookClient(
        nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': str(path_notebooks)}}
    )
    # Execute notebook. 
    try:
        nb = client.execute()
    except BaseException as e:
        return str(e), 500
    # Extract notebook output and write to GCP Storage. 
    match nb: 
        case {"cells": [*cells, {"outputs": [{"data": {"application/json": res}}, *next_outputs]}]}:
            storage_client.upload(f"{nb_name}.json", json.dumps(res))
            return "success", 200
    return "Notebook executed but did not produce an output.", 500 


@functions_framework.http
def my_http_function(request):
    """Top level server routing handler 
    
    Routes incoming requests to the correct notebook containing 
    logic that produces a compiled vega spec. 
    """
    name = request.args.get("name")
    match (name and name.lower()): 
        case None: 
            return "No name specified", 404
        case valid_name if valid_name in notebook_names: 
            return handler(notebook_names[valid_name])
        case _: 
            print(notebook_names)
            return (
                f"Chart with name {name} does not exist. "
                f"Valid options are {notebook_names.keys()}."
            ), 404
