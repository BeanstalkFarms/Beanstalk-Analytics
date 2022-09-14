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
  function. 

## Contributor Documentation 

These links are for developers who wish to contribute new charts to the 
analytics website. 

TODO: Fill in some documentation on this topic. 

## Developer Documentation 

These links are for developers working on the full-stack application.

Right now, this really just for **TBIQ**. 

- [Google Cloud Platform Infrastructure](./docs/setup-cloud-infra.md)
- [Application Development](./docs/dev.md)
- [Application Testing](./docs/testing.md)
- [Application Deployment](./docs/deploy.md)