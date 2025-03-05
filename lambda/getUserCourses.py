import json
import psycopg2
import utils.get_rds_secret
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_student_courses, get_instructor_courses

def lambda_handler(event, context):
    headers = event.get("headers", {})
    if not headers:
        return construct_response(400, {"error": "Header is missing"})
    
    token  = headers.get("Authorization", {})
    if not token:
        return construct_response(400, {"error": "Missing required fields: 'Authorization' is required"})

    courses_as_students = get_student_courses(token)
    if courses_as_students is None:
        return construct_response(500, {"error": "Failed to fetch student courses from Canvas"})
    
    courses_as_instructor = get_instructor_courses(token)
    if courses_as_instructor is None:
        return construct_response(500, {"error": "Failed to fetch instructor courses from Canvas"})
    
    availableStudentList = []
    availableInstructorList = []
    unavailableStudentList = []
    for course in courses_as_students:
        # construct object
        if course["workflow_state"] == "available":
            cur_course = {
                "id": course["id"],
                "courseCode": course["course_code"],
                "name": course["name"]
            }
            # check course availability in db
            available = get_availability(course["id"])
            # add into its corresponding list
            if available:
                availableStudentList.append(cur_course)
            else:
                unavailableStudentList.append(cur_course)

    for course in courses_as_instructor:
        # construct object
        if course["workflow_state"] == "available":
            cur_course = {
                "id": course["id"],
                "courseCode": course["course_code"],
                "name": course["name"]
            }
            availableInstructorList.append(cur_course)
            print("type of id", type(course["id"]))

    response_body = {
        "availableCoursesAsStudent": availableStudentList, 
        "availableCoursesAsInstructor": availableInstructorList,
        "unavailableCoursesAsStudent": unavailableStudentList
    }

    return construct_response(200, response_body)

def get_availability(course_id):
    secret = utils.get_rds_secret.get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    static_db_config = utils.get_rds_secret.load_db_config()
    # Combine static DB config and dynamic credentials
    DB_CONFIG = {
        **static_db_config,
        "user": username,
        "password": password
    }
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query the course configuration
        query = """
        SELECT student_access_enabled
        FROM course_configuration
        WHERE course_id = %s
        """
        cursor.execute(query, (str(course_id),))  # Convert ID to string
        row = cursor.fetchone()

        if not row:
            return False

        # Close database connection
        cursor.close()
        connection.close()

        return row[0] 
    except Exception as e:
        print(f"Error: {e}")
        return False