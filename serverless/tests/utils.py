import os 
import json
import requests 
import datetime 
from typing import Tuple 
from pathlib import Path 
from urllib.parse import urlencode

import altair as alt 
# TODO: Add link to the functions_framework test where this is used 
from functions_framework import create_app
from google.cloud.storage._helpers import _get_storage_host


"""
WARNING: DO NOT TRY TO IMPORT ENVIRONMENT VARIABLES OUTSIDE OF FUNCTION SCOPES
The tests that use these utility functions patch os.environ depending on their 
purpose, so we want to keep these functions idempotent. 
"""


def get_test_api_client():
    """Testing api client for locally deployed cloud function 

    DO NOT TRY TO MAKE THIS A FIXTURE. Not sure why right now, but 
    the notebook path gets messed up when this is a fixture but not 
    when this is initialized within each test. 
    """
    CLOUD_FUNCTION_NAME = os.environ['CLOUD_FUNCTION_NAME']
    PATH_SERVERLESS_CODE_DEPLOY = os.environ['PATH_SERVERLESS_CODE_DEPLOY']
    path_to_func = str(Path(PATH_SERVERLESS_CODE_DEPLOY) / Path("main.py"))
    flask_app = create_app(
        CLOUD_FUNCTION_NAME, path_to_func, 'http'
    )
    api = flask_app.test_client()
    return api


def call_api_validate(
    api, query_params, expected_schema_names, expected_status
): 
    """Calls api client and validates response object. 
    
    Returns the json parsed data from the response. 
    """
    resp = api.get(f"/charts/refresh?{urlencode(query_params)}")
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert set(expected_schema_names) == set(data.keys())
    for schema_data in data.values(): 
        assert set(['run_time_seconds', "status"]) == set(schema_data.keys())
        if expected_status == "recomputed": 
            assert isinstance(schema_data['run_time_seconds'], float) 
        else: 
            assert schema_data['run_time_seconds'] is None 
        assert schema_data['status'] == expected_status
    return data 


def call_storage_validate(schema_name) -> Tuple[datetime.datetime, dict]:
    """Calls storage client and validates response object. 
    
    Returns the timestamp and schema. 
    """
    BUCKET_NAME = os.environ['NEXT_PUBLIC_STORAGE_BUCKET_NAME']
    url_storage = (
        f"{_get_storage_host()}/{BUCKET_NAME}/schemas/{schema_name}.json"
    )
    resp = requests.get(url_storage) 
    assert resp.status_code == 200
    data = resp.json() 
    match data: 
        case {"timestamp": str(tstamp), "schema": schema}: 
            tstamp = datetime.datetime.fromisoformat(tstamp)
            assert isinstance(tstamp, datetime.datetime)
            alt.Chart.from_json(json.dumps(schema))
        case _: 
            assert False, "Object returned from storage has incorrect structure"
    return tstamp, schema 