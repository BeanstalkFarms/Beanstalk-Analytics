import datetime
import os
import logging 
from unittest import mock 
from pathlib import Path 

import pytest 
from google.cloud.storage._helpers import _get_storage_host

from tests.utils import (
    get_test_api_client, 
    call_api_validate, 
    call_storage_validate, 
)


logging.basicConfig(level=logging.DEBUG)


PATH_SERVERLESS_CODE_DEV = os.environ['PATH_SERVERLESS_CODE_DEV']
PATH_SERVERLESS_CODE_DEPLOY = os.environ['PATH_SERVERLESS_CODE_DEPLOY']
RPATH_NOTEBOOKS = os.environ['RPATH_NOTEBOOKS']
environ_patch = {
    "RPATH_NOTEBOOKS": str(Path(PATH_SERVERLESS_CODE_DEPLOY) / Path(RPATH_NOTEBOOKS))
}

notebook_names = list(
    p.stem.lower() for p in 
    (Path(PATH_SERVERLESS_CODE_DEPLOY) / Path(RPATH_NOTEBOOKS)).iterdir()
    if p.suffix == '.ipynb'
)
# Rather than hardcoding in values (which is annoying bc notebook names)
# change as we add / delete / modify / etc., We simply check that we are 
# detecting some of the notebooks. 
assert len(notebook_names) > 3

# notebook_names = notebook_names[:1]

def test_host(): 
    assert _get_storage_host() == 'https://storage.googleapis.com'


@mock.patch.dict(os.environ, environ_patch)
@pytest.mark.parametrize("schema_name", notebook_names)
def test_charts_refresh(schema_name):  
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
