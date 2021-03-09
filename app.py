import os
import sys

import aws_cdk.core as core
import aws_cdk.aws_appsync as appsync
import aws_cdk.aws_lambda as aws_lambda
import aws_cdk.aws_iam as iam
import aws_cdk.aws_apigatewayv2 as apigatewayv2
import aws_cdk.aws_apigatewayv2_integrations as apigatewayv2_integrations

import boto3

# Import the lambda function to scan for routes
sys.path.append(os.getcwd() + "/src")
import lambda_function

stage = os.environ['STAGE']
service_name = os.environ['FUNCTION']
region = os.environ['AWS_DEFAULT_REGION']
stack_name = f"{service_name}-{region}-{stage}"


class CdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        account = self.account

        print("")
        print(f"   Service: {service_name}")
        print(f"   Region:  {region}")
        print(f"   Stage:   {stage}")
        print(f"   Account: {account}")
        print(f"   Stack:   {stack_name}")
        print("")

        ssm = boto3.client('ssm')

        # Environment variable mapping
        environment: dict = {'dev': {
                                     'logLevel': 'DEBUG',
                                     'dbHost': 'simple-serverless-aurora-serverless-development.cluster-cw3bjgnjhzxa.us-east-2.rds.amazonaws.com',
                                     'dbName': 'simple_serverless_dev',
                                     'vpcId': 'vpc-319daa58'
                                     },
                             'prod': {
                                      'logLevel': 'INFO',
                                      'dbHost': 'simple-serverless-aurora-serverless-production.cluster-cw3bjgnjhzxa.us-east-2.rds.amazonaws.com',
                                      'dbName': 'simple_serverless_prod',
                                      'vpcId': 'vpc-XXXXXX'
                                      }
                             }

        env_variables = {
            'STAGE': stage,
            "LOG_LEVEL": environment[stage]['logLevel']
        }

        # Create the main lambda function
        service_lambda = aws_lambda.Function(self,
                                             'LambdaFunction',
                                             runtime=aws_lambda.Runtime.PYTHON_3_8,
                                             description=service_name,
                                             code=aws_lambda.AssetCode("./dist"),
                                             function_name=service_name + "-" + stage,
                                             timeout=core.Duration.seconds(35),
                                             tracing=aws_lambda.Tracing.ACTIVE,
                                             memory_size=128,
                                             handler='lambda_function.handler',
                                             environment=env_variables)

        #
        # REST (API Gateway HTTP) stuff starts here
        #

        # How to: Import an existing HTTP API Gateway instance
        # http_api = apigatewayv2.HttpApi.from_api_id(self, id='APIGateway', http_api_id='0fdl9wlxw4')

        # How to: Create a new HTTP API Gateway instance
        http_api = apigatewayv2.HttpApi(
            self, 'APIGateway',
            api_name=f'{service_name}-api-{stage}'
        )

        integration = apigatewayv2_integrations.LambdaProxyIntegration(
            handler=service_lambda,
            payload_format_version=apigatewayv2.PayloadFormatVersion.VERSION_2_0
        )

        # How to: auto generate REST endpoints from decorators ex: @router.rest("GET", "/students").
        for route_key, endpoint in lambda_function.router.get_rest_endpoints().items():
            print(f"Creating REST endpoint for {route_key}")
            http_api.add_routes(
                path=endpoint['path'],
                methods=[apigatewayv2.HttpMethod(endpoint['method'])],
                integration=integration
            )

        #
        # Graphql (AppSync) stuff starts here
        #
        policy = iam.PolicyStatement(actions=['lambda:InvokeFunction'],
                                     resources=[service_lambda.function_arn])
        principal = iam.ServicePrincipal('appsync.amazonaws.com')
        service_role = iam.Role(self, 'service-role', assumed_by=principal)
        service_role.add_to_policy(policy)

        # How to: import an existing AppSync instance
        # graphql_api = appsync.GraphqlApi.from_graphql_api_attributes(self, 'GraphQLApi', graphql_api_id='phw4kdabqnbjzi4czy3dtbmynu')

        graphql_schema = appsync.Schema(file_path='./src/schema.graphql')
        graphql_auth_mode = appsync.AuthorizationMode(authorization_type=appsync.AuthorizationType.API_KEY)
        graphql_auth_config = appsync.AuthorizationConfig(default_authorization=graphql_auth_mode)

        graphql_api = appsync.GraphqlApi(
            self, 'GraphQLApi',
            name=f'{service_name}-api-' + stage,
            authorization_config=graphql_auth_config,
            schema=graphql_schema
        )

        datasource_name = to_camel(service_name) + "Lambda"
        lambda_data_source = appsync.LambdaDataSource(
            self, 'LambdaDataSource',
            api=graphql_api,
            name=datasource_name,
            lambda_function=service_lambda,
            service_role=service_role
        )

        # How to: auto generate GraphQL resolvers from decorators ex: @router.graphql("Query", "listStudents").
        for field_name, graphql_def in lambda_function.router.get_graphql_endpoints().items():
            print(f"Creating graphql {graphql_def['parent']} for {field_name}")
            appsync.Resolver(
                self, field_name + "Resolver",
                api=graphql_api,
                type_name=graphql_def['parent'],
                field_name=field_name,
                data_source=lambda_data_source
            )


        core.CfnOutput(self, "RestAPIUrlOutput",
                       value=http_api.url,
                       export_name=f"{stack_name}-RestApiUrl-{stage}")

        core.CfnOutput(self, "GraphQLApiIdOutput",
                       value=graphql_api.api_id,
                       export_name=f"{stack_name}-GraphqlApiId-{stage}")

        core.CfnOutput(self, "GraphQLUrlOutput",
                       value=graphql_api.graphql_url,
                       export_name=f"{stack_name}-GraphqlUrl-{stage}")

        core.CfnOutput(self, "GraphQLApiKeyOutput",
                       value=graphql_api.api_key,
                       export_name=f"{stack_name}-GraphQLApiKey-{stage}")


# Sometimes AWS lets you use '-' ex: service-name and sometimes you have to or want to use camel case ex: serviceName.
# This saves me from having to create two sets of parameters
def to_camel(name):
    components = name.split('-')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return ''.join(x.title() for x in components)


# Code to execute stack below
app = core.App()

# NOTE! ~/.aws/config will override the CDK_DEFAULT_ACCOUNT value no matter what you set it to in your environment variables
account = os.environ['AWS_ACCOUNT']
region = os.environ['AWS_DEFAULT_REGION']

CdkStack(app, f"{service_name}-us-east2-dev", env={"account": account, "region": region})

app.synth()

# Possibly cleaner idea to define mulitple enviroments
# https://taimos.de/blog/deploying-your-cdk-app-to-different-stages-and-environments