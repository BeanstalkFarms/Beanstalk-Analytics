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