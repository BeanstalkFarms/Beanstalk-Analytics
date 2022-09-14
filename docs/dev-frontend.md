

### Development Environment  

The local api development environment can run with two kinds of backends

1. Emulator storage bucket
2. GCP storage bucket 



frontend-dev-bucket-local



Setup local environment:

1. `cp .env.example .env`
2. If using an emulator for development, set `NEXT_PUBLIC_CDN` and `STORAGE_EMULATOR_HOST` to point to a local Cloud Storage emulator. A simple proxy is provided via `yarn emulate`, see `test/emulate.py` for more.
3. If testing uploads to a live Cloud Storage bucket: set `NEXT_PUBLIC_STORAGE_BUCKET_NAME` and `GOOGLE_APPLICATION_CREDENTIALS`. You'll need to create a bucket which allows public and a service account with permission to upload files, see below.

Run the local development environment:

```
yarn dev     # Runs the frontend at localhost:3000
yarn emulate # Runs the gcloud emulator at localhost:9023
```