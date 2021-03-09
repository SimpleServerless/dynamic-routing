from aws_lambda_powertools import Logger
import logging
from utils import Invocation
from utils import Router
from aws_lambda_powertools.utilities.typing import LambdaContext

log: Logger = Logger()
Logger("botocore").setLevel(logging.INFO)
Logger("urllib3").setLevel(logging.INFO)

router: Router = Router()

# Handler
@log.inject_lambda_context()
def handler(event: dict, context: LambdaContext) -> dict:
    return Invocation(router, event).call()


#
# Query Actions
#

@router.direct("list_students") # Resolves for a direct invoke
@router.rest("GET", "/students") # Resolves for a ReST endpoint
@router.graphql("Query", "listStudents") # Resolves for graphQL endpoint
def list_students(args: dict) -> list:
    return list(students.values())


@router.direct("get_student") # Resolves for a direct invoke
@router.rest("GET", "/students/{studentId}") # Resolves for a ReST endpoint
@router.graphql("Query", "getStudent") # Resolves for graphQL endpoint
def get_student(args: dict) -> dict:
    student_id = int(args['studentId'])
    return students[student_id]


#
# Mutation Actions
#
@router.direct("save_student") # Resolves for a direct invoke
@router.rest("PUT", "/students/{studentId}") # Resolves for a ReST endpoint
@router.graphql("Mutation", "saveStudent")
def save_student(args: dict) -> dict:
    student = args['student']

    # Cover key from either REST path params and GrqphQL inputs
    if 'studentId' in args:  # REST
        key = int(args['studentId'])
        student['studentId'] = key
    else:  # GraphQL or Direct
        key = student['studentId']

    # Add or update student data for given key
    students[key] = student
    return students[key]


students: dict = {
  1: {
    "studentUuid": "78f7424c-b4c0-4196-af42-9a4a32c6f26a",
    "studentId": 1,
    "firstName": "Martha",
    "lastName": "Jones",
    "status": "ENROLLED",
    "programId": "dd961f3d-ae35-4a0b-863a-eaff31e4efc8"
  },
  2: {
    "studentUuid": "87917a4e-9fd0-4207-87da-a7bfb0144d84",
    "studentId": 2,
    "firstName": "Amy",
    "lastName": "Pond",
    "status": "ENROLLED",
    "programId": "faf0108a-352c-4a2e-ab98-956adf5d1ef8"
  },
  3: {
    "studentUuid": "1c60dd8a-9a65-48c0-991c-65c369ec0244",
    "studentId": 3,
    "firstName": "Rose",
    "lastName": "Tyler",
    "status": "ENROLLED",
    "programId": "81541c1a-7ec1-44c2-aa33-385812a8fbcc"
  }
}