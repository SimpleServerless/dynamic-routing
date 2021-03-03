## Makefile for simple serverless routing service.

# Before running STAGE needs to be exported for the shell ex: 'export STAGE=dev'

FUNCTION=simple-serverless-routing
DESCRIPTION="Simple serverless service to demonstrate routing"
REGION=us-east-2
AWS_PAGER=
S3_BUCKET="simple-serverless-$(STAGE)-lambda-artifacts-$(REGION)"
STACK_NAME="$(FUNCTION)-$(REGION)-$(STAGE)"
PYTHONPATH=$(shell pwd)/src

.EXPORT_ALL_VARIABLES:

print-stage:
	@echo
	@echo '***** STAGE=$(STAGE) *****'
	@echo


build:
	sam build

build-cdk: clean
	cp -R src dist
	pip install --no-deps --platform manylinux1_x86_64 -r src/requirements.txt -t dist/

# Example for deploying with CDK instead of SAM
deploy-cdk: build-cdk
	cdk deploy --require-approval never


package: build
	@if test -z "$(STAGE)"; then echo "****** STAGE not set. Set STAGE with: export STAGE=env ******"; exit 1; fi
	sam package \
	--s3-bucket $(S3_BUCKET) \
	--output-template-file "package.$(STAGE).yaml"


clean:
	@echo 'Removing crap'
	rm -rf dist
	rm -rf .aws-sam
	rm -rf .pytest_cache
	rm -rf tests/.pytest_cache
	rm -rf src/__pycache__
	rm -rf tests/integration/__pycache__


deploy: print-stage build package
	sam deploy \
	--no-fail-on-empty-changeset \
	--template-file "package.$(STAGE).yaml" \
	--stack-name $(STACK_NAME) \
	--capabilities CAPABILITY_IAM \
	--region $(REGION) \
	--parameter-overrides StageName=$(STAGE) ServiceName=$(FUNCTION)


invoke:
	aws lambda invoke --invocation-type RequestResponse --function-name $(FUNCTION)-$(STAGE) --payload '{"fieldName": "listStudents", "args": {}}' --cli-binary-format raw-in-base64-out /dev/stdout


# Run a custom event locally and see it's entire output. Good for iterating fast on your local machine.
run-local:
	python3 tests/run_local.py LIST_STUDENTS


tail:
	aws logs tail --follow --format short /aws/lambda/$(FUNCTION)-$(STAGE)


.PHONY : package