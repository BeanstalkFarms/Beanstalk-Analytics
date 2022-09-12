# https://unix.stackexchange.com/questions/235223/makefile-include-env-file
include .env
export

# ENVIRONMENT VARIABLES 
# -----------------------------------------------------------------------------------------------

SERVERLESS_HANDLER=bean_analytics_http_handler
# Directory where we keep code deployed to google cloud function (our serverless backend)
PATH_SERVERLESS_CODE_DEPLOY=.build/serverless
# Directory where we keep code that serves as base for code deployed to google cloud function 
# This directory contains additional code and data that we don't want to deploy so that's 
# why it is separate from PATH_SERVERLESS_CODE_DEPLOY
PATH_SERVERLESS_CODE_DEV=serverless
# Directory where production notebooks exist (within the deployed code bundle).
# Note: This path is relative to the root PATH_SERVERLESS_CODE_DEPLOY
PATH_NOTEBOOKS=notebooks/prod
# This tells the GCP storage client to connect to a different endpoint than 
# for production buckets. Useful to avoid reading from / writing to buckets in testing. 
# Not a well documented feature within the API but here's the PR that added in the feature
# https://github.com/googleapis/google-cloud-python/pull/9219
STORAGE_EMULATOR_HOST_NAME=localhost
STORAGE_EMULATOR_PORT=9023
STORAGE_EMULATOR_HOST_LOCAL=http://$(STORAGE_EMULATOR_HOST_NAME):$(STORAGE_EMULATOR_PORT)

# -----------------------------------------------------------------------------------------------
# RULES
# -----------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------------
# RULES - FRONTEND 
# -----------------------------------------------------------------------------------------------
.PHONY: frontend-dev-bucket-local
frontend-dev-bucket-local: NEXT_PUBLIC_CDN=STORAGE_EMULATOR_HOST_LOCAL
frontend-dev-bucket-local: 
	@yarn dev 

.PHONY: frontend-dev-bucket-gcp
frontend-dev-bucket-gcp: NEXT_PUBLIC_CDN=https://storage.googleapis.com
frontend-dev-bucket-gcp: 
	@yarn dev 

.PHONY: frontend-start
frontend-start: 
	@yarn start 

.PHONY: frontend-build
frontend-build: 
	@yarn build 

# -----------------------------------------------------------------------------------------------
# RULES - BACKEND 
# -----------------------------------------------------------------------------------------------

# RULES - BACKEND - Builds 
# -----------------------------------------------------------------------------------------------

# Builds serverless code bundle that gets deployed to google cloud functions. 
# This code bundle is also used when running api locally. 
define run_build_api
	chmod +x ./scripts/shell/build-api.sh; \
		scripts/shell/build-api.sh; 
endef 

# Builds serverless code bundle with verbose output 
.PHONY: build-api 
build-api: BUILD_API_VERBOSE=true
build-api: 
	@$(call run_build_api)
	
# Builds serverless code bundle with no output 
.PHONY: build-api-quiet
build-api-quiet: BUILD_API_VERBOSE=false
build-api-quiet: 
	@$(call run_build_api)

# RULES - BACKEND - Local Api Development 
# -----------------------------------------------------------------------------------------------

# Runs the google storage bucket emulator process. This command should 
# be run when testing the application with a local backend. 
.PHONY: local-bucket
local-bucket: 
	@python "${PATH_SERVERLESS_CODE_DEV}/tests/emulate_storage.py"

# Deploys google cloud function locally for testing. 
# If env variable STORAGE_EMULATOR_HOST is set we use a local backend storage emulator. 
# If env variable STORAGE_EMULATOR_HOST is not set we use a GCP bucket as the backend. 
define run_local_api
	chmod +x ./scripts/shell/test-api.sh; \
		scripts/shell/test-api.sh; 
endef 

# Run google cloud function locally for testing with local backend. 
# Note: Run `make local-bucket` prior to executing this command. 
# 		This is required so that you can view the logs for the local emulator. 
.PHONY: api-local-bucket-local
api-local-bucket-local: STORAGE_EMULATOR_HOST=$(STORAGE_EMULATOR_HOST_LOCAL)
api-local-bucket-local: build-api-quiet
	@$(call run_local_api)

# Run google cloud function locally for testing with gcp backend. 
.PHONY: api-local-bucket-gcp
api-local-bucket-gcp: build-api-quiet
	@$(call run_local_api)

# Executes nodemon to watch source directory for changes. Each time a change 
# is detected in one the source files, we run a make command that 
# 1. Re-builds the serverless code bundle 
# 2. Re-launches the local serverless development stack.
# TODO: Figure out if there is any teardown that needs to be performed by nodemomn 
define run_nodemon
	nodemon --watch "${PATH_SERVERLESS_CODE_DEV}" \
		--exec "make $(1)" \ 
		-e py,ipynb \
		--verbose
endef 

# Local debugging of cloud function with local backend. 
.PHONY: debug-api-local-bucket-local
debug-api-local-bucket-local: build-api-quiet
	@$(call run_nodemon, "api-local-bucket-local")

# Local debugging of cloud function with gcp backend. 
.PHONY: debug-api-local-bucket-gcp
debug-api-local-bucket-gcp: build-api-quiet
	@$(call run_nodemon, "api-local-bucket-gcp")


# RULES - BACKEND - Local Api Unit Testing 
# -----------------------------------------------------------------------------------------------

.PHONY: unit-test-api-local
unit-test-api-local: STORAGE_EMULATOR_HOST=$(STORAGE_EMULATOR_HOST_LOCAL)
unit-test-api-local: PATH_NOTEBOOKS=notebooks/testing
unit-test-api-local: build-api-quiet
# Note: tests must be run within the source directory, not the 
# build directory due to how the tests import dependencies. 
# However, the tests use a simulated local deployment of the 
# cloud function sourced from the build directory, to ensure 
# that the build process operates as expected. 
	@pytest "${PATH_SERVERLESS_CODE_DEV}/tests/test_api_local.py" \
		#  --log-cli-level DEBUG \ # uncomment when debugging tests 
		 -s -vvv
	@rmdir .cloudstorage # used by emulator for local data storage 

# RULES - BACKEND - Api Deployment 
# -----------------------------------------------------------------------------------------------

.PHONY: deploy-api
deploy-api: GCLOUD_ENV_FILE=.env.yml
deploy-api: build-api 
# TODO: What is the right amount of memory for the cloud function? 
	@echo "Creating temporary environment file ${GCLOUD_ENV_FILE}"
	@python scripts/python/create_gcloud_env_file.py \
		--file $(GCLOUD_ENV_FILE) \
		--env-vars \
			GOOGLE_APPLICATION_CREDENTIALS \
			NEXT_PUBLIC_STORAGE_BUCKET_NAME \
			PATH_NOTEBOOKS \
			SUBGRAPH_URL; 
	gcloud functions deploy $(SERVERLESS_HANDLER) \
		--region=us-east1 \
		--runtime=python310 \
		--memory=1024MB \
		--source=$(PATH_SERVERLESS_CODE_DEPLOY) \
		--entry-point=$(SERVERLESS_HANDLER) \
		--env-vars-file=$(GCLOUD_ENV_FILE) \
		--trigger-http \
		--allow-unauthenticated
	@echo "Removing temporary environment file ${GCLOUD_ENV_FILE}"
	@rm $(GCLOUD_ENV_FILE)
