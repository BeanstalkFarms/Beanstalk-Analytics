import os 
import json
import requests 
import datetime 
from typing import Tuple 
from pathlib import Path 
from urllib.parse import urlencode

import altair as alt 
from google.cloud.storage._helpers import _get_storage_host

# TODO: Add link to the functions_framework test where this is used 
from functions_framework import create_app

"""
WARNING: DO NOT TRY TO IMPORT ENVIRONMENT VARIABLES OUTSIDE OF FUNCTION SCOPES
The tests that use these utility functions patch os.environ depending on their 
purpose, so we want to keep these functions idempotent. 
"""


def get_test_api_client():
    """Testing api client for locally deployed cloud function 

    The function `create_app` has some really nasty side effects 
    that are difficult to work around. Internally, it dynamically 
    creates a module for the file containing the function. In our 
    testing setup, we test with multiple different patches on 
    os.environ. I tried and failed to put tests in different files 
    but since the serverless build isn't a package (it's just a 
    module), things got tricky and I reverted to the separate 
    test files approach. 

    DO NOT TRY TO MAKE THIS A FIXTURE. I WILL HURT YOU IF YOU DO! 
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
    resp = api.get(f"/schemas/refresh?{urlencode(query_params)}")
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert set(expected_schema_names) == set(data.keys())
    for schema_data in data.values(): 
        assert len(schema_data.keys()) == 1
        assert schema_data['status'] == expected_status
    return data 


def call_storage_validate(schema_name) -> Tuple[datetime.datetime, dict]:
    """Calls storage client and validates response object. 
    
    Returns the timestamp and schema. 
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    BUCKET_NAME = os.environ['NEXT_PUBLIC_STORAGE_BUCKET_NAME']
    url_storage = (
        # Appending timestamp to querystring bypasses caching
        f"{_get_storage_host()}/{BUCKET_NAME}/schemas/{schema_name}.json?{now.isoformat()}"
    )
    resp = requests.get(url_storage) 
    assert resp.status_code == 200
    data = resp.json() 
    match data: 
        case {
            "timestamp": str(tstamp), "schema": schema, "run_time_seconds": float(run_secs)
        }: 
            tstamp = datetime.datetime.fromisoformat(tstamp)
            assert isinstance(tstamp, datetime.datetime)
            assert run_secs
            alt.Chart.from_json(json.dumps(schema))
        case _: 
            assert False, "Object returned from storage has incorrect structure"
    return tstamp, schema 