##### TODO's: 

###### High 

- Enable CORS on all buckets. 
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
