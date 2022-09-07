<img src="public/bean-logo-circled.svg" alt="Beanstalk logo" align="right" width="120" />

# Beanstalk-Data-Playground

[![Discord][discord-badge]][discord-url]

[discord-badge]: https://img.shields.io/discord/880413392916054098?label=Beanstalk
[discord-url]: https://discord.gg/beanstalk

**Beanstalk analytics and protocol metrics: [analytics.bean.money](https://analytics.bean.money)**

## Application Architecture 

This application consists of
- A frontend application (next.js) in `pages/`.
- A backend in `serverless` consisting of 
  - Object storage (GCP storage). 
  - Serverless compute (GCP cloud functions). 
    - The single api endpoint for the application exists within `serverless/main.py`.
      - This endpoint is a multipliexer, selecting and executing one of the notebooks in 
      `serverless/notebooks_processed/`. Once the notebook is executed, it's output is 
      extracted and written to GCP Storage. JSON objects representing compiled vega 
      schemas for charts to be visualized in the frontend are stored in this bucket. 

### Prerequisites

Developers will need to do the following 
- Setup a [GCloud Account](https://cloud.google.com/). 
  - Ensure that you enable billing for your account. GCloud gives new users $300 in free credits so 
  you won't actually be charged unless you surpass this amount of credit, which is hard to do. 
- Create a project within your GCloud account for developing this application. 
- Install and authenticate the [GCloud CLI](https://cloud.google.com/sdk/docs/install). 

### Backend 

The backend consists of GCP storage buckets and GCP cloud functions. 

#### Storage 

To run the application either in production or in a development setting where data is read from 
and written to cloud storage, the user will need to set up a GCP storage bucket. 

Contributors who are only concerned with implementing new charts do not need to set
up their own bucket. Instead, they can use the GCP storage emulator to simulate writing 
to and reading from a bucket. 

##### GCP Storage Setup 

1. Within the project you created earlier, go to `Cloud Storage` and then `buckets`. 
2. Create a bucket with 
   1. Region: `us-east1` 
   2. Storage Class: `default` 
   3. Public Access: ` Public to internet` 
   4. Access Control: `Uniform`
   This bucket will store all data for the application 
3. Go to the bucket's permission settings and add a new IAM permission.
   1. Principal: `allUsers` 
   2. Role: `Storage Object Viewer`
   This enables anyone to view the contents of the buckets. 
   TODO: Can we make this more restrictive in some way but still enable all 
   clients to view the contents of the buckets? 
4. Go to `IAM & Admin` and then `Service Accounts`. 
   1. Create a new service account. 
   2. Generate and download a key for this service account (a JSON file).
   This service account will be used by the serverless function to write 
   data to the bucket created earlier. 
5. Go to the bucket's permission settings and add a new IAM permission.
   1. Principal: `SERVICE_ACCOUNT_ID` (the id of the service account created in step 4) 
   2. Role: `Storage Object Admin`
   This enables to serverless function to write to the bucket. 
6. Enter the google cloud shell 
   1. Run `nano cors.json` amd paste in the value contained in `cors.json` in this repo.
   2. Run `gsutil cors set cors.json gs://BUCKET_NAME`.
   This ensures that bucket resources are accessible from any origin. 

##### GCP Cloud Functions Setup 

There is a single serverless function used as the entrypoint for this 
application. The function is `beanstalk_analytics_handler` in 
`serverless/main.py`. This function chooses the appropriate notebook 
to execute, then runs it, extracts its output, then writes it to GCP 
storage. 

To deploy this function, run 

```bash 
python scripts/deploy_cloud_function.py
```

This function wraps the `gcloud functions deploy` command, and performs
some pre-processing and data manipulation logic. 

After deploying the serverless function, run the following command in the 
GCP shell to test that it is working as expected. 

```bash 
set -o allexport; source conf-file; set +o allexport
```

```bash 
curl -m 70 -X GET https://us-east1-tbiq-beanstalk-analytics.cloudfunctions.net/beanstalk_analytics_handler?name=field \
-H "Authorization: bearer $(gcloud auth print-identity-token)"
```

The request should return a `200` status code and there should be a new object
called `Field.json` in the GCP storage bucket. 

```bash
functions-framework --target=beanstalk_analytics_handler --debug 
```

```bash 
curl "http://localhost:8080/api?name=field"
```

TODO: Notes on service account access for this function. 

### Frontend 

Install Next.js dependencies:

```
yarn
```

Setup local environment:

1. `cp .env.example .env`
2. If using an emulator for development, set `NEXT_PUBLIC_CDN` and `STORAGE_EMULATOR_HOST` to point to a local Cloud Storage emulator. A simple proxy is provided via `yarn emulate`, see `test/emulate.py` for more.
3. If testing uploads to a live Cloud Storage bucket: set `NEXT_PUBLIC_STORAGE_BUCKET_NAME` and `GOOGLE_APPLICATION_CREDENTIALS`. You'll need to create a bucket which allows public and a service account with permission to upload files, see below.

Run the local development environment:

```
yarn dev     # Runs the frontend at localhost:3000
yarn emulate # Runs the gcloud emulator at localhost:9023
```

##### TODO's: 

###### High 

- Re-architecture of service account for cloud function 
  - Currently, we deploy a service account key file with the cloud function
  and set a runtime environment variable to point to this key file. 
  - New paradigm
   - Deployed function 
     - https://cloud.google.com/functions/docs/securing/function-identity
     - Add `--service-account` or `--impersonate-service-account` flags to cloud 
     function deploy command. 
       - https://cloud.google.com/sdk/gcloud/reference/functions/deploy#--run-service-account
     - Remove the key from being uploaded and ensure that the 
     `GOOGLE_APPLICATION_CREDENTIALS` env var is not set. 
     - This should allow the function to be invoked with the ability 
     to write to GCP storage. 
   - Local development 
     - Impersonate the service account 
     - https://cloud.google.com/iam/docs/impersonating-service-accounts#attaching-to-resources
     - https://cloud.google.com/iam/docs/impersonating-service-accounts#impersonate-sa-level
     I should be able to impersonate the service account locally when running my local dev 
     stack for google cloud functions. 

###### Medium 

- Serverless source code deployment 
  - Minify the supply increase file. 
    - This is about 1/5 the bundle size right now. Would allow for viewing source online in the GCP console. 
  - Ensure that the notebooks directory is not included in cloud functions deployment 

###### Low 

- Investigate how much we can speed up execution time by converting 
  the notebooks into scripts. 
