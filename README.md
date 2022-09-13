<img src="public/bean-logo-circled.svg" alt="Beanstalk logo" align="right" width="120" />

# Beanstalk-Data-Playground

[![Discord][discord-badge]][discord-url]

[discord-badge]: https://img.shields.io/discord/880413392916054098?label=Beanstalk
[discord-url]: https://discord.gg/beanstalk

**Beanstalk analytics and protocol metrics: [analytics.bean.money](https://analytics.bean.money)**

## Application Architecture 

This application consists of
- A frontend application (next.js) contained in various top level directories.
  - The frontend ingests and visualizes data created by the serverless backend.
- Google Cloud Platform Infrastructure 
  - A GCP storage bucket containing vega-lite schemas and other application data.  
- A serverless backend in `serverless` 
  - A single http request handler is defined in `serverless/main.py`. This handler 
  serves as a router that routes incoming requests to the appropriate internal handler 
  function. It supports the following routes
    - `/charts/refresh`: This route takes one or more schema names as input and for each 
    one, optionally re-computes the schema. The schema is recomputed when a schema for 
    the chart does not exist, is older than some number of seconds, or is force refreshed. 
    When a schema is re-computed, it is written to a GCP storage bucket.  
  - The `charts/refresh` route detailed above internally executes jupyter notebooks that 
  exist in `serverless/notebooks/prod`. Each of these notebooks produces a vega-lite schema, 
  and each notebook in this directory must adhere to a specific structure. 


#### Storage 

To run the application either in production or in a development setting where data is read from 
and written to cloud storage, the user will need to set up a GCP storage bucket. 

Contributors who are only concerned with implementing new charts do not need to set
up their own bucket. Instead, they can use the GCP storage emulator to simulate writing 
to and reading from a bucket. 



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

TODO: Cors enable all buckets. 