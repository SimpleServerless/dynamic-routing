import os
import sys

import aws_cdk.core as core
import aws_cdk.aws_appsync as appsync
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_lambda as aws_lambda
import aws_cdk.aws_iam as iam

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

        # How to: Retrieve an existing VPC instance.
        vpc = ec2.Vpc.from_lookup(self, 'VPC', vpc_id=environment[stage]['vpcId'])

        env_variables = {
            'STAGE': stage,
            "PGHOST": environment[stage]['dbHost'],
            "PGPORT": "5432",
            "PGDATABASE": environment[stage]['dbName'],
            "LOG_LEVEL": environment[stage]['logLevel']
        }

        # How to: Import a value exported from another stack
        app_security_group_id = core.Fn.import_value(f"simple-serverless-database-us-east-2-{stage}-AppSGId")

        # How to: Import a security group
        app_security_group = ec2.SecurityGroup.from_security_group_id(self, "AppSecurityGroup", app_security_group_id)

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
                                             vpc=vpc,
                                             security_groups=[app_security_group],
                                             environment=env_variables)

        # Add SecretsManager permissions to lambda
        service_lambda.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue", "secretsmanager:List*"],
            resources=[f"arn:aws:secretsmanager:{region}:{account}:secret:simple-serverless/*"]))

        # API endpoint configuration starts here
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
            name='dynamic-graphql-api-' + stage,
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


        #
        # Example for how to create an API gateway integration point for ReST support
        #

        # Create an API gateway integration point for ReST
        # integration = api_gateway.CfnIntegration(
        #     self, 'dynamic-routing-integration',
        #     api_id="XXXXXXXX",
        #     description='lambda integration',
        #     integration_type='AWS_PROXY',
        #     payload_format_version='1.0',
        #     integration_uri=f'arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/arn:aws:lambda:us-west-2:XXXXXXXXX:function:dynamic-routing-dev:live/invocations')

        # Do slick ass auto generation of ReST routes.
        # for endpoint in lambda_function.router.get_rest_endpoints().keys():
        #     print("Creating rest route for " + endpoint)
        #
        #     method, path = endpoint.split(' ', 1)
        #     components = path.replace('{', '').replace('}', '').split('/')
        #     name = components[0] + ''.join(x.title() for x in components[1:])
        #
        #     api_gateway.CfnRoute(self,
        #                          name + 'Route',
        #                          route_key=endpoint,
        #                          api_id="XXXXXXXX",
        #                          authorization_type='NONE',
        #                          target=f'integrations/{integration.ref}')

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

CdkStack(app, "dynamic-routing-us-east2-dev", env={"account": account, "region": region})

app.synth()

# Possibly cleaner idea to define mulitple enviroments
# https://taimos.de/blog/deploying-your-cdk-app-to-different-stages-and-environments