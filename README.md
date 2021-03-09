# Dynamic Routing: Lesson 2
This repo is a companion to **Lesson 2** in the "Simple Serverless" series and future lessons will build on the tools and patterns used here.
I hope you find something here helpful, and please give this repo a star if you do. Thanks for checking it out.

This repo builds on the patterns used in [Simple Routing: Lesson 1](https://github.com/SimpleServerless/simple-routing) 
that uses decorators to map REST and GrqphQL endpoints to functions in lambdas but also leverages CDK to scan the lambda
for decorators and automatically generate API Gateway (REST) or AppSync (GraphQL) endpoints during deployment.

You can use CDK and the included `app.py` file to deploy a fully functional API to AWS. 
I was careful to favor resources that are only "pay for what you use" so there should be little or no reoccurring costs for this deployment.

I also use this repo as a toolbox of tricks I've learned over the years to make developing lambdas fast and easy. 

You will find in this repo:
- A single CDK file (app.py) that will scan lambda_function.py for decorators ex: `@router.rest("GET", "/students")` and automatically generate API Gateway (REST) or AppSync (GraphQL) endpoints.
- All the infrastructure as code needed to deploy fully functional APIs via SAM which is an AWS extension of CloudFormation
- A simple script (`run_local.py`) that makes it easy to iterate and debug locally
- Commands to invoke a deployed lambda and tail its logs in realtime (`make invoke`, `make tail`)


# Example

### Rest

```
@router.rest("GET", "/students")
def list_students(args: dict) -> dict:
    ...
    return student_list
```
Generates the CloudFormation equivalent:
```
  RestListStudentsRoute:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      RouteKey: "GET /students"
      ApiId: !Ref APIGateway
      Target: !Sub 'integrations/my-integration'
```

### GraphQL
```
@router.graphql("Query", "listStudents")
def list_students(args: dict) -> dict:
    ...
    return student_list
```
Generates the CloudFormation equivalent:
```
getStudentsResolver:
    Type: AWS::AppSync::Resolver
    Properties:
      ApiId: my-appsync-id
      FieldName: listStudents
      TypeName: Query
      DataSourceName: my-lambda-data-source
```

# Requirements

- Python 3.8
- Pip 3
- AWS CLI: [Install](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- CDK: [Getting started with CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)
- make
- An S3 Bucket for uploading the lambda deployments as defined in the `S3_BUCKET` variable in the make file.
- An AWS account with permissions to deploy Lambda, API Gateway, AppSync 
and other resources they depend on.
- A shell configured with your AWS credentials AWS_DEFAULT_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY... 
  [docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)


# Deploy
```
git clone git@github.com:SimpleServerless/dynamic-routing.git
cd dynamic-routing
make deploy
```

# What if I only want REST or GraphQL not both?
Nothing will break if you do or do not include a decorator for REST or GrqphQL in lambda_function.py, so feel free to delete the 
decorators you don't want to use.
If you want to go a step further you can remove all reverences to Api Gateway or AppSync from the app.py file.


# Files Explanation

**app.py:** All the infrastructure as code needed to deploy this project to AWS. This file contains the code that does 
the actual dynamic generation of endpoints based on the decorators found in lambda_function

**Makefile:** Make targets for deploying, testing and iterating. See [Make Targets](#make-targets) for more information.

**run_local.py:** Helper script for testing and iterating locally in a shell or IDE. 
You can run this script in an IDE to execute lambda_function.handler locally, set break points...

**/src**

&nbsp;&nbsp;&nbsp;&nbsp;**lambda_function.py:** Contains the lambda handler and all CRUD or business logic functions the endpoints are routed to.

&nbsp;&nbsp;&nbsp;&nbsp;**requirements.txt:** Contains a list of any dependancies that needs to be included in the deploy.

&nbsp;&nbsp;&nbsp;&nbsp;**schema.graphql:** GraphQL schema only used if grqphQL routes are declared

&nbsp;&nbsp;&nbsp;&nbsp;**utils.py:** Contains supporting functions for lambda_handler.py




# Make Targets
**clean:** Removes artifacts that are created by testing and deploying

**build:** Uses src/requirements.txt to prepare target appropriate (manylinux1_x86_64) dependencies for deployment

**deploy:** Uses CDK and `app.py` to deploy the function and supporting infrastructure to AWS.

**synth:** Uses CDK and `app.py` to generate and output a CloudFormation template that represents the deployment. This can be
useful for iterating on changes to `app.py` without waiting for an actual deploy to see if it's valid.

**invoke:** Uses the AWS CLI to invoke the deployed function.

**run-local:** Uses run_local.py to execute the handler locally. This target demonstrates
how run_local.py can be used as a wrapper to run and debug the function in a shell or from an IDE.

**tail:** Uses the AWS CLI to tail the logs of the deployed function in realtime.



# Iterate in a local environment
You'll need to have your AWS credentials set up in your shell to access AWS resources like SecretsManager. [docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)

The `run_local` make target demonstrates how to use the run_local.py script to iterate locally, or as something you can 
run in an IDE allowing you so set breakpoints and debug. 
