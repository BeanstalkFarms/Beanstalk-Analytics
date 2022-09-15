# Deployment 

## Backend (API) Testing 

Prior to deploying a new version of the cloud function, you must run the unit test suite. 

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

## Backend (API) Deployment 

To deploy (or re-deploy) the handler as a google cloud function, run 

```bash 
make deploy-api
```

To test that the deployed function is operating as expected, execute an HTTP request against it's endpoint 
which can be found through the GCP console.  

```bash 
curl -m 70 -X GET https://us-east1-bean-analytics-http-handler.cloudfunctions.net/bean_analytics_http_handler?data=silo \
-H "Authorization: bearer $(gcloud auth print-identity-token)"
```
