# Development Guide 

Most of the commands and scripts that need to be executed throughout the development 
process are contained within a `Makefile`. This allows us to run many different kinds 
of commands within different environments using simple commands, facilitating a smooth 
developer experience. 

## Environment File 

Most environment variables are public and currently exist in the `Makefile`, which 
is versioned on github. 

You should also create a file called `.env` in the root directory of this project. 
This file name is already included in `.gitignore` so this file won't be versioned. 

Within this file, define the following key value pairs. 

- `PATH_PROJECT`: The absolute file path to the project root directory. 
  - This is defined as a safety measure, as some of the build processes use file 
  system commands (`shutil.rmtree`) that could potentially be dangerous if run 
  incorrectly. I've implemented a "safe" wrapper around this method in `scripts/python/safe_rmtree.py` 
  that ensures that this environment variable is set prior to performing any operations. 
- `GOOGLE_APPLICATION_CREDENTIALS`: The name of the service account credentials file. This 
  File should exist both in the root directory, and also in `backend/src`, but the value of 
  this variable should point to the one in the root directory (i.e. it is just the filename). 
  The pattern `**/*ceaec.json ` in `.gitignore` should prevent any service account key file 
  created by developers from being versioned, but take extra precautions here. 

## Frontend Overview 

The frontend leverages the [Next.js](https://nextjs.org/) React development framework.

Dependencies are managed via yarn. Follow [this](https://yarnpkg.com/getting-started/install)
guide to install yarn on your machine. 

### Frontend Dependencies 

Once yarn is installed, install the Next.js dependencies by running 

```bash 
yarn 
```

## Backend (API) Overview 

The application uses a single serverless google cloud function to serve all client requests.

- This handler is called `bean_analytics_http_handler` and it exists in `backend/src/main.py`.

This function serves as a router that delegates to internal handlers to 
service different types of requests. Here are the currently supported routes: 

- `/schemas/refresh`
  - Takes one or more chart names as input. For each chart name, we optionally re-compute 
  the corresponding schema. When a schema is re-computed, it is written to the storage 
  bucket.  
  - The schema is recomputed when a schema does not exist, is older than some number of 
  seconds, or is force refreshed. 
  - The schemas are computed by running jupyter notebooks that exist within 
  `backend/src/notebooks/prod`. When building the code bundle to deploy the serverless 
  function, these notebooks are processed into a modified (and more efficient) form. 

### Backend Environment and Dependencies 

The backend is written in python, so you will need to set up a python (3.10) virtual 
environment for backend development. The application is agnostic to the tool that you 
use for managing environment, but I prefer conda personally. 

[Here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) is a 
guide for installing conda.  

[Here](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html#managing-envs) is a 
guide on managing conda environments. 

Assuming you have conda installed, create a python 3.10 environment. Here are the commands to 
create, activate, and deactivate your virtual development environment. 

```bash 
# create 
conda create --name bean-analytics python=3.10
# activate
conda activate bean-analytics 
# de-activate 
conda deactivate 
```

Within your conda (or other platform) virtual environment, install the dependencies in both 
`backend/requirements.txt` and `backend/requirements.dev.txt`. 

I personally use pip for this 

```bash 
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
```

Whenever you are developing the application, I recommend having this environment active. 
Many `Makefile` commands require it. 

### Backend (API) Builds 

The code in `backend/src` serves as the source code for our google cloud function. However, 
the version of this code that we end up deploying is a little different from the source. 
During the build process, we do the following. 

- Convert `.env` to `.env.yml`, since google requires environment variables files to be in 
  yml format. This file is created and destroyed transparently during the build process. It 
  only includes a necessary subset of variables from the build command's runtime context. 
- Notebooks are pre-processed, combining all source code into a single cell. Since we 
  execute the notebooks using a notebook client, this removes the storage of intermediate
  (and unnecessary) data outputs, speeding up execution and lowering the memory requirements. 

The built code bundle exists in `.build/serverless`. There are two development commands to 
initiate builds. 

```bash 
# produces informational textual output 
make build-api       
# produces no textual output
make build-api-quiet 
``` 

These build commands are pre-requisites to many other makefile rules, so you won't often 
have to issue these commands directly. 

The command `make build-api` has the nice feature that it logs the directory structure 
of the code bundle as it will appear when uploaded to GCP (taking into account the 
`.gcloudignore` file). This is useful as our source directory has lots of files that we 
don't want to upload when deploying, so it's good to run `make-build-api` prior to 
deployments prior to ensure that the source code bundle looks like you expect it to.

## Local Development Environment 

The local development environment consists of 

- Locally deployed google cloud function on `http://localhost:8080`
- Locally deployed frontend on `http://localhost:3000`
- Two kinds of storage backends 
  1. Emulator storage bucket
  2. GCP storage bucket 

While developing, it is recommended to initially work with the emulator bucket backend, to avoid 
issuing unnecessary requests to google cloud. Once things are working as expected with the emulator, 
you should switch to testing with the gcp bucket backend. 

There are separate commands to start the frontend and the API, and it is recommended to start both 
in different terminal windows so you have access to the logs for both. When issuing commands to start 
both the API and the frontend, ensure that both commands you issue target the same backend to avoid 
issues. These specific commands will be covered in the sections below. 

Additionally, if using the emulator backend, start the emulator in a separate terminal window 
(again so you can see the logs) by running 

```bash 
make local-bucket
``` 

### Local Development Environment - Frontend

The frontend supports both a static and hot-reload development stack. 

The start the frontend development stack, run one of these commands  

```bash
# static build / emulator backend 
make frontend-dev-bucket-local
# static build / gcp backend 
make frontend-dev-bucket-gcp
# hot-reload build / emulator backend 
make frontend-start-bucket-local
# hot-reload build / gcp backend 
make frontend-start-bucket-gcp
```

### Local Development Environment - Backend (API) 

The API supports both a static and hot-reload development stack. 

The start the API development stack, run one of these commands  

```bash
# static build / emulator backend 
make api-dev-bucket-local 
# static build / gcp backend 
make api-dev-bucket-gcp 
# hot-reload build / emulator backend 
make debug-api-dev-bucket-local
# hot-reload build / gcp backend 
make debug-api-dev-bucket-gcp 
```

The hot-reload development environment works better with the emulator backend. The hot-reload command 
with the GCP backend is still being worked on (might need to add some delays in here post-rebuild???). 

#### Issuing requests to the Locally Deployed Backend (API) 

If you want to test the backend in isolation (without the frontend running locally), you can simply 
send HTTP commands to it using your preferred tool. Here are some useful testing commands. 

```bash 
# template 
curl "http://localhost:8080/schemas/refresh?data=<data>&force_refresh=<force_refresh>" 
# examples
curl "http://localhost:8080/schemas/refresh?data=silo"

curl "http://localhost:8080/schemas/refresh?data=silo&force_refresh=true"

curl "http://localhost:8080/schemas/refresh?data=silo,farmers_market_volume"

curl "http://localhost:8080/schemas/refresh?data=*"
```

