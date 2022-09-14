# Cloud Infrastructure Setup 

All of the cloud infrastructure for this application is provided by Google Cloud Platform. 

At a high level, the required cloud infrastructure for this application includes 

- A GCP storage bucket. This serves as a persistant data store for application data. 
- A GCP cloud function. The API that services client requests is serverless. When invoked 
it interprets users requests and makes modifications to objects in the storage bucket. 

## Prerequisites

Developers will need to do the following 
- Setup a [GCloud Account](https://cloud.google.com/). 
  - Ensure that you enable billing for your account. GCloud gives new users $300 in free credits so 
  you won't actually be charged unless you surpass this amount of credit, which is hard to do. 
- Create a project within your GCloud account for developing this application. 
- Install and authenticate the [GCloud CLI](https://cloud.google.com/sdk/docs/install). 

Note: Use the project created above for all GCP console and GCP client library interactions. 

## Create Storage Buckets 

These steps create a publically accessible storage bucket. Anyone with the URL can view it's contents. 

1. Go to `Cloud Storage` and then `buckets`. 
2. Create a bucket with 
   1. Region: `us-east1` 
   2. Storage Class: `default` 
   3. Public Access: ` Public to internet` 
   4. Access Control: `Uniform`
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

## Enable Cloud Function Writing to the Bucket 

These steps create a service account with permission to manage (read + write) 
objects within the bucket created earlier. The google cloud function that we 
will create in a later step will use assume the identity of this service account 
to manage objects in the bucket. 

1. Go to `IAM & Admin` and then `Service Accounts`. 
   1. Create a new service account. 
   2. Generate and download a key for this service account (a JSON file).
   3. Move this file into the `serverless` directory.
2. Go to the bucket's permission settings and add a new IAM permission.
   1. Principal: `SERVICE_ACCOUNT_ID` (the id of the service account created in step 1). 
   2. Role: `Storage Object Admin`. 

Repeat step 2 for all buckets (dev, testing, prod). 

## Cloud Function 

There isn't really any setup required for the cloud function. It's implementation already 
exists, and the methodology for deploying / re-deploying the function when it's implementation 
changes will be covered in a separate development document. 
