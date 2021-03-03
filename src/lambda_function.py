from aws_lambda_powertools import Logger
from psycopg2.extras import RealDictCursor
from utils import Invocation
from utils import Router
import utils
import psycopg2
import sql
from typing import Any, Optional, Dict
from aws_lambda_powertools.utilities.typing import LambdaContext
from psycopg2 import _connect

log: Logger = Logger()
router: Router = Router()
conn: Optional[_connect] = None

# Handler
@log.inject_lambda_context(log_event=True)
def handler(event: dict, context: LambdaContext) -> dict:
    set_connection()
    return Invocation(router, event).call()


#
# Query Actions
#

@router.direct("list_students") # Resolves for a direct invoke
@router.rest("GET", "/students") # Resolves for a ReST endpoint
@router.graphql("Query", "listStudents") # Resolves for graphQL endpoint
def list_students(args: dict) -> dict:
    with conn.cursor() as curs:
        curs.execute( sql.GET_STUDENTS, )
        item_list = curs.fetchall()
    item_list = utils.camelfy(item_list)
    return item_list


@router.direct("get_student") # Resolves for a direct invoke
@router.rest("GET", "/students/{studentId}") # Resolves for a ReST endpoint
@router.graphql("Query", "getStudent") # Resolves for graphQL endpoint
def get_student(args: dict) -> dict:
    student_id = args.get('studentId')
    with conn.cursor() as curs:
        curs.execute(sql.GET_STUDENT_BY_STUDENT_ID, (student_id,))
        item = curs.fetchone()
    item = utils.camelfy(item)

    return item


#
# Mutation Actions
#
@router.direct("save_student") # Resolves for a direct invoke
@router.rest("PUT", "/students") # Resolves for a ReST endpoint
@router.graphql("Mutation", "saveStudent")
def save_student(args: dict) -> dict:
    # Save a dog
    return {'statusCode': 202}


# Lazy load connection. Should only happen on cold start
def set_connection():
    global conn

    try:
        if conn is None or conn.closed > 0:
            db_user, db_password = utils.get_db_credentials()
            log.info("user " + db_user)
            conn = psycopg2.connect(user=db_user,
                                          password=db_password,
                                          sslmode='prefer',
                                          connect_timeout=3,
                                          cursor_factory=RealDictCursor)
            log.info("New DB connection created")
    except Exception as e:
        log.error(e)
        if conn is not None:
            conn.rollback()
        raise e
    finally:
        if conn is not None:
            conn.reset()