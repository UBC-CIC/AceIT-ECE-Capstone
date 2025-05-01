import requests
import json
import utils.get_canvas_secret

secret = utils.get_canvas_secret.get_secret()
credentials = json.loads(secret)

def make_canvas_api_call(url, request_type, headers, data={}, params={}):
    try:
        result = {}
        if request_type == "get":
            response = requests.get(url, headers=headers, data=data, params=params)
            response.raise_for_status()

            # deal with pagination
            result = response.json()
            while 'next' in response.links and 'url' in response.links['next']:
                response = requests.get(response.links['next']['url'], headers=headers)
                response.raise_for_status()
                result.extend(response.json())
        elif request_type == "post":
            response = requests.post(url, headers=headers, data=data, params=params)
            response.raise_for_status()
            result = response.json()
        elif request_type == "delete":
            response = requests.delete(url, headers=headers, data=data, params=params)
            response.raise_for_status()
            result = response.json()
        else:
            print(f"Invalid request_type: {request_type}")
            return None
        
        return result
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None

def get_all_courses():
    """
    Fetch all courses from canvas lms.
    """
    BASE_URL = credentials['baseURL']
    TOKEN = credentials['adminAccessToken']
    
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    url = f"{BASE_URL}/api/v1/accounts/1/courses"
    return make_canvas_api_call(url=url, request_type="get", headers=HEADERS)

def get_files_by_course_id(course_id):
    """
    Fetch all files from canvas lms.
    """
    BASE_URL = credentials['baseURL']
    TOKEN = credentials['adminAccessToken']
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    url = f"{BASE_URL}/api/v1/courses/{course_id}/files"

    return make_canvas_api_call(url=url, request_type="get", headers=HEADERS)

def refresh_token(refresh_token):
    BASE_URL = credentials['baseURL']
    CLIENT_ID = credentials['apiKeyId']
    CLIENT_SECRET = credentials['apiKey']
    REDIRECT_URI = credentials['redirectURI']

    url = f"{BASE_URL}/login/oauth2/token"

    data = {
            "client_id": f"{CLIENT_ID}",
            "client_secret": f"{CLIENT_SECRET}",
            "grant_type": "refresh_token",
            "redirect_uri": f"{REDIRECT_URI}",
            "refresh_token": f"{refresh_token}"
            }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    return make_canvas_api_call(url=url, request_type="post", headers=headers, data=data)

def log_out(access_token):
    BASE_URL = credentials['baseURL']

    url = f"{BASE_URL}/login/oauth2/token"

    headers = { 
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
        }
    
    params = {"expire_sessions": "1"}

    return make_canvas_api_call(url=url, request_type="delete", headers=headers, params=params)

def get_access_token(authorization_code):
    BASE_URL = credentials['baseURL']
    CLIENT_ID = credentials['apiKeyId']
    CLIENT_SECRET = credentials['apiKey']
    REDIRECT_URI = credentials['redirectURI']

    url = f"{BASE_URL}/login/oauth2/token"

    data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": authorization_code,
            "scope": "https://canvas.instructure.com/auth/courses.readonly"
            }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    return make_canvas_api_call(url=url, request_type="post", headers=headers, data=data)

def get_user_info(token):
    """
    Fetch user info from canvas lms.
    """
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/users/self"

    return make_canvas_api_call(url=url, request_type="get", headers=HEADERS)

def get_student_courses(token):
    """
    Fetch all courses that user enrolled as a student.
    """
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/courses?enrollment_state=active&enrollment_type=student"

    return make_canvas_api_call(url=url, request_type="get", headers=HEADERS)

def get_instructor_courses(token):
    """
    Fetch all courses that user enrolled as a instructor.
    """
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    instructor_url = f"{BASE_URL}/api/v1/courses?enrollment_state=active&enrollment_type=teacher"
    result_instructor = make_canvas_api_call(url=instructor_url, request_type="get", headers=HEADERS)
    ta_url = f"{BASE_URL}/api/v1/courses?enrollment_state=active&enrollment_type=ta"
    result_ta = make_canvas_api_call(url=ta_url, request_type="get", headers=HEADERS)

    # Combine both lists (avoiding duplicates)
    all_courses = {course["id"]: course for course in result_instructor} 
    for course in result_ta:
        if course["id"] not in all_courses:
            all_courses[course["id"]] = course


    return list(all_courses.values())