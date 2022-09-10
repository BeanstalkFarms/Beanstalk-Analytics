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
_STORAGE_EMULATOR_HOST="http://$(STORAGE_EMULATOR_HOST_NAME):$(STORAGE_EMULATOR_PORT)"

# PATTERN VARIABLES (DO NOT MODIFY THESE VALUES UNLESS YOU HAVE A DAMN GOOD REASON TO)
# -----------------------------------------------------------------------------------------------

# Ensures that when running api in local dev mode with local backend, we use emulator 
test-api-bucket-loc%: STORAGE_EMULATOR_HOST=$(_STORAGE_EMULATOR_HOST)
# Suppresses build logs for quiet builds 
build-api-q%: BUILD_API_VERBOSE=false

# CANNED RECIPES 
# Rely on values set by pattern variables above 
# -----------------------------------------------------------------------------------------------

define run_test_api
	chmod +x ./scripts/test-api.sh; scripts/test-api.sh; 
endef 

define run_build_api
	if [[ "${BUILD_API_VERBOSE}" = "false" ]]; then \
		chmod +x ./scripts/build-api.sh; scripts/build-api.sh false; \
	else \
		chmod +x ./scripts/build-api.sh; scripts/build-api.sh true; \
	fi 
endef 

# RULES
# -----------------------------------------------------------------------------------------------
local-bucket: 
	@yarn emulate

# Re-runs make-test api on any changes to source code directory. This allows 
# developers to make changes in the source code directory, and each time a 
# change is detected, the serverless code is rebuilt, and functions-framework
# is re-launched. Ngl I kinda popped off on this one. 
.PHONY: test-api-debug
test-api-debug: 
# TODO: Fix the test command called here. Make a pattern variable. 
	@nodemon --watch src_py --exec "make test-api" -e py,ipynb --verbose

# Builds serverless code bundle, ensures emulator host is running, 
# and starts functions framework from deployment code directory. 
.PHONY: test-api-bucket-local
test-api-bucket-local: build-api-quiet
	@$(call run_test_api)

# Builds serverless code bundle, ensures emulator host is NOT running, 
# and starts functions framework from deployment code directory. 
.PHONY: test-api-bucket-gcp
test-api-bucket-gcp: build-api-quiet
	@$(call run_test_api)

# Builds serverless code bundle that gets deployed to google cloud functions 
# verbose textual output
.PHONY: build-api 
build-api: 
	@$(call run_build_api)
	
# Builds serverless code bundle that gets deployed to google cloud functions 
# limited textual output
.PHONY: build-api-quiet
build-api-quiet: 
	@$(call run_build_api)
