# Deployment 

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
