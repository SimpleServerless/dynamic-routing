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
              "accept": "application/json"
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
                    "x-api-key": "xxx-xxxxxxxxxxx",
                    "accept": "application/json"
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
              "accept": "application/json"
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
                    "x-api-key": "xxx-xxxxxxxxxxx",
                    "accept": "application/json"
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
        """,

    "SAVE_STUDENT_DIRECT":
        """
        {
            "route": "save_student",
            "student": {
                "studentUuid": "7812233d-9289-4442-8cbb-92535124e9a7",
                "studentId": 4,
                "firstName": "Jack ",
                "lastName": "Harkness",
                "status": "ENROLLED",
                "programId": "d958c587-db7b-41f9-9954-c33dc56e08f5"
            }
        }
        """,

    "SAVE_STUDENT_REST":
        """
        {
            "version": "2.0",
            "routeKey": "PUT /students/{studentId}",
            "rawPath": "/students/1",
            "rawQueryString": "testParam=4567&otherParam=8888",
            "headers": {
              "accept": "application/json"
            },
            "queryStringParameters": {
              "otherParam": "8888",
              "testParam": "4567"
            },
            "pathParameters": {
              "studentId": "4"
            },
            "body": "{\\\"student\\\": {\\\"studentUuid\\\": \\\"7812233d-9289-4442-8cbb-92535124e9a7\\\", \\\"firstName\\\": \\\"Jack\\\", \\\"lastName\\\": \\\"Harkness\\\", \\\"status\\\": true, \\\"programId\\\": \\\"d958c587-db7b-41f9-9954-c33dc56e08f5\\\"}}",
            "isBase64Encoded": false
        }
        """,

    "SAVE_STUDENT_GRAPHQL":
        """
        {
            "arguments": {
                "studentId": 1
            },
                "request": {
                  "headers": {
                    "x-api-key": "xxx-xxxxxxxxxxx",
                    accept": "application/json"
                  }
                },
            "info": {
                "selectionSetList": ["studentUuid", "studentId", "firstName", "lastName", "programId", "status"],
                "selectionSetGraphQL": "{\\n  studentUuid\\n  studentId\\n  firstName\\n  lastName\\n  programId\\n  status\\n}",
                "parentTypeName": "Mutation",
                "fieldName": "saveStudent",
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
    print("\nEVENT:")
    print(event_string)
    event = json.loads(event_string)

    result = handler_function(event, context)

    # Log the result of the main handler as json
    print("\nRESULT:")
    print("\n" + json.dumps(result, indent=4, sort_keys=True, default=str))
    return result


if __name__ == '__main__':
    sys.path.append(os.getcwd())
    from src import lambda_function

    event_name = sys.argv[1]
    print("Running event: " + event_name)
    run(events[event_name], lambda_function.handler)
