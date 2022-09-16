# TODO's: 

Priorities are assigned low (1) to high (5)

Any priority 3 or greater should be completed before v1 launch. 

## Frontend

- **(4)** Figure out approach to sizing and organizing charts. 
- **(4)** Implement page based routing into the application. 
- **(3)** Integrate the following pieces of information (already available) into the chart component. 
  Not sure how I want to visualize these, maybe expose them through a tooltip or indicator of 
  some kind. 
  - status (refreshed, cached). 
  - run time (amount of time notebook that created schema took to run). 
  - timestamp (when the schema was created)

## Serverless API 

Good to go for now. 

## Charts 

- **(5)** Polish up the 5-6 existing charts so they are ready for the v1 launch. 

## Infrastructure 

- **(1)** Tear down the load balancer and CDN in my personal gcloud account that were setup for testing. 
- **(2)** Review of IAM policies and infra permissions to ensure things are secure.
  - Low priority for now but high priorty pre-launch 

## Devops 

- **(2)** Run end to end tests of all makefile commands before v1 launch. 

## Documentation 

- **(3)** Update the notion document that serves as the roadmap for charts on the website. TODO: add a link here. 

## Others 

- **(3)** Minify supply increase file (used to fill in silo emissions data missing from subgraph)
  - Currently this represents about 1/5 of the bundle size. 
- **(1)** Convert backend from running notebooks to running scripts 
  - Based on some experiments in `serverless/notebooks/dev/ntbk_vs_script_performance.ipynb` there 
  we can shave off at least 2 seconds from all notebook executions (lower bound, would have to do)
  more testing to figure out what more realistic expectation is. 
- **(1)** Move from service account key to service account impersonation. More secure. 
  - https://cloud.google.com/functions/docs/securing/function-identity
  - https://cloud.google.com/sdk/gcloud/reference/functions/deploy#--run-service-account
  - https://cloud.google.com/iam/docs/impersonating-service-accounts#attaching-to-resources
  - https://cloud.google.com/iam/docs/impersonating-service-accounts#impersonate-sa-level
  - Add `--service-account` or `--impersonate-service-account` flags to cloud 
  function deploy command?
