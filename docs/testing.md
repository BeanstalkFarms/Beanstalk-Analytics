# Testing 

## Backend (API) Testing 

After changing the implementation of the api handler, and testing things using the local 
development stack, the next step is to run the the unit test suite. 

The unit test suite consists of two test files each using different environment configurations

- `serverless-tests/test_api_emulator.py`
  - Uses the local storage bucket. 
  - Uses test notebooks in `serverless/notebooks/testing/`. 
  - Checks that all API routes correctly handle incoming requests. 
  - Checks that the specs returned by the testing notebooks contain expected data. 
- `serverless-tests/test_api_gcp.py`
  - Uses the GCP testing bucket. 
  - Uses the prod notebooks in `serverless/notebooks/prod/`. 
  - Force refreshes all possible production notebooks through the API.
  - Validates that the objects produced to the test bucket have the expected structure, 
  and that the schema portion of the object is a valid vega-lite schema. 

You can run these test files in isolation or together using the following commands 

```bash 
make unit-test-api-emulator # local bucket 
make unit-test-api-gcp # GCP bucket 
make unit-test-api # local and GCP bucket 
``` 

If tests fail in either suite, you can run them individually to debug. 
But prior to deployments, you should always run the tests together. 