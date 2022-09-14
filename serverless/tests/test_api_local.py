import os
import logging 
import datetime 
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


PATH_SERVERLESS_CODE_DEPLOY = Path(os.environ['PATH_SERVERLESS_CODE_DEPLOY'])
RPATH_NOTEBOOKS = Path(os.environ['RPATH_NOTEBOOKS'])
STORAGE_EMULATOR_HOST_LOCAL = os.environ['STORAGE_EMULATOR_HOST_LOCAL']
RPATH_NOTEBOOKS_TEST = os.environ['RPATH_NOTEBOOKS_TEST']
BUCKET_TEST = os.environ['BUCKET_TEST']


@pytest.fixture
def notebook_data(): 
    # Data objects expected to exist in the returned schemas 
    notebook_data = {
        "notebook_1": [{'data': 1, 'timestamp': 1}, {'data': 1, 'timestamp': 2}],
        "notebook_2": [{'data': 2, 'timestamp': 1}, {'data': 2, 'timestamp': 2}],
        "notebook_3": [{'data': 3, 'timestamp': 1}, {'data': 3, 'timestamp': 2}],
    }
    return notebook_data


@mock.patch.dict(os.environ, {
    "RPATH_NOTEBOOKS": str(PATH_SERVERLESS_CODE_DEPLOY / RPATH_NOTEBOOKS_TEST), 
    "STORAGE_EMULATOR_HOST": STORAGE_EMULATOR_HOST_LOCAL,
})
class TestApiLocal: 

    def setup_method(self, method):
        # Setup and start emulator server.
        self.server = get_emulator_server()
        self.server.start()

    def teardown_method(self, method):
        # Teardown emulator server. 
        self.server.wipe() 
        self.server.stop() 

    @staticmethod
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

    def test_host(self): 
        # Tests that storage host used by api is google cloud 
        assert _get_storage_host() == os.environ['STORAGE_EMULATOR_HOST_LOCAL']

    CHARTS_REFRESH_PARAMETERIZE = [
        # Refresh single chart 
        ({"data": "notebook_1"}, ['notebook_1'],),
        ({"data": "notebook_3"}, ['notebook_3'],), 
        # Refresh multiple charts 
        ({"data": "notebook_1,notebook_2"}, ['notebook_1', 'notebook_2'],),
        # Refresh all charts 
        ({"data": "*"}, ['notebook_1', 'notebook_2', 'notebook_3'],),
    ]

    @pytest.mark.parametrize(
        "query_params,expected_chart_names", CHARTS_REFRESH_PARAMETERIZE
    )
    def test_charts_refresh(
        self, notebook_data, query_params, expected_chart_names
    ):  
        api = get_test_api_client()
        api_data = call_api_validate(
            api, query_params, expected_chart_names, "recomputed",
        )
        schema_names = api_data.keys()
        self.multi_call_storage_validate(schema_names, notebook_data)

    @pytest.mark.parametrize(
        "query_params,expected_chart_names", CHARTS_REFRESH_PARAMETERIZE
    )
    def test_charts_refresh_force_update(
        self, notebook_data, query_params, expected_chart_names
    ):
        api = get_test_api_client()
        call_times = dict()
        for i, (qp, expected_status) in enumerate([
            (query_params, "recomputed"),
            (query_params, "use_cached"),
            ({**query_params, "force_refresh": True}, "recomputed"),
        ]): 
            api_data = call_api_validate(api, qp, expected_chart_names, expected_status)
            schema_names = api_data.keys()
            schema_timestamps = self.multi_call_storage_validate(schema_names, notebook_data)
            call_times[i] = schema_timestamps
        # Ensure that all call_times returned status for same set of schemas
        assert set(call_times[0].keys()) == set(call_times[1].keys()) == set(call_times[2].keys())
        for k in call_times[0].keys(): 
            # Ensure that timestamps for first and second call match 
            assert call_times[0][k] == call_times[1][k]
            # Ensure that timestamps for first call are less than that of third call 
            assert call_times[0][k] < call_times[2][k]


@mock.patch.dict(os.environ, {
    "RPATH_NOTEBOOKS": str(PATH_SERVERLESS_CODE_DEPLOY / RPATH_NOTEBOOKS), 
    "NEXT_PUBLIC_STORAGE_BUCKET_NAME": BUCKET_TEST,
})
class TestApiGCP: 

    # TODO: On setup, log the imported modules 

    schema_names = list(
        p.stem.lower() for p in 
        (Path(PATH_SERVERLESS_CODE_DEPLOY) / Path(RPATH_NOTEBOOKS)).iterdir()
        if p.suffix == '.ipynb'
    )
    # Rather than hardcoding in values (which is annoying bc notebook names)
    # change as we add / delete / modify / etc., We simply check that we are 
    # detecting some of the notebooks. 
    assert len(schema_names) > 3

    def test_host(self): 
        # Tests that storage host used by api is google cloud 
        assert _get_storage_host() == os.environ['STORAGE_HOST']

    def test_bucket(self): 
        # Tests that this class uses the test bucket 
        assert os.environ['NEXT_PUBLIC_STORAGE_BUCKET_NAME'] == os.environ['BUCKET_TEST']

    def test_rpath_notebooks(self): 
        assert os.environ['RPATH_NOTEBOOKS'].endswith(
            os.environ['RPATH_NOTEBOOKS_PROD']
        )

    @pytest.mark.parametrize("schema_name", schema_names)
    def test_charts_refresh(self, schema_name):  
        now = datetime.datetime.now(datetime.timezone.utc)
        api = get_test_api_client()
        query_params = {"data": schema_name, "force_refresh": True}
        expected_schema_names = [schema_name]
        expected_status = "recomputed"
        cf_data = call_api_validate(
            api, query_params, expected_schema_names, expected_status
        )
        for schema_name in cf_data.keys(): 
            tstamp, _ = call_storage_validate(schema_name)
            assert tstamp > now
