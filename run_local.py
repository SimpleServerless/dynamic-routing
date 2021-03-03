import logging
import json
import sys
import os
from aws_lambda_powertools.utilities.typing import LambdaContext

events = {

    "LIST_STUDENTS_DIRECT":
        """
        {
            "route": "list_students"
        }
        """,

    "LIST_STUDENTS_REST":
        """
        {
            "version": "2.0",
            "routeKey": "GET /students",
            "rawPath": "/students",
            "headers": {
              "accept": "application/json",
              "accept-encoding": "gzip, deflate, br",
              "accept-language": "en-US,en;q=0.9",
              "content-length": "0",
              "host": "test.execute-api.us-east-2.amazonaws.com"
            },
            "isBase64Encoded": false
        }
        """,

    "LIST_STUDENTS_GRAPHQL":
        """
        {
            "arguments": {},
                "request": {
                  "headers": {
                    "content-type": "application/json",
                    "x-api-key": "xxx-xxxxxxxxxxx",
                    "accept": "*/*"
                  }
                },
            "info": {
                "selectionSetList": ["studentUuid", "studentId", "firstName", "lastName", "programId", "status"],
                "selectionSetGraphQL": "{\\n  studentUuid\\n  studentId\\n  firstName\\n  lastName\\n  programId\\n  status\\n}",
                "parentTypeName": "Query",
                "fieldName": "listStudents",
                "variables": {}
            }
        }
        """,

    "GET_STUDENT_BY_STUDENT_ID_DIRECT":
        """
        {
            "route": "get_student",
            "studentId": "1" 
        }
        """,

    "GET_STUDENT_BY_STUDENT_ID_REST":
        """
        {
            "version": "2.0",
            "routeKey": "GET /students/{studentId}",
            "rawPath": "/students/1234",
            "rawQueryString": "testParam=4567&otherParam=8888",
            "headers": {
              "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
              "accept-encoding": "gzip, deflate, br",
              "accept-language": "en-US,en;q=0.9",
              "content-length": "0",
              "host": "test.execute-api.us-east-2.amazonaws.com"
            },
            "queryStringParameters": {
              "otherParam": "8888",
              "testParam": "4567"
            },
            "pathParameters": {
              "studentId": "1"
            },
            "isBase64Encoded": false
        }
        """,

    "GET_STUDENT_BY_STUDENT_ID_GRAPHQL":
        """
        {
            "arguments": {
                "studentId": 1
            },
                "request": {
                  "headers": {
                    "content-type": "application/json",
                    "x-api-key": "xxx-xxxxxxxxxxx",
                    "accept": "*/*"
                  }
                },
            "info": {
                "selectionSetList": ["studentUuid", "studentId", "firstName", "lastName", "programId", "status"],
                "selectionSetGraphQL": "{\\n  studentUuid\\n  studentId\\n  firstName\\n  lastName\\n  programId\\n  status\\n}",
                "parentTypeName": "Query",
                "fieldName": "getStudent",
                "variables": {}
            }
        }
        """

}


class MockContext(LambdaContext):
    def __init__(self,
                 invoked_function_arn="arn:aws:lambda:us-west-2:0000000000:function:mock_function-name:dev",
                 function_name="mock_function_name",
                 memory_limit_in_mb=64,
                 aws_request_id="mock_id"):
        print("Mock context initialized")

def run(event_string, handler_function):
    # Initialize a context to pass into the halder method
    context = MockContext

    # Create an event dictionary from event_string
    event = json.loads(event_string)

    # Set up logging for a local run
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    log = logging.getLogger()

    result = handler_function(event, context)
    # Log the result of the main handler as json
    log.info("\n" + json.dumps(result, indent=4, sort_keys=True, default=str))
    return result


if __name__ == '__main__':
    sys.path.append(os.getcwd())
    from src import lambda_function

    event_name = sys.argv[1]
    print("Running event: " + event_name)
    run(events[event_name], lambda_function.handler)
