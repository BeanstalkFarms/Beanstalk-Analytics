# https://unix.stackexchange.com/questions/235223/makefile-include-env-file
include .env
export

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
_STORAGE_EMULATOR_HOST=http://localhost:9023


# local-bucket: 
# 	@yarn emulate

# test api local bucket 
# test api gcp bucket 
# test api local bucket (+nodemon)
# test api gcp bucket (+nodemon)


# Re-runs make-test api on any changes to source code directory. This allows 
# developers to make changes in the source code directory, and each time a 
# change is detected, the serverless code is rebuilt, and functions-framework
# is re-launched. Ngl I kinda popped off on this one. 
.PHONY: test-api-debug
test-api-debug: 
	@nodemon --watch src_py --exec "make test-api" -e py,ipynb --verbose

# Builds serverless code, launches funtions framework from the 
# bulid directory for local api testing. 
test-api-bucket-loc%: STORAGE_EMULATOR_HOST=$(_STORAGE_EMULATOR_HOST)
test-api-bucket-loc%: STORAGE_EMULATOR_PORT=9023

# Builds serverless code bundle, ensures emulator host is running, 
# and starts functions framework from deployment code directory. 
.PHONY: test-api-bucket-local
test-api-bucket-local: build-api-quiet
	@chmod +x ./scripts/test-api.sh 
	@scripts/test-api.sh

# Builds serverless code bundle, ensures emulator host is NOT running, 
# and starts functions framework from deployment code directory. 
.PHONY: test-api-bucket-gcp
test-api-bucket-gcp: build-api-quiet
	@chmod +x ./scripts/test-api.sh 
	@scripts/test-api.sh 

# Builds serverless code bundle that gets deployed to google cloud functions 
# verbose textual output
.PHONY: build-api 
build-api: 
	@chmod +x ./scripts/build-api.sh 
	@scripts/build-api.sh 
	
# Builds serverless code bundle that gets deployed to google cloud functions 
# limited textual output
.PHONY: build-api-quiet
build-api-quiet: 
	@chmod +x ./scripts/build-api.sh 
	@scripts/build-api.sh false 
	

