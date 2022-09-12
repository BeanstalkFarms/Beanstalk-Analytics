from datetime import datetime
import os
import requests 
import json 
import logging 
import datetime 
from urllib.parse import urlencode
from unittest import mock 
from pathlib import Path 

import pytest 
from functions_framework import create_app

from tests.emulate_storage import get_emulator_server


logging.basicConfig(level=logging.DEBUG)


SERVERLESS_HANDLER = os.environ['SERVERLESS_HANDLER']
PATH_SERVERLESS_CODE_DEV = os.environ['PATH_SERVERLESS_CODE_DEV']
PATH_SERVERLESS_CODE_DEPLOY = os.environ['PATH_SERVERLESS_CODE_DEPLOY']
PATH_NOTEBOOKS = os.environ['PATH_NOTEBOOKS']
STORAGE_EMULATOR_HOST = os.environ['STORAGE_EMULATOR_HOST']
BUCKET_NAME = os.environ['NEXT_PUBLIC_STORAGE_BUCKET_NAME']

assert STORAGE_EMULATOR_HOST == 'http://localhost:9023'


@pytest.fixture 
def server(): 
    server = get_emulator_server()
    server.start()
    yield server
    server.wipe() 
    server.stop() 


def get_cloud_function():
    """Testing client for locally deployed cloud function 

    DO NOT TRY TO MAKE THIS A FIXTURE. Not sure why right now, but 
    the notebook path gets messed up when this is a fixture but not 
    when this is initialized within each test. 
    """
    path_to_func = str(Path(PATH_SERVERLESS_CODE_DEPLOY) / Path("main.py"))
    cloud_function = create_app(
        SERVERLESS_HANDLER, path_to_func, 'http'
    ).test_client()
    return cloud_function


@pytest.fixture
def notebook_data(): 
    notebook_1_data = [{'data': 1, 'timestamp': 1}, {'data': 1, 'timestamp': 2}]
    notebook_2_data = [{'data': 2, 'timestamp': 1}, {'data': 2, 'timestamp': 2}]
    notebook_3_data = [{'data': 3, 'timestamp': 1}, {'data': 3, 'timestamp': 2}]
    notebook_data = {
        "notebook_1": notebook_1_data,
        "notebook_2": notebook_2_data,
        "notebook_3": notebook_3_data,
    }
    return notebook_data


def get_chart_names_from_query_params(query_params): 
    qp_data = query_params['data']
    if qp_data == '*': 
        chart_names = ["notebook_1", "notebook_2", "notebook_3"]
    elif ',' in qp_data: 
        chart_names = qp_data.split(",")
    else: 
        chart_names = [qp_data]
    return chart_names 


def call_cloud_function_validate_response(
    cloud_function, query_params, expected_status
): 
    cf_resp = cloud_function.get(f"/charts/refresh?{urlencode(query_params)}")
    cf_data = json.loads(cf_resp.data)
    assert cf_resp.status_code == 200
    chart_names = get_chart_names_from_query_params(query_params)
    assert set(chart_names) == set(cf_data.keys())
    for chart_data in cf_data.values(): 
        assert set(['run_time_seconds', "status"]) == set(chart_data.keys())
        if expected_status == "recomputed": 
            assert isinstance(chart_data['run_time_seconds'], float) 
        else: 
            assert chart_data['run_time_seconds'] is None 
        assert chart_data['status'] == expected_status
    return cf_data 


def get_schemas_from_storage(schema_names, notebook_data):
    schema_timestamps = dict()
    for schema_name in schema_names: 
        url_storage = (
            f"{STORAGE_EMULATOR_HOST}/{BUCKET_NAME}/schemas/{schema_name}.json"
        )
        storage_resp = requests.get(url_storage) 
        assert storage_resp.status_code == 200
        success = False 
        match storage_resp.json(): 
            case {"timestamp": str(tstamp), "schema": schema}: 
                schema_timestamps[schema_name] = (
                    datetime.datetime.fromisoformat(tstamp)
                )
                assert isinstance(schema_timestamps[schema_name], datetime.datetime)
                success = (
                    schema['datasets'][schema['data']['name']] 
                    == notebook_data[schema_name]
                )
        assert success
    return schema_timestamps


CHARTS_REFRESH_TEST_QUERY_PARAMS = [
    # Refresh single chart 
    (
        {"data": "notebook_1"}
    ),
    (
        {"data": "notebook_3"}
    ), 
    # Refresh multiple charts 
    (
        {"data": "notebook_1,notebook_2"}
    ),
    # Refresh all charts 
    (
        {"data": "*"}
    ),
]


@mock.patch.dict(os.environ, {
    "PATH_NOTEBOOKS": str(Path(PATH_SERVERLESS_CODE_DEPLOY) / Path(PATH_NOTEBOOKS))
})
@pytest.mark.parametrize(
    "query_params", CHARTS_REFRESH_TEST_QUERY_PARAMS
)
def test_charts_refresh(
    server, notebook_data, query_params
):  
    cloud_function = get_cloud_function()
    cf_data = call_cloud_function_validate_response(
        cloud_function, query_params, "recomputed",
    )
    get_schemas_from_storage(cf_data.keys(), notebook_data)


@mock.patch.dict(os.environ, {
    "PATH_NOTEBOOKS": str(Path(PATH_SERVERLESS_CODE_DEPLOY) / Path(PATH_NOTEBOOKS))
})
@pytest.mark.parametrize(
    "query_params", CHARTS_REFRESH_TEST_QUERY_PARAMS
)
def test_charts_refresh_force_update(
    server, notebook_data, query_params
):
    cloud_function = get_cloud_function()
    # First call, no data exists so charts will be computed 
    cf_data = call_cloud_function_validate_response(
        cloud_function, query_params, "recomputed",
    )
    schema_timestamps_one = get_schemas_from_storage(cf_data.keys(), notebook_data)
    # Second call, data exists so no re-computation occurs 
    cf_data = call_cloud_function_validate_response(
        cloud_function, query_params, "use_cached",
    )
    schema_timestamps_two = get_schemas_from_storage(cf_data.keys(), notebook_data)
    # Third call, we force refresh 
    query_params = {**query_params, "force_refresh": True}
    cf_data = call_cloud_function_validate_response(
        cloud_function, query_params, "recomputed",
    )
    schema_timestamps_three = get_schemas_from_storage(cf_data.keys(), notebook_data)
    # Ensure that all calls returned status for same set of schemas
    assert (
        set(schema_timestamps_one.keys()) == 
        set(schema_timestamps_two.keys()) == 
        set(schema_timestamps_three.keys()) 
    )
    # Ensure that timestamps for first and second call match 
    for k in schema_timestamps_one.keys(): 
        assert (
            schema_timestamps_one[k] == schema_timestamps_two[k]
        ) 
    # Ensure that timestamps for first call are less than that for third call 
    for k in schema_timestamps_one.keys(): 
        assert (
            schema_timestamps_one[k] < schema_timestamps_three[k]
        )
