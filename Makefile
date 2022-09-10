# https://unix.stackexchange.com/questions/235223/makefile-include-env-file
include .env
export

# MAKEFILE ENVIRONMENT VARIABLES 
# -----------------------------------------------------------------------------------------------

# Directory where we keep code deployed to google cloud function (our serverless backend)
PATH_SERVERLESS_CODE_DEPLOY=serverless
# Directory where we keep code that serves as base for code deployed to google cloud function 
# This directory contains additional code and data that we don't want to deploy so that's 
# why it is separate from PATH_SERVERLESS_CODE_DEPLOY
PATH_SERVERLESS_CODE_DEV=src_py
# Directory where production notebooks exist (within the deployed code bundle).
# Note: This path is relative to the root PATH_SERVERLESS_CODE_DEPLOY
PATH_NOTEBOOKS=notebooks/prod
# This tells the GCP storage client to connect to a different endpoint than 
# for production buckets. Useful to avoid reading from / writing to buckets in testing. 
# Not a well documented feature within the API but here's the PR that added in the feature
# https://github.com/googleapis/google-cloud-python/pull/9219
STORAGE_EMULATOR_HOST_NAME=localhost
STORAGE_EMULATOR_PORT=9023
STORAGE_EMULATOR_HOST_LOCAL="http://$(STORAGE_EMULATOR_HOST_NAME):$(STORAGE_EMULATOR_PORT)"

# RULES - FRONTEND  
# Wrappers around `yarn run` with environment configuration. 
# -----------------------------------------------------------------------------------------------

frontend-dev-bucket-lo%: NEXT_PUBLIC_CDN=STORAGE_EMULATOR_HOST_LOCAL
frontend-dev-bucket-gc%: NEXT_PUBLIC_CDN=https://storage.googleapis.com

.PHONY: frontend-dev-bucket-local
frontend-dev-bucket-local: 
	@yarn dev 

.PHONY: frontend-dev-bucket-gcp
frontend-dev-bucket-gcp: 
	@yarn dev 

.PHONY: frontend-start
frontend-start: 
	@yarn start 

.PHONY: frontend-build
frontend-build: 
	@yarn build 

# RULES - BACKEND 
# -----------------------------------------------------------------------------------------------

# Runs the google storage bucket emulator process. This command 
# should be run prior to testing the api locally with a local backend.
.PHONY: local-bucket
local-bucket: 
	@python scripts/python/emulate_storage.py

# Executes nodemon to watch src_py for changes. Each time a change 
# is detected in one the source files, we run a make command that 
# 1. Re-builds the serverless code bundle 
# 2. Re-launches the local serverless development stack.
# TODO: Figure out if there is any teardown that needs to be performed by nodemomn 
define run_nodemon
	nodemon --watch src_py \
		--exec "make $(1)" \ 
		-e py,ipynb \
		--verbose
endef 

# Local debugging of cloud function with local backend. 
.PHONY: debug-api-bucket-local
debug-api-bucket-local: build-api-quiet
	@$(call run_nodemon, "test-api-bucket-local")

# Local debugging of cloud function with gcp backend. 
.PHONY: debug-api-bucket-gcp
debug-api-bucket-gcp: build-api-quiet
	@$(call run_nodemon, "test-api-bucket-gcp")

# Deploys google cloud function locally for testing. 
# If env variable STORAGE_EMULATOR_HOST is set we use a local backend storage emulator. 
# If env variable STORAGE_EMULATOR_HOST is not set we use a GCP bucket as the backend. 
define run_test_api
	chmod +x ./scripts/shell/test-api.sh; \
		scripts/shell/test-api.sh; 
endef 

test-api-bucket-loc%: STORAGE_EMULATOR_HOST=$(STORAGE_EMULATOR_HOST_LOCAL)

# Deploy google cloud function locally for testing with local backend. 
.PHONY: test-api-bucket-local
test-api-bucket-local: build-api-quiet
	@$(call run_test_api)

# Deploy google cloud function locally for testing with gcp backend. 
.PHONY: test-api-bucket-gcp
test-api-bucket-gcp: build-api-quiet
	@$(call run_test_api)

# Builds serverless code bundle that gets deployed to 
# google cloud functions. This code bundle is also used 
# for local testing. 
# $1: bool = flag for verbose output 
define run_build_api
	chmod +x ./scripts/shell/build-api.sh; \
		scripts/shell/build-api.sh "$(1)"; 
endef 

# Builds serverless code bundle with verbose output 
.PHONY: build-api 
build-api: 
	@$(call run_build_api, "true")
	
# Builds serverless code bundle with no output 
.PHONY: build-api-quiet
build-api-quiet: 
	@$(call run_build_api, "false")
