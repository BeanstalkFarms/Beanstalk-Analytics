# Development 

This document covers the process developers will follow to work on the application.

Most of the commands and scripts that need to be executed throughout the development 
process are contained within a `Makefile`. This allows us to run many different kinds 
of commands within different environments using simple commands, facilitating a smooth 
developer experience. 

## Frontend Overview 

The frontend leverages the [Next.js](https://nextjs.org/) React development framework.

Dependencies are managed by yarn. Follow [this](https://yarnpkg.com/getting-started/install)
guide to install yarn on your machine. 

### Frontend Dependencies 

Once yarn is installed, install the Next.js dependencies by running 

```bash 
yarn 
```

## Backend (API) Overview 

The application uses a single serverless google cloud function to serve all client requests.

- This handler is called `bean_analytics_http_handler` and it exists in 
`serverless/main.py`.

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

### Backend (API) Builds 

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

### Backend (API) Local Development 

Prior to deploying the serverless function, it can be tested in a local development environment. 

The local api development environment can run with two kinds of backends

1. Emulator storage bucket
2. GCP storage bucket 

While developing on the API, development should first be done with the emulator bucket backend, 
and once things are working in that environment, you should try using a GCP bucket. 

The local api stack can be run on static builds (not responding to changes in source directory)
with the following two commands. 

```bash
make api-local-bucket-local
make api-local-bucket-gcp
```

The stack can also be run using a hot-reload build (leveraging `nodemon` to re-build when changes
are detected). This kind of environment can be created with the following two commands. 

```bash 
make debug-api-local-bucket-local
make debug-api-local-bucket-gcp 
```

The hot-reload development environment works better with the emulator backend. The hot-reload command 
with the GCP backend is still being worked on (might need to add some delays in here post-rebuild???). 

### Issuing requests to the Locally Deployed Backend (API) 

Once the API is deployed locally, you'll need to send requests to it in order to perform testing. 
You can use whatever tool you like (postman, curl, etc.), but here are some useful curl commands

```bash 
# template 
curl "http://localhost:8080/charts/refresh?data=<data>&force_refresh=<force_refresh>" 
# examples
curl "http://localhost:8080/charts/refresh?data=silo"

curl "http://localhost:8080/charts/refresh?data=silo&force_refresh=true"

curl "http://localhost:8080/charts/refresh?data=silo,fieldoverview"

curl "http://localhost:8080/charts/refresh?data=*"
```

### Backend (API) Testing 

After changing the implementation of the api handler, and testing things using the local 
development stack, the next step is to the the unit test suite. 

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

### Backend (API) Deployment 

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
