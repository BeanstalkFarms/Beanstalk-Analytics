import os 
import requests 
import logging 
from unittest import mock 
from pathlib import Path 

import pytest 
from functions_framework import create_app

from emulate_storage import get_emulator_server

logging.basicConfig(level=logging.DEBUG)


PATH_SERVERLESS_CODE_DEV = os.environ['PATH_SERVERLESS_CODE_DEV']
PATH_SERVERLESS_CODE_DEPLOY = os.environ['PATH_SERVERLESS_CODE_DEPLOY']
PATH_NOTEBOOKS = os.environ['PATH_NOTEBOOKS']
STORAGE_EMULATOR_HOST = os.environ['STORAGE_EMULATOR_HOST']


@pytest.fixture 
def server(): 
    _server = get_emulator_server()
    _server.start()
    yield _server 
    _server.wipe() 
    _server.stop() 


@mock.patch.dict(os.environ, {
    "PATH_NOTEBOOKS": str(Path(PATH_SERVERLESS_CODE_DEPLOY) / Path(PATH_NOTEBOOKS))
})
@pytest.mark.parametrize(
    "url", [
        (
            "http://localhost:8080/api?name=FieldOverview&force_refresh=True",
        )
    ]
)
def test_api_local(server, url):
    assert STORAGE_EMULATOR_HOST == 'http://localhost:9023'
    func_name = "bean_analytics_http_handler"
    path_to_func = str(Path(PATH_SERVERLESS_CODE_DEPLOY) / Path("main.py"))
    client = create_app(func_name, path_to_func, 'http').test_client()
    resp = client.post("/api?name=notebook_1&force_refresh=True")
    assert resp.status_code == 200
    print(resp)
    print(resp.data)
    # assert resp.data == b"success"
    
    
    # resp = requests.get(url)
    # print(resp)

