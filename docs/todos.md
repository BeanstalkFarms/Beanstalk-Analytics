# TODO's: 

Priorities are assigned low (1) to high (5)

Any priority **3** or greater should be completed before v1 launch. 

## Frontend

- **(4)** Modify frontend so that we organize existing set of charts into pages. 
  - Also implement header based navigation so user can switch between pages easily. 
- **(2)** Support for toggling between different subgraphs. Similar to how we do things in the frontend.

## Serverless API 

- **(3)** Fork the gcp storage emulator package, and make the changes necessary to use bypass 
  CORS issues. The work is already done here just need to setup the fork and ensure that the 
  version in requirements-dev.txt matches the fork. 

## Charts 

- **(5)** Polish up the 5-6 existing charts so they are ready for the v1 launch. 

## Infrastructure 

- **(3)** Switch from infra on my personal GCP account to infra using the BF GCP account. 
  - Deploy both prod and testing infra. 
- **(3)** Review of IAM policies and infra permissions to ensure things are secure.
- **(1)** Tear down the load balancer and CDN in my personal gcloud account that were setup for testing. 

## Devops 

- **(3)** Run end to end tests of all makefile commands before v1 launch. 
- **(3)** Fix unit / integration tests to reflect new output object structures 
  (inclusion of width paths and other metadata changed this slightly).
  
## Documentation 

- **(3)** Full documentation review for correctness. 
- **(3)** Update the notion document that serves as the roadmap for charts on the website. TODO: add a link here. 
- **(1)** Contributor facing documentation.  

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
