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

## Local Development Environment 

The local development environment for the full-stack application supports two kinds of backends 

1. Emulator storage bucket
2. GCP storage bucket 

While developing, it is recommended to initially work with the emulator bucket backend, to avoid 
issuing unnecessary requests to google cloud. Once things are working as expected with the emulator, 
you should switch to testing with the gcp bucket backend. 

When issuing commands to start either the frontend or API with either the emulator or GCP backends, 
make sure to issue commands to both parts of the application that use the same backend. 

Also, if you are planning on running the development stack with the emulator backend, you must 
separately start the emulator server by running

```bash 
make local-bucket
``` 

### Backend (API) Local Development Environment  

The API supports both a static and hot-reload development stack. 

The start the API development stack, run one of these commands  

```bash
# Run API on static builds 
make api-dev-bucket-local 
make api-dev-bucket-gcp 

# Run API on hot-reloaded builds 
make debug-api-dev-bucket-local
make debug-api-dev-bucket-gcp 
```

The hot-reload development environment works better with the emulator backend. The hot-reload command 
with the GCP backend is still being worked on (might need to add some delays in here post-rebuild???). 

#### Issuing requests to the Locally Deployed Backend (API) 

If you want to test the backend in isolation (without frontend running locally), you can simply 
send HTTP commands to it using your preferred tool. Here are some useful testing commands. 

```bash 
# template 
curl "http://localhost:8080/charts/refresh?data=<data>&force_refresh=<force_refresh>" 
# examples
curl "http://localhost:8080/charts/refresh?data=silo"

curl "http://localhost:8080/charts/refresh?data=silo&force_refresh=true"

curl "http://localhost:8080/charts/refresh?data=silo,fieldoverview"

curl "http://localhost:8080/charts/refresh?data=*"
```

### Frontend Local Development Environment  

<!-- TODO: Does the frontend support hot-reloading? -->

The start the frontend development stack, run one of these commands  

```bash
make frontend-dev-bucket-local
make frontend-dev-bucket-gcp
```
