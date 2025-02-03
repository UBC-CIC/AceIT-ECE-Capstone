import json
import utils
import requests
import psycopg2
import utils.get_canvas_secret
import utils.get_rds_secret

def lambda_handler(event, context):
    headers = event.get("headers", {})
    token  = headers.get("Authorization", {})
    if not token:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Authorization token is required"})
        }

    courses_as_students = get_student_courses(token)
    courses_as_instructor = get_instructor_courses(token)
    availableStudentList = {}
    availableInstructorList = {}
    unavailableStudentList = {}
    for course in courses_as_students:
        # construct object
        if course["workflow_state"] == "available":
            cur_course = {
                "id": course["uuid"],
                "courseCode": course["course_code"],
                "name": course["name"]
            }
            # check course availability in db
            available = get_availability(course["uuid"])
            # add into its corresponding list
            if available:
                availableStudentList.append(cur_course)
            else:
                unavailableStudentList.append(cur_course)

    for course in courses_as_instructor:
        # construct object
        if course["workflow_state"] == "available":
            cur_course = {
                "id": course["uuid"],
                "courseCode": course["course_code"],
                "name": course["name"]
            }
            availableInstructorList.append(cur_course)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({
            "availableCoursesAsStudent": availableStudentList, 
            "availableCoursesAsInstructor": availableInstructorList,
            "unavailableCoursesAsStudent": unavailableStudentList})
    }

# TODO: error handling
def get_student_courses(token):
    """
    Fetch all courses that user enrolled as a student.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/courses?enrollment_state=active&enrollment_type=student"
    response = requests.get(url, headers=HEADERS, verify=False)
    return response.json()

# TODO: error handling
def get_instructor_courses(token):
    """
    Fetch all courses that user enrolled as a instructor.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/courses?enrollment_state=active&enrollment_type=teacher"
    response = requests.get(url, headers=HEADERS, verify=False)
    return response.json()

def get_availability(course_id):
    secret = utils.get_rds_secret.get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    # Database connection parameters
    DB_CONFIG = {
        "host": "privaceitececapstonemainstack-t4grdsdb098395df-peocbczfvpie.czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "dbname": "postgres",
        "user": username,
        "password": password,
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
        cursor.execute(query, (str(course_id),))  # Convert UUID to string
        row = cursor.fetchone()

        if not row:
            return "Course configuration not found"

        # Close database connection
        cursor.close()
        connection.close()

        return row[0] 
    except Exception as e:
        print(f"Error: {e}")
        return "Cannot connect to db"