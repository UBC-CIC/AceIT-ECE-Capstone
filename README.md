# Ace It - AI Study Assistant

## Project Overview

Ace It is an AI Study Assistant designed to help university students with their courses. Integrated directly with Canvas LMS and leveraging AI large language models (LLM), Ace It is able to access course information to provide Students contextual support in areas such as:

- Finding Course Information & Material References
- Providing Learning Recommendations (Tips & Suggested Materials)
- Solution Review & Feedback
- Problem Explanation

This repository contains the complete code for the project, including the frontend, backend, and AWS infrastructure.

### User Experience & Features

Users may have one of two roles for each course they are associated with in Canvas, either "Student" or "Instructor". Users are not assigned roles for courses in Ace It, the solution instead uses the roles specified in Canvas.

All users are able to:

1. Log-in using their Canvas authentication credentials
2. See all of their courses in Canvas, separated between "Available Courses" (where the user is an Instructor or the Instructor has enabled Student access) and "Unavailable Courses" (where the Instructor has not enabled Student Access)
3. Change their preferred AI Study Assistant response language

With the Student role, users are able to:

1. Start new conversation sessions or continue previous ones with the AI Study Assistant
2. Ask questions to the AI Study Assistant in their preferred language
3. Receive responses from the AI Study Assistant in their preferred language with references to Canvas

With the Instructor role, users are able to:

1. View Ace It usage analytics for the course
   - Number of questions asked
   - Number of student sessions
   - Number of students using Ace It
   - Most common questions (determined using AI)
   - Most referenced materials
2. Configure the AI Study Assistant for the course, specifically:
   - Enable Student access to the course (default no access)
   - Select which course content to include from Canvas (e.g. Announcements, Syllabus, Files, etc.)
   - Select which types of questions should be supported by the AI Study Assistant
   - Configure custom response tone / style
3. Test the AI Study Assistant for the course, sending messages like a Student would to evaluate the experience

### Demo

TODO: Add gif of short demo video highlighting the key features

### Screenshots

TODO: Add table of screenshots of key functionality

---

## Technical Details

### Key Technologies

Ace It leverages the following key technologies:

- Frontend: React.js (Vite)
- Backend: Python 3
- Infrastructure: AWS CDK

### Infrastructure Architecture

The following diagram depicts the high-level AWS architecture:

TODO: Add diagram image here

### Repository Structure

TODO: Need to come back to this after we clean up the code base some more. Once complete, we should note our logical concept about how the code was organized with a specific list afterwards of the directory with a summary next to each item.

---

## Deploying & Running Ace It on AWS

### Pre-Requisites

To deploy Ace It, you will need to first have the following pre-requisites:

1. A Canvas LMS instance where you have the Admin role
   - If you need to first set up a Canvas instance, please refer to the [Canvas documentation here](https://github.com/instructure/canvas-lms/wiki/Production-Start)
2. An AWS account with appropriate permissions for deployment

### Instructions

Deploying Ace It on AWS requires configuration in several areas, specifically AWS, Canvas, and minor code adjustments.

#### Canvas Configuration

TODO (e.g. API and app keys)

#### AWS Configuration

TODO

#### Frontend Code Configuration

TODO (e.g. APIs and styling)

#### Backend Code Configuration

TODO

#### Infrastructure Code Configuration

TODO
