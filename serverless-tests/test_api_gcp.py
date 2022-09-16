import os
import logging 
import datetime 
from unittest import mock 
from pathlib import Path 

import pytest 
from google.cloud.storage._helpers import _get_storage_host

from utils import (
    get_test_api_client, 
    call_api_validate, 
    call_storage_validate, 
) 


logging.basicConfig(level=logging.DEBUG)


RPATH_NOTEBOOKS = Path(os.environ['RPATH_NOTEBOOKS'])


class TestApiGCP: 

    schema_names = list(
        p.stem.lower() for p in RPATH_NOTEBOOKS.iterdir() if p.suffix == '.ipynb'
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
