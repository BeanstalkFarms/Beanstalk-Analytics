<img src="public/bean-logo-circled.svg" alt="Beanstalk logo" align="right" width="120" />

## Beanstalk-Data-Playground

[![Discord][discord-badge]][discord-url]

[discord-badge]: https://img.shields.io/discord/880413392916054098?label=Beanstalk
[discord-url]: https://discord.gg/beanstalk

**Beanstalk analytics and protocol metrics: [analytics.bean.money](https://analytics.bean.money)**

## Getting started

Install Python dependencies with `pipenv`:

```
pipenv install
# Or: python3 -m pipenv install
```

Install Next.js dependencies:

```
yarn
```

Setup local environment:

1. `cp .env.example .env`
2. If using an emulator for development, set `NEXT_PUBLIC_CDN` and `STORAGE_EMULATOR_HOST` to point to a local Cloud Storage emulator. A simple proxy is provided via `yarn emulate`, see `test/emulate.py` for more.
3. If testing uploads to a live Cloud Storage bucket: set `NEXT_PUBLIC_STORAGE_BUCKET_NAME` and `GOOGLE_APPLICATION_CREDENTIALS`. You'll need to create a bucket which allows public and a service account with permission to upload files, see below.


Run the local development environment:

```
yarn dev     # Runs the frontend at localhost:3000
yarn emulate # Runs the gcloud emulator at localhost:9023
```

## Setting up a test bucket

1. Set up a Google Cloud account.
2. Create a new project.
3. Create a storage bucket. Uncheck the option that prevents the bucket from being exposed to publicly.
4. Add a role for `allUsers` that enables viewing objects.
5. Create a service account with permissions to upload to the bucket:
  a. Create a service account.
  b. Add a key to the service account and save it locally.
  c. On the Bucket, give the service account permission to create and update objects.
  d. Update environment config to point `GOOGLE_APPLICATION_CREDENTIALS` at the location of the locally stored service account key.
6. Use the Google Cloud Shell to set bucket CORS policy:
  a. Open Google Cloud Shell.
  b. Run `nano cors.json` amd paste in the value contained in `cors.json` in this repo.
  c. Run `gsutil cors set cors.json gs://BUCKET_NAME`.
  d. Resources on the bucket are now accessible from any origin.