This document contains information for application admins. Application admins are 
individuals who have access to the underlying GCP infrastructure that the application 
relies upon to operate. 

Right now, this really just applies to **TBIQ**. But I'm documenting this information 
for future reference for those who want a similar level of control. 

## Prerequisites

Developers will need to do the following 
- Setup a [GCloud Account](https://cloud.google.com/). 
  - Ensure that you enable billing for your account. GCloud gives new users $300 in free credits so 
  you won't actually be charged unless you surpass this amount of credit, which is hard to do. 
- Create a project within your GCloud account for developing this application. 
- Install and authenticate the [GCloud CLI](https://cloud.google.com/sdk/docs/install). 

Note: For all future steps performed through the GCP console, ensure that you are using 
the same project that you created in the steps above. 

### Setup 

Setup is a one-time process admins must undergo to set up the requisite infrastructure. 

#### GCP Storage Bucket Setup 

These steps create a bucket where anyone who has the URL can view its contents. 

1. Go to `Cloud Storage` and then `buckets`. 
2. Create a bucket with 
   1. Region: `us-east1` 
   2. Storage Class: `default` 
   3. Public Access: ` Public to internet` 
   4. Access Control: `Uniform`
   This bucket will store all data for the application 
3. Go to the bucket's permission settings and add a new IAM permission.
   1. Principal: `allUsers` 
   2. Role: `Storage Object Viewer`
4. Enter the google cloud shell 
   1. Run `nano cors.json` amd paste in the value contained in `cors.json` in this repo.
   2. Run `gsutil cors set cors.json gs://BUCKET_NAME`.
   This ensures that bucket resources are accessible from any origin. 

To run the application, you should create three buckets (all following this same process). 

1. A **testing** bucket, used for unit tests. 
2. A **dev** bucket, used during development while testing new features and bug fixes. 
3. A **prod** bucket, used as the production backend for the application. 

Test that everything is working by uploading a test file to the bucket, then 
using the bucket's public url (with the file name appended) to view the contents. 

#### Enable Cloud Function Writing to the Bucket 

These steps create a service account with permission to manage (read + write) 
objects within the bucket created earlier. The google cloud function that we 
will create in a later step will use assume the identity of this service account 
to update objects in the bucket. 

1. Go to `IAM & Admin` and then `Service Accounts`. 
   1. Create a new service account. 
   2. Generate and download a key for this service account (a JSON file).
   3. Move this file into the `serverless` directory.
2. Go to the bucket's permission settings and add a new IAM permission.
   1. Principal: `SERVICE_ACCOUNT_ID` (the id of the service account created in step 1). 
   2. Role: `Storage Object Admin`. 

### Devlopment  

Once [Setup](#setup) has been completed, admins can start acting as developers 
with full control over the application. 

#### Serverless API Overview 

The application uses a single cloud function to serve all client requests. 
This handler is called `bean_analytics_http_handler` and it exists in 
`serverless/main.py`.

This function serves as a router that delegates to internal handlers to 
service different types of requests. Here are the supported routes: 

- `/charts/refresh`
  - Takes one or more chart names as input. For each chart name, we optionally re-compute 
  the corresponding schema. When a schema is re-computed, it is written to the storage 
  bucket.  
  - The schema is recomputed when a schema for the chart does not exist, is older than 
  some number of seconds, or is force refreshed. 
  - The schemas are computed by running jupyter notebooks that exist within 
  `serverless/notebooks/prod`. When building the code bundle to deploy the serverless 
  function, these notebooks are processed into a modified form. 
    - Each of the notebooks within this directory must follow a specific template 
    detailed (TODO: Create section detailing notebook format. Also create notebook template). 

#### Serverless API Deployment 

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