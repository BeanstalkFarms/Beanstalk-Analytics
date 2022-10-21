# TODO's: 

Priorities are assigned low (1) to high (5)

Any priority **3** or greater should be completed before v1 launch. 

## Frontend

- **(2)** Fix css styling of tooltips. Can be done through custom vegaEmbed themes but this 
  is causing an issue with re-renders that needs to be debugged. 
- **(2)** Support for toggling between different subgraphs, similar to how we do things in the frontend.

## Serverless API 

## Charts 

## Infrastructure 

- **(2)** Application security review (IAM, permissions, etc.). 

## Devops 

## Documentation 

- **(2)** Update the notion document that serves as the roadmap for charts on the website. 
- **(1)** Contributor facing documentation.  

## Others 

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
