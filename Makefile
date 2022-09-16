# Exports all environment variables from .env into makefile environment 
# https://unix.stackexchange.com/questions/235223/makefile-include-env-file
include .env
export

# ENVIRONMENT VARIABLES 
# -----------------------------------------------------------------------------------------------
# Environment variables defined in this file are public (versioned on git)
# Keep sensitive information in .env 

# Conventions 
# - Env vars beginning with PATH are paths relative to project directory. 
# - Env vars beginning with RPATH are relative paths to some parent path (parent depends). 

# STATIC FRONTEND ENVIRONMENT VARIABLES
# -----------------------------------
NEXT_PUBLIC_CHAIN_ID=1
NEXT_PUBLIC_RPC_URL=https://eth-mainnet.gateway.pokt.network/v1/5f3453978e354ab992c4da79

# STORAGE / BUCKETS 
# -----------------
# Testing bucket (used only by tests with GCP backend)
BUCKET_TEST=beanstalk-analytics-bucket-test
# Development bucket (write objects here while developing)
BUCKET_DEV=beanstalk-analytics-bucket-dev
# Production bucket (backend of production application)
BUCKET_PROD=beanstalk-analytics-bucket-prod 
# Emulator bucket (doesn't actually exist, used when running emulator)
BUCKET_EMULATOR=beanstalk-analytics-bucket-local
# Production storage host is gcloud storage 
STORAGE_HOST=https://storage.googleapis.com
# Local storage host (used for testing). Private and only set in env for certain commands 
# Not a well documented feature within the API but here's the PR that added in the feature
# https://github.com/googleapis/google-cloud-python/pull/9219
_STORAGE_EMULATOR_HOST=http://localhost:9023

# SERVERLESS API 
# --------------
# Url for the local api deployment 
LOCAL_API_URL=http://127.0.0.1:8080
# Build directory for source code bundle of google cloud function 
PATH_SERVERLESS_CODE_DEPLOY=.build/serverless
# The name of function in main.py of the build directory that is our google cloud function 
CLOUD_FUNCTION_NAME=bean_analytics_http_handler
# Directory that serves as source for serverless build. We copy contents from here to the build directory. 
PATH_SERVERLESS_CODE_DEV=serverless
# Relative path within build directory to notebooks used for unit tests 
RPATH_NOTEBOOKS_TEST=notebooks/testing
# Relative path within build directory to notebooks used for production backend 
RPATH_NOTEBOOKS_PROD=notebooks/prod
# By default, we use prod notebook path. For emulator tests, we override this value 
RPATH_NOTEBOOKS=$(RPATH_NOTEBOOKS_PROD)
# The url of the subgraph that the production notebooks will query to retrieve data 
SUBGRAPH_URL=https://graph.node.bean.money/subgraphs/name/beanstalk-testing

# -----------------------------------------------------------------------------------------------
# RULES
# -----------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------------
# RULES - FRONTEND 
# -----------------------------------------------------------------------------------------------
frontend-dev-%: NEXT_PUBLIC_API_URL=$(LOCAL_API_URL)
frontend-start-%: NEXT_PUBLIC_API_URL=$(LOCAL_API_URL)

frontend-%-bucket-local: NEXT_PUBLIC_CDN=$(_STORAGE_EMULATOR_HOST)
frontend-%-bucket-local: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_EMULATOR)

frontend-%-bucket-gcp: NEXT_PUBLIC_CDN=https://storage.googleapis.com
frontend-%-bucket-gcp: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_DEV)

.PHONY: frontend-dev-bucket-local
frontend-dev-bucket-local: 
	@yarn dev 

.PHONY: frontend-dev-bucket-gcp
frontend-dev-bucket-gcp: 
	@yarn dev 

.PHONY: frontend-start-bucket-local
frontend-start-bucket-local: 
	@yarn start 

.PHONY: frontend-start-bucket-gcp
frontend-start-bucket-gcp: 
	@yarn start 

.PHONY: frontend-build
frontend-build: NEXT_PUBLIC_CDN=https://storage.googleapis.com
frontend-build: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_PROD)
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

build-ap%: RPATH_NOTEBOOKS=$(RPATH_NOTEBOOKS_PROD)

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
local-bucket: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_EMULATOR)
local-bucket: STORAGE_EMULATOR_HOST=$(_STORAGE_EMULATOR_HOST)
local-bucket: 
	@python "serverless-tests/emulate_storage.py"

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
.PHONY: api-dev-bucket-local
api-dev-bucket-local: STORAGE_EMULATOR_HOST=$(_STORAGE_EMULATOR_HOST)
api-dev-bucket-local: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_EMULATOR)
api-dev-bucket-local: build-api-quiet
	@$(call run_local_api)

# Run google cloud function locally for testing with gcp backend. 
.PHONY: api-dev-bucket-gcp
api-dev-bucket-gcp: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_DEV)
api-dev-bucket-gcp: build-api-quiet
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
.PHONY: debug-api-dev-bucket-local
debug-api-dev-bucket-local: build-api-quiet
	@$(call run_nodemon, "api-dev-bucket-local")

# Local debugging of cloud function with gcp backend. 
.PHONY: debug-api-dev-bucket-gcp
debug-api-dev-bucket-gcp: build-api-quiet
	@$(call run_nodemon, "api-dev-bucket-gcp")


# RULES - BACKEND - Local Api Unit Testing 
# -----------------------------------------------------------------------------------------------

# Uncomment one of the target specific definitions for UNIT_TEST_API_ARGS 
# to pass different sets of arguments to the pytest commands. 
unit-test-api: UNIT_TEST_API_ARGS="-v" # Recommended pre-deployment, as this shows names of passing tests 
# unit-test-api: UNIT_TEST_API_ARGS="-v -x" # Exits on first failure
# unit-test-api: UNIT_TEST_API_ARGS="-s -vvv"
# unit-test-api: UNIT_TEST_API_ARGS="-s -vvv --log-cli-level DEBUG"

.PHONY: unit-test-api-emulator
unit-test-api-emulator: STORAGE_EMULATOR_HOST=$(_STORAGE_EMULATOR_HOST)
unit-test-api-emulator: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_EMULATOR)
unit-test-api-emulator: RPATH_NOTEBOOKS=$(PATH_SERVERLESS_CODE_DEPLOY)/$(RPATH_NOTEBOOKS_TEST)
unit-test-api-emulator: build-api-quiet
	@if [ -d ".cloudstorage " ]; then rmdir ".cloudstorage"; fi
	eval "pytest ./serverless-tests/test_api_emulator.py ${UNIT_TEST_API_ARGS}"
	@if [ -d ".cloudstorage " ]; then rmdir ".cloudstorage"; fi

.PHONY: unit-test-api-gcp
unit-test-api-gcp: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_TEST)
unit-test-api-gcp: RPATH_NOTEBOOKS=$(PATH_SERVERLESS_CODE_DEPLOY)/$(RPATH_NOTEBOOKS_PROD)
unit-test-api-gcp: build-api-quiet
	eval "pytest ./serverless-tests/test_api_gcp.py ${UNIT_TEST_API_ARGS}"

.PHONY: unit-test-api
unit-test-api: unit-test-api-emulator unit-test-api-gcp

# RULES - BACKEND - Api Deployment 
# -----------------------------------------------------------------------------------------------

.PHONY: deploy-api
deploy-api: GCLOUD_ENV_FILE=.env.yml
deploy-api: NEXT_PUBLIC_STORAGE_BUCKET_NAME=$(BUCKET_PROD)
deploy-api: build-api 
# TODO: What is the right amount of memory for the cloud function? 
# 		This is set conservatively high right now. 
	@echo "Creating temporary environment file ${GCLOUD_ENV_FILE}"
	@python scripts/python/create_gcloud_env_file.py \
		--file $(GCLOUD_ENV_FILE) \
		--env-vars \
			GOOGLE_APPLICATION_CREDENTIALS \
			NEXT_PUBLIC_STORAGE_BUCKET_NAME \
			RPATH_NOTEBOOKS \
			SUBGRAPH_URL; 
	gcloud functions deploy $(CLOUD_FUNCTION_NAME) \
		--region=us-east1 \
		--runtime=python310 \
		--memory=1024MB \
		--source=$(PATH_SERVERLESS_CODE_DEPLOY) \
		--entry-point=$(CLOUD_FUNCTION_NAME) \
		--env-vars-file=$(GCLOUD_ENV_FILE) \
		--trigger-http \
		--allow-unauthenticated
	@echo "Removing temporary environment file ${GCLOUD_ENV_FILE}"
	@rm $(GCLOUD_ENV_FILE)
