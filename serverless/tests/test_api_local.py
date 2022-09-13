import os
import logging 
from unittest import mock 
from pathlib import Path 

import pytest 
from google.cloud.storage._helpers import _get_storage_host

from tests.emulate_storage import get_emulator_server
from tests.utils import (
    get_test_api_client, 
    call_api_validate, 
    call_storage_validate, 
) 


logging.basicConfig(level=logging.DEBUG)


PATH_SERVERLESS_CODE_DEPLOY = os.environ['PATH_SERVERLESS_CODE_DEPLOY']
RPATH_NOTEBOOKS = os.environ['RPATH_NOTEBOOKS']
STORAGE_EMULATOR_HOST = os.environ['STORAGE_EMULATOR_HOST']
environ_patch = {
    "RPATH_NOTEBOOKS": str(Path(PATH_SERVERLESS_CODE_DEPLOY) / Path(RPATH_NOTEBOOKS))
}

@pytest.fixture 
def server(): 
    # Emulator server simulates GCP storage bucket locally 
    server = get_emulator_server()
    server.start()
    yield server
    server.wipe() 
    server.stop() 


@pytest.fixture
def notebook_data(): 
    # Data objects expected to exist in the returned schemas 
    notebook_data = {
        "notebook_1": [{'data': 1, 'timestamp': 1}, {'data': 1, 'timestamp': 2}],
        "notebook_2": [{'data': 2, 'timestamp': 1}, {'data': 2, 'timestamp': 2}],
        "notebook_3": [{'data': 3, 'timestamp': 1}, {'data': 3, 'timestamp': 2}],
    }
    return notebook_data
  

def multi_call_storage_validate(schema_names, notebook_data):
    """Retrieves schemas from storage, validates they contain specific data. """
    schema_timestamps = dict()
    for schema_name in schema_names: 
        tstamp, schema = call_storage_validate(schema_name)
        assert (
            schema['datasets'][schema['data']['name']] 
            == notebook_data[schema_name]
        )
        schema_timestamps[schema_name] = tstamp
    return schema_timestamps


CHARTS_REFRESH_PARAMETERIZE = [
    # Refresh single chart 
    ({"data": "notebook_1"}, ['notebook_1'],),
    ({"data": "notebook_3"}, ['notebook_3'],), 
    # Refresh multiple charts 
    ({"data": "notebook_1,notebook_2"}, ['notebook_1', 'notebook_2'],),
    # Refresh all charts 
    ({"data": "*"}, ['notebook_1', 'notebook_2', 'notebook_3'],),
]


def test_host(): 
    assert _get_storage_host() == 'http://localhost:9023'


@mock.patch.dict(os.environ, environ_patch)
@pytest.mark.parametrize(
    "query_params,expected_chart_names", CHARTS_REFRESH_PARAMETERIZE
)
def test_charts_refresh(
    server, notebook_data, query_params, expected_chart_names
):  
    api = get_test_api_client()
    api_data = call_api_validate(
        api, query_params, expected_chart_names, "recomputed",
    )
    schema_names = api_data.keys()
    multi_call_storage_validate(schema_names, notebook_data)


@mock.patch.dict(os.environ, environ_patch)
@pytest.mark.parametrize(
    "query_params,expected_chart_names", CHARTS_REFRESH_PARAMETERIZE
)
def test_charts_refresh_force_update(
    server, notebook_data, query_params, expected_chart_names
):
    api = get_test_api_client()
    # First call, no data exists so charts will be computed 
    api_data = call_api_validate(
        api, query_params, expected_chart_names, "recomputed",
    )
    schema_names_one = api_data.keys()
    schema_timestamps_one = multi_call_storage_validate(schema_names_one, notebook_data)
    # Second call, data exists so no re-computation occurs 
    api_data = call_api_validate(
        api, query_params, expected_chart_names, "use_cached",
    )
    schema_names_two = api_data.keys()
    schema_timestamps_two = multi_call_storage_validate(schema_names_two, notebook_data)
    # Third call, we force refresh 
    query_params = {**query_params, "force_refresh": True}
    api_data = call_api_validate(
        api, query_params, expected_chart_names, "recomputed",
    )
    schema_names_three = api_data.keys()
    schema_timestamps_three = multi_call_storage_validate(schema_names_three, notebook_data)
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
    # Ensure that timestamps for first call are less than that of third call 
    for k in schema_timestamps_one.keys(): 
        assert (
            schema_timestamps_one[k] < schema_timestamps_three[k]
        )
