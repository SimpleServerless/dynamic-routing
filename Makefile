## Makefile for simple serverless routing service.

# Before running STAGE needs to be exported for the shell ex: 'export STAGE=dev'

FUNCTION=dynamic-serverless-routing
DESCRIPTION="Simple serverless service to demonstrate dynamic routing"
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


clean:
	@echo 'Removing crap'
	rm -rf dist
	rm -rf .aws-sam
	rm -rf .pytest_cache
	rm -rf tests/.pytest_cache
	rm -rf src/__pycache__
	rm -rf tests/integration/__pycache__


build: clean
	cp -R src dist
	# Lambda requires linux x86. This will make sure the dependencies target that instead of the local architecture.
	pip install --no-deps --platform manylinux1_x86_64 -r src/requirements.txt -t dist/


# Example for deploying with CDK instead of SAM
deploy: build
	cdk deploy --require-approval never


synth:
	cdk synth


# May need to be run one time if deploy gets the error "This stack uses assets, so the toolkit stack must be deployed"
bootstrap:
	cdk bootstrap aws://$(AWS_ACCOUNT)/$(REGION)


package: build
	@if test -z "$(STAGE)"; then echo "****** STAGE not set. Set STAGE with: export STAGE=env ******"; exit 1; fi
	sam package \
	--s3-bucket $(S3_BUCKET) \
	--output-template-file "package.$(STAGE).yaml"


invoke:
	aws lambda invoke --invocation-type RequestResponse --function-name $(FUNCTION)-$(STAGE) --payload '{"route": "list_students", "args": {}}' --cli-binary-format raw-in-base64-out /dev/stdout


# Run a custom event locally and see it's entire output. Good for iterating fast on your local machine.
run-local:
	python3 tests/run_local.py LIST_STUDENTS


tail:
	aws logs tail --follow --format short /aws/lambda/$(FUNCTION)-$(STAGE)


.PHONY : package