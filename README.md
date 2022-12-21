<img src="https://github.com/BeanstalkFarms/Beanstalk-Brand-Assets/blob/main/BEAN/bean-128x128.png" alt="Beanstalk logo" align="right" width="120" />

# Beanstalk Analytics

[![Discord][discord-badge]][discord-url]

[discord-badge]: https://img.shields.io/discord/880413392916054098?label=Beanstalk
[discord-url]: https://discord.gg/beanstalk

**Beanstalk analytics and protocol metrics: [analytics.bean.money](https://analytics.bean.money)**

## Application Architecture 

This application consists of

- A frontend (next.js).
  - The frontend ingests and visualizes data created by the serverless backend.
- Google Cloud Platform Infrastructure 
  - A GCP storage bucket containing vega-lite schemas and other application data.  
- A serverless api
  - Responds to frontend requests, manages objects in the storage bucket. 

## Contributor Documentation 

These links are for developers who wish to contribute new charts to the 
analytics website. 

TODO: Fill in some documentation on this topic. 

## Developer Documentation 

These links are for developers working on the full-stack application.

Right now, this really just for **TBIQ**. 

- [Google Cloud Platform Infrastructure Setup](./docs/setup-cloud-infra.md)
- [Application Development](./docs/development.md)
- [Application Deployment](./docs/deploy.md) 
