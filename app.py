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

# CloudFormation and SAM is preferred especially if you are new to AWS, CloudFormation, CDK, or Serverless
# This file represents an example of how to do most of what can be found in template.yaml wiht CDK
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

        datasource_name = to_camel(service_name) + "Lambda"

        ssm = boto3.client('ssm')

        # Environment variable mapping
        environment: dict = {'dev': {'logLevel': 'DEBUG',
                                     'dbHost': 'simple-serverless-aurora-serverless-development.cluster-cw3bjgnjhzxa.us-east-2.rds.amazonaws.com',
                                     'dbName': 'simple_serverless_service_dev',
                                     'apiId': 'XXXXXXXX'
                                     }
                             }

        # Retrieve an existing VPC instance.
        vpc = ec2.Vpc.from_lookup(self, 'VPC', vpc_id=environment[stage]['vpcId'])

        env_variables = {
            'STAGE': stage,
            "PGHOST": environment[stage]['dbHost'],
            "PGPORT": "5432",
            "PGDATABASE": environment[stage]['dbName'],
            "LOG_LEVEL": environment[stage]['logLevel']
        }

        app_security_group_id = core.Fn.import_value(f"simple-serverless-database-us-east-2-{stage}-AppSGId")
        app_security_group = ec2.SecurityGroup.from_security_group_id(self, "AppSecurityGroup", app_security_group_id)

        # Layer for adding Insights extension
        insights_layer = aws_lambda.LayerVersion.from_layer_version_arn(self, "InsightsLayer",
                                                                        f"arn:aws:lambda:{self.region}:580247275435:layer:LambdaInsightsExtension:2")


        # Create the main lambda function
        service_lambda = aws_lambda.Function(self,
                                             'LambdaFunction',
                                             runtime=aws_lambda.Runtime.PYTHON_3_8,
                                             description=service_name,
                                             code=aws_lambda.AssetCode("./dist"),
                                             function_name=service_name + "-" + stage,
                                             timeout=core.Duration.seconds(45),
                                             tracing=aws_lambda.Tracing.ACTIVE,
                                             memory_size=256,
                                             handler='lambda_function.handler',
                                             vpc=vpc,
                                             security_groups=[app_security_group],
                                             environment=env_variables)

        # Add SecretsManager permissions to lambda
        service_lambda.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue", "secretsmanager:List*"],
            resources=[f"arn:aws:secretsmanager:{region}:{account}:secret:simple-serverless-service/*"]))

        # Create a version and some Aliases used for promotion
        lambda_version = service_lambda.add_version('LambdaVersion')
        aws_lambda.Alias(self, 'LambdaAlias', alias_name='live', version=lambda_version)
        aws_lambda.Alias(self, 'LambdaVerifiedAlias', alias_name='verified', version=lambda_version)

        # API endpoint configuration starts here
        policy = iam.PolicyStatement(actions=['lambda:InvokeFunction'],
                                     resources=[service_lambda.function_arn + ":live"])
        principal = iam.ServicePrincipal('appsync.amazonaws.com')
        service_role = iam.Role(self, 'service-role', assumed_by=principal)
        service_role.add_to_policy(policy)

        # Create an AppSync data source for GraphQL
        lambda_data_source = appsync.CfnDataSource(
            self, 'LambdaDataSource',
            api_id='XXXXX',
            name=datasource_name,
            type='AWS_LAMBDA',
            lambda_config=appsync.CfnDataSource.LambdaConfigProperty(
                lambda_function_arn=service_lambda.function_arn + ":live"),
            service_role_arn=service_role.role_arn
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


        # Do slick ass auto generation of GraphQL resolvers routes.
        for field_name in lambda_function.router.get_graphql_endpoints().keys():
            print("Creating graphql query for " + field_name)
            graphql_def = lambda_function.router.get_graphql_endpoints()[field_name]

            # Nested GraphQL queries likely have additional arguments that need
            # to be passed, typically ids (i.e. student_id)
            id_field = graphql_def.get('id_field', '')
            id_field_put = ""
            # Set id_field_put string to id_field(s) to append to request
            # mapping template below
            if id_field:
                if type(id_field) == list:
                    for field in id_field:
                        id_field_put += f"$!{{args.put(\"{field}\", $context.source.{field})}}\n"
                elif type(id_field) == str:
                    id_field_put = f"$!{{args.put(\"{id_field}\", $context.source.{id_field})}}\n"

            request_mapping_template = """
                        #set( $args = {} )
                        $!{args.putAll($context.args)}
                        %s
                        {
                          "version": "2017-02-28",
                          "operation": "Invoke",
                          "payload": {
                               "fieldName": "$context.info.fieldName",
                               "args": $util.toJson($args)
                            }
                        }
                    """ % id_field_put

            resolver = appsync.CfnResolver(
                self, field_name + "Resolver",
                api_id=environment[stage]['apiId'],
                type_name=graphql_def['parent'],
                field_name=field_name,
                data_source_name=lambda_data_source.name,
                request_mapping_template=request_mapping_template,
                response_mapping_template="$util.toJson($ctx.result)"
            )

            resolver.add_depends_on(lambda_data_source)




def to_camel(name):
    components = name.split('-')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return ''.join(x.title() for x in components)

app = core.App()

# NOTE! ~/.aws/config will override the CDK_DEFAULT_ACCOUNT value no matter what you set it to in your environment
account = os.environ['AWS_ACCOUNT']
region = os.environ['AWS_DEFAULT_REGION']

CdkStack(app, "dynamic-routing-us-east2-dev", env={"account": account, "region": region})

app.synth()

# Possibly cleaner idea to define mulitple enviroments
# https://taimos.de/blog/deploying-your-cdk-app-to-different-stages-and-environments