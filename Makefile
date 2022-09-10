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

# define my_func
# 	echo "Doing some stuff"
# 	echo "${HELLO}"
# endef

# cm%: HELLO = heyyyy
# cmd: 
# 	$(call my_func);
# cd: 
# 	$(call my_func);

local-bucket: 
	@yarn emulate

# Re-runs make-test api on any changes to source code directory. This allows 
# developers to make changes in the source code directory, and each time a 
# change is detected, the serverless code is rebuilt, and functions-framework
# is re-launched. Ngl I kinda popped off on this one. 
.PHONY: test-api-debug
test-api-debug: 
	@nodemon --watch src_py --exec "make test-api" -e py,ipynb --verbose

# Builds serverless code, launches funtions framework from the 
# bulid directory for local api testing. 
.PHONY: test-api
test-api: build-api-quiet
	@echo "------------------------------------------------------------------------"
	@echo "Launching api in dev mode from ${PATH_SERVERLESS_CODE_DEPLOY}" 
	@echo "------------------------------------------------------------------------"
	@cd $(PATH_SERVERLESS_CODE_DEPLOY); \
	functions-framework --target=bean_analytics_recalculate_chart

# Builds serverless code bundle that will be deployed to google cloud functions 
.PHONY: build-api 
build-api: 
	@echo "------------------------------------------------------------------------"
	@echo "Creating serverless code bundle" 
	@echo "------------------------------------------------------------------------"
	@python scripts/create_serverless_code.py 
	@echo "------------------------------------------------------------------------"
	@echo "Showing generated directory structure" 
	@echo "------------------------------------------------------------------------"
	@python scripts/tree.py --path $(PATH_SERVERLESS_CODE_DEPLOY)

# Does the same thing as build but produces no text output 
.PHONY: build-api-quiet
build-api-quiet: 
	@python scripts/create_serverless_code.py --quiet 

