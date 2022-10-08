import logging 

import pytest 
from google.cloud.storage._helpers import _get_storage_host

from emulate_storage import get_emulator_server
from utils import (
    get_test_api_client, 
    call_api_validate, 
    call_storage_validate, 
) 


logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def notebook_data(): 
    # Data objects expected to exist in the returned schemas 
    # The schemas in serverless/notebooks/testing each contain different 
    # data objects so that's where these values originate from. 
    notebook_data = {
        "notebook_1": [{'data': 1, 'timestamp': 1}, {'data': 1, 'timestamp': 2}],
        "notebook_2": [{'data': 2, 'timestamp': 1}, {'data': 2, 'timestamp': 2}],
        "notebook_3": [{'data': 3, 'timestamp': 1}, {'data': 3, 'timestamp': 2}],
    }
    return notebook_data


class TestApiLocal: 

    def setup_method(self, method):
        self.server = get_emulator_server()
        self.server.start()

    def teardown_method(self, method):
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
        assert _get_storage_host() == "http://localhost:9023"

    CHARTS_REFRESH_PARAMETERIZE = [
        # Refresh single chart 
        ({"data": "notebook_1"}, ['notebook_1'],),
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
            # First iteration, no schema exists so it is computed. 
            (query_params, "recomputed"),
            # Second iteration, schema exists so no re-computation. 
            (query_params, "use_cached"),
            # Third iteration, we force refresh so re-computation occurs. 
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
