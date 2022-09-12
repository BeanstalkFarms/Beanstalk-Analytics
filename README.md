<img src="public/bean-logo-circled.svg" alt="Beanstalk logo" align="right" width="120" />

# Beanstalk-Data-Playground

[![Discord][discord-badge]][discord-url]

[discord-badge]: https://img.shields.io/discord/880413392916054098?label=Beanstalk
[discord-url]: https://discord.gg/beanstalk

**Beanstalk analytics and protocol metrics: [analytics.bean.money](https://analytics.bean.money)**

## Application Architecture 

This application consists of
- A frontend application (next.js) contained in various top level directories.
  - The main application 
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

```bash
curl "http://localhost:8080/api?name=FieldOverview&force_refresh=True"
```

TODO: Notes on service account access for this function. 

### HTTPS Load Balancer 

Follow [this](https://cloud.google.com/cdn/docs/setting-up-cdn-with-bucket) guide for setting up an HTTP Load Balancer that uses a storage bucket as a backend. 

Create a **Global External HTTP(S)** load balancer, as the classic load balancer doesn't support CORS. 

Create an IAM role of `Compute -> Load Balancer Admin` for service account. 

Go to Cloud CDN, select the backend bucket, then go to the caching section to monitor recent cache invalidation requests. 

Use [this](https://console.cloud.google.com/logs/query;query=resource.type%3D%22http_load_balancer%22%0Aresource.labels.forwarding_rule_name%3D%22http-lb%22;summaryFields=:false:32:beginning;cursorTimestamp=2022-09-09T04:18:55.301642Z?_ga=2.177749413.1458977516.1662403865-1595580898.1662403865&_gac=1.87929578.1662597955.Cj0KCQjwguGYBhDRARIsAHgRm4_hIPBcIbRNh_KE8yYIQfwdzvktlvWvv0_WpwqSZ6zNVn2feLtvwdQaAtYPEALw_wcB&project=tbiq-beanstalk-analytics) link to monitor the logs for the https load balancer (filtering by forwarding rule to 
isolate this component). This allows us to investigate whether or not requests to the load balancer were cache hits / misses. 

To retrieve a value from the load balancer (with CDN enabled we need to hit the IP address of the load balancer). 

example: `http://34.117.61.253/Field.json?1234568`

Appending a random number to the end bypasses browser based caching. 

[Programmatic cache invalidation](https://cloud.google.com/compute/docs/reference/rest/v1/urlMaps/invalidateCache?apix_params=%7B%22project%22%3A%22tbiq-beanstalk-analytics%22%2C%22urlMap%22%3A%22http-lb%22%2C%22resource%22%3A%7B%22path%22%3A%22%2FField.json%22%7D%7D)

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

google auth docs: https://google-auth.readthedocs.io/en/master/reference/google.auth.html#google.auth.default

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

```bash 
gcloud meta list-files-for-upload .build-serverless/deploy  
```