# Backend Development 

This document covers the process developers will follow to work on the serverless backend.  

## Serverless API Overview 

The application uses a single cloud function to serve all client requests.

- This handler is called `bean_analytics_http_handler` and it exists in 
`serverless/main.py`. 
- Development scripts reference this handler by name via the environment variable 
`CLOUD_FUNCTION_NAME` within the `Makefile`. 

This function serves as a router that delegates to internal handlers to 
service different types of requests. Here are the currently supported routes: 

- `/charts/refresh`
  - Takes one or more chart names as input. For each chart name, we optionally re-compute 
  the corresponding schema. When a schema is re-computed, it is written to the storage 
  bucket.  
  - The schema is recomputed when a schema for the chart does not exist, is older than 
  some number of seconds, or is force refreshed. 
  - The schemas are computed by running jupyter notebooks that exist within 
  `serverless/notebooks/prod`. When building the code bundle to deploy the serverless 
  function, these notebooks are processed into a modified (and more efficient) form. 

## Serverless API Builds 

The code in `serverless` serves as the source code for our google cloud function. However, 
the version of this code that we end up deploying is a little different from the source. 
During the build process, we do the following. 

- Convert `.env` to `.env.yml`, since google requires environment variables files to be in 
  yml format. This file is created and destroyed transparently during the build process. 
- Notebooks are pre-processed, combining all source code into a single cell. Since we 
  execute the notebooks using a notebook client, this removes the storage of intermediate
  (and unnecessary) data outputs, speeding up execution and lowering the memory requirements. 

The built code bundle exists in `.build/serverless`. There are two development commands to 
initiate builds. 

```bash 
make build-api # produces informational textual output 
make build-api-quiet # produces no textual output
``` 

These build commands are pre-requisites to many other makefile rules, so you won't often 
have to issue these commands directly. 

The command `make build-api` has the nice feature that it logs the directory structure 
of the code bundle as it will appear when uploaded to GCP (taking into account the 
`.gcloudignore` file). This is useful as our source directory has lots of files that we 
don't want to upload when deploying, so it's good to run `make-build-api` prior to 
deployments prior to ensure that the source code bundle is as expected. 

## Serverless API Local Development 

## Serverless API Deployment 

To deploy (or re-deploy) the handler as a google cloud function, run 

```bash 
make deploy-api
```

To test that the deployed function is operating as expected, run 

```bash 
curl -m 70 -X GET https://us-east1-tbiq-beanstalk-analytics.cloudfunctions.net/beanstalk_analytics_handler?name=field \
-H "Authorization: bearer $(gcloud auth print-identity-token)"
```




```bash 
curl "http://localhost:8080/api?name=field"
```

```bash
curl "http://localhost:8080/api?name=FieldOverview&force_refresh=True"
```

#### Serverless API Testing 

The name of this is `BUCKET_TEST` in the `Makefile`. 
- This bucket is used by the unit test in `serverless-tests/test_api_gcp.py`. This unit test 
  - Builds and deploys a local version of the api. 
  - Executes a series of calls to the api to refresh objects created by all production notebooks. 
  - Reads these new objects from the test bucket, then validates they have the expected structure 
  and can be rendered as vega-lite charts. 
  - Note: This test only checks that the notebook outputs are written upon api request and that 
  they have the correct structure. Out local api test in `serverless-tests/test_api_emulator.py`