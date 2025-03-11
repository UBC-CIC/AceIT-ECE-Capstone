import json
import boto3
from datetime import datetime 
from .get_canvas_secret import get_secret
import requests
from bs4 import BeautifulSoup

def clean_html(text):
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()

lambda_client = boto3.client('lambda')
def call_course_activity_stream(auth_token, course_id):
    secret = get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {auth_token}"}
    # print("Token: ", auth_token)

    url = f"{BASE_URL}/api/v1/courses/{course_id}/activity_stream"
    try:
        response = requests.get(url, headers=HEADERS, verify=False)
        response.raise_for_status()
        # Lambda function to extract and format the data
        response = response.json()
        format_data = lambda entries: "\n".join(
            [f"Type: {entry['type']}\nTitle: {entry['title']}\nMessage: {clean_html(entry['message'])}\n" for entry in entries]
        )
        result = format_data(response)
        # print("format Result: ", result)
        # print("result type", type(result))
        return result
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None
    
def fetch_syllabus_from_canvas(auth_token, base_url, course_id):
    """
    Fetch syllabus body from Canvas API.
    """
    url = f"{base_url}/api/v1/courses/{course_id}?include[]=syllabus_body"
    # url = f"https://15.157.251.49/api/v1/courses/{course_id}?include[]=syllabus_body"
    headers = {"Authorization": f"Bearer {auth_token}"}
    url_syllabus = f"{base_url}/courses/{course_id}/assignments/syllabus"

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        course_data = response.json()
        syllabus_body = course_data.get("syllabus_body", "")

        if syllabus_body:
            # Convert HTML to plain text
            # print("syllabus body: ", syllabus_body)
            soup = BeautifulSoup(syllabus_body, "html.parser")
            # print("soup: ", soup.get_text(separator="\n").strip())
            str_syllabus = "syllabus: " + soup.get_text(separator="\n").strip() + "; syllabus link: " + url_syllabus
            return str_syllabus
    
    print(f"Failed to fetch syllabus: {response.status_code}, {response.text}")
    return None

def fetch_announcments_from_canvas(auth_token, base_url, course_id):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = "2025-01-01" # better use the start time of the term
    announcments_url = f"{base_url}/api/v1/announcements?context_codes[]=course_{course_id}&active_only=true&end_date={end_date}&start_date={start_date}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    url_announcements = f"{base_url}/courses/{course_id}/announcements"
    response = requests.get(announcments_url, headers=headers, verify=False)
    return_str = "Announcements: \n"
    if response.status_code == 200:
        announcement_list = response.json()
        counter = 0
        for announcement in announcement_list:
            counter += 1
            announcement_str = f"  Announcement {counter}: \n"
            # get announcement_title
            announcement_title = announcement.get("title", "")
            str_to_indent = "Announcement title: \n" + announcement_title + "\n"
            announcement_str += indent_string(str_to_indent, 2)

            # get announcement_message
            announcement_message_html = announcement.get("message", "")
            if announcement_message_html:
                # Convert HTML to plain text
                soup = BeautifulSoup(announcement_message_html, "html.parser")
                announcement_message_str = soup.get_text(separator="\n").strip()
                str_to_indent = "Announcement body: \n" + announcement_message_str + "\n"
                announcement_str += indent_string(str_to_indent, 2)
            url_announcement = announcement.get("html_url", "")
            announcement_str += f"  Announcement {counter} link: " + url_announcement + "\n"

            return_str += announcement_str
        return_str += "Announcements link: " + url_announcements
        return return_str
    print(f"Failed to fetch announcements: {response.status_code}, {response.text}")
    return None

def fetch_discussions_from_canvas(auth_token, base_url, course_id):
    message_url = f"{base_url}/api/v1/courses/{course_id}/discussion_topics"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(message_url, headers=headers, verify=False)
    if response.status_code == 200:
        discussion_list = response.json()
        return_str = "Discussions: \n"
        counter = 0
        for discussion in discussion_list:
            counter += 1
            dicussion_str = f"Discussion post number {counter}: \n"
            # get instructor_message
            instructor_message = discussion.get("message", "")
            str_to_indent = "Instructor message: \n" + instructor_message + "\n"
            dicussion_str += indent_string(str_to_indent, 2)

            # get student reply threads
            topic_id = discussion.get("id", "")
            topic_url = f"{base_url}/api/v1/courses/{course_id}/discussion_topics/{topic_id}/view"
            view_response = requests.get(topic_url, headers=headers, verify=False)
            if view_response.status_code == 200:
                discussion_info = view_response.json()
                discussion_threads = discussion_info.get("view", "")
                student_discussions_html = extract_messages(discussion_threads)
                if student_discussions_html:
                    # Convert HTML to plain text
                    soup = BeautifulSoup(student_discussions_html, "html.parser")
                    student_discussions = soup.get_text(separator="\n").strip()
                    str_to_indent = "Student reply to discussions: \n" + student_discussions + "\n"
                    dicussion_str += indent_string(str_to_indent, 2)
            # add dicussion link
            url_discussion = discussion.get("html_url", "")
            dicussion_str += f"  Discussion {counter} link: " + url_discussion + "\n"
            return_str += dicussion_str
        url_discussions = f"{base_url}/courses/{course_id}/discussion_topics"
        return_str += "Dicussions link: " + url_discussions   
        return return_str
    print(f"Failed to fetch discussion: {response.status_code}, {response.text}")
    return None

def extract_messages(threads, depth=0):
    """
    Helper Function to process messages recursively
    """
    result = ""
    for thread in threads:
        if thread.get("deleted", "") != True:
            # Indentation based on depth to format hierarchy
            if "message" in thread and thread["message"]:
                indent = "  " * depth
                result += f"{indent}- {thread['message']}\n"
                if "replies" in thread and thread["replies"]:
                    result += extract_messages(thread["replies"], depth + 1)
    return result

def indent_string(text, indent_level=1, indent_char="  "):
    """
    Helper Function to adds indentation at the beginning of each line in the given text.
    """
    indent = indent_char * indent_level
    return "\n".join(indent + line for line in text.split("\n"))

def fetch_assignments_from_canvas(auth_token, base_url, course_id):
    assignments_url = f"{base_url}/api/v1/courses/{course_id}/assignments"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(assignments_url, headers=headers, verify=False)
    if response.status_code == 200:
        assignments_list = response.json()
        return_str = "Assignments: \n"
        counter = 0
        for assignment in assignments_list : 
            # get none quiz assingments
            if assignment.get("workflow_state", "") == "published" and not assignment.get("quiz_id", "") and not assignment.get("is_quiz_assignment", ""):
                counter += 1
                assignment_str = f" Assignment {counter}: \n"
                # get name
                assignment_name = assignment.get("name", "")
                str_to_indent = "Assignment name: \n" + assignment_name + "\n"
                assignment_str += indent_string(str_to_indent, 2)
                # get due date
                due_date = assignment.get("due_at", "")
                if due_date:
                    str_to_indent = "Assignment due date: \n" + due_date + "\n"
                    assignment_str += indent_string(str_to_indent, 2)
                # get description
                description_html = assignment.get("description", "")
                if description_html:
                    # Convert HTML to plain text
                    soup = BeautifulSoup(description_html, "html.parser")
                    description_str = soup.get_text(separator="\n").strip()
                    str_to_indent = "Assignment description: \n" + description_str + "\n"
                    assignment_str += indent_string(str_to_indent, 2)
                # add assignment link
                url_assignment = assignment.get("html_url", "")
                assignment_str += f"  Assignment {counter} link: " + url_assignment + "\n"
                return_str += assignment_str

        url_assignments = f"{base_url}/courses/{course_id}/assignments"
        return_str += "Assignments link: " + url_assignments   
        return return_str
    print(f"Failed to fetch assignments: {response.status_code}, {response.text}")
    return None
    
def fetch_quizzes_from_canvas(auth_token, base_url, course_id):
    quizzes_url = f"{base_url}/api/v1/courses/{course_id}/quizzes"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(quizzes_url, headers=headers, verify=False)
    if response.status_code == 200:
        quizzes_list = response.json()
        return_str = "Quizzes: \n"
        counter = 0
        for quiz in quizzes_list:
            if quiz.get("published", ""):
                counter += 1
                quiz_str = f"  Quiz {counter}: \n"
                # get quiz title
                quiz_title = quiz.get("title", "")
                str_to_indent = "Quiz title: " + quiz_title + "\n"
                quiz_str += indent_string(str_to_indent, 2)
                # get due date
                quiz_due_date = quiz.get("due_at", "")
                if quiz_due_date:
                    str_to_indent = "Quiz due date: " + quiz_due_date + "\n"
                    quiz_str += indent_string(str_to_indent, 2)
                # get quiz description
                quiz_description = quiz.get("description", "")
                str_to_indent = "Quiz description: " + quiz_description + "\n"
                quiz_str += indent_string(str_to_indent, 2)
                # get quiz type
                quiz_type = quiz.get("quiz_type", "") # possible value: {graded_survey,practice_quiz,survey,assignment}
                str_to_indent = "Quiz type: " + quiz_type + "\n"
                quiz_str += indent_string(str_to_indent, 2)
                # get question and answer
                quiz_id = quiz.get("id", "")
                if quiz_id:
                    questions_url = f"{base_url}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions"
                    questions_response = requests.get(questions_url, headers=headers, verify=False)
                    if questions_response.status_code == 200:
                        questions_list = questions_response.json()
                        quiz_str += indent_string("Quiz questions: \n", 2)
                        question_counter = 0
                        for question in questions_list:
                            question_counter += 1
                            # question number
                            question_position = question.get("position", question_counter)
                            str_to_indent = f"Question {question_position}: \n"
                            quiz_str += indent_string(str_to_indent, 3)
                            
                            # question points
                            points_possible = question.get("points_possible", "")
                            str_to_indent = f"Available points for Question {question_position}: " + points_possible + "\n"
                            quiz_str += indent_string(str_to_indent, 4)

                            # name
                            question_name = question.get("question_name", "")
                            str_to_indent = "Question name: " + question_name + "\n"
                            quiz_str += indent_string(str_to_indent, 4)

                            # type
                            question_type = question.get("question_type", "")
                            str_to_indent = "Question type: " + question_type + "\n"
                            quiz_str += indent_string(str_to_indent, 4)

                            # question text html form
                            question_content_html = question.get("question_text", "")
                            if question_content_html:
                                # Convert HTML to plain text
                                soup = BeautifulSoup(question_content_html, "html.parser")
                                question_content_str = soup.get_text(separator="\n").strip()
                                str_to_indent = "Question description: \n" + question_content_str + "\n"
                                quiz_str += indent_string(str_to_indent, 4)

                            # add question answers if available
                            show_correct_answers = quiz.get("show_correct_answers", "") # boolean
                            answers_list = quiz.get("answers", "") # json list
                            due_date = datetime.strptime(quiz_due_date, "%Y-%m-%dT%H:%M:%SZ")
                            past_due = due_date <= datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                            has_answer = (quiz_type == "practice_quiz") or (quiz_type == "assignment")

                            if answers_list and show_correct_answers and past_due and has_answer:
                                str_to_indent = f"Answers: \n"
                                answer_str = indent_string(str_to_indent, 4)
                                if question_type != "matching_question":
                                    answer_counter = 0
                                    for answer in answers_list:
                                        answer_counter += 1
                                        # answer text
                                        answer_text = answer.get("text", "")
                                        str_to_indent = f"Answer {answer_counter}: \n" + answer_text + "\n"
                                        answer_str += indent_string(str_to_indent, 5)
                                        # answer weight
                                        answer_weight = answer.get("weight", "")
                                        str_to_indent = f"Answer {answer_counter} wight: \n" + answer_weight + "%" + "\n"
                                        answer_str += indent_string(str_to_indent, 5)
                                else:
                                    # matching_question need to get both left and right for each matching
                                    match_counter = 0
                                    for answer in answers_list:
                                        match_counter += 1
                                        # answer left + right
                                        answer_left = answer.get("left", "")
                                        answer_right = answer.get("right", "")
                                        if answer_left and answer_right:
                                            str_to_indent = f"Matching {answer_counter}: \n" + answer_left + "--" + answer_right+ "\n"
                                            answer_str += indent_string(str_to_indent, 5)

                                quiz_str += answer_str
                    else:
                        print("failed to get questions and answers")

                url_quiz = quiz.get("html_url", "")
                quiz_str += "  Quiz link: " + url_quiz + "\n"

        url_quizzes = f"{base_url}/courses/{course_id}/quizzes"
        return_str += "Quizzes link: " + url_quizzes   
        return return_str
    print(f"Failed to fetch discussion: {response.status_code}, {response.text}")
    return None

def fetch_pages_from_canvas(auth_token, base_url, course_id):
    pages_url = f"{base_url}/api/v1/courses/{course_id}/pages?include[]=body"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(pages_url, headers=headers, verify=False)
    if response.status_code == 200:
        pages_list = response.json()
        return_str = "Pages: \n" 
        counter = 0
        for page in pages_list:
            counter += 1
            page_str = f"  Page {counter}: \n"
            # front page info
            is_front_page = page.get("front_page", "")
            if is_front_page:
                page_str += f"  This Page is the course front page: \n"
            # get title
            page_title = page.get("title", "")
            str_to_indent = f"Page Title: " + page_title + "\n"
            page_str += indent_string(str_to_indent, 2)

            # get content
            page_body_html = page.get("body", "")
            if page_body_html:
                # Convert HTML to plain text
                soup = BeautifulSoup(page_body_html, "html.parser")
                page_body_str = soup.get_text(separator="\n").strip()
                str_to_indent = "Page body: \n" + page_body_str + "\n"
                page_str += indent_string(str_to_indent, 2)

            # add page link
            url_page = page.get("html_url", "")
            page_str += f"  Page {counter} link: " + url_page + "\n"
            return_str += page_str
        url_pages = f"{base_url}/courses/{course_id}/pages"
        return_str += "Pages link: " + url_pages   
        return return_str
    print(f"Failed to fetch pages: {response.status_code}, {response.text}")
    return None