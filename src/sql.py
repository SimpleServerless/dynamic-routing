# A place to keep sql statemennts

GET_STUDENTS: str = """
SELECT student_uuid, student_id, first_name, last_name, status, program_id
FROM students
WHERE active = true;
"""

GET_STUDENT_BY_STUDENT_ID: str = """
SELECT student_uuid, student_id, first_name, last_name, status, program_id
FROM students
WHERE active = true
AND student_id = %s;
"""