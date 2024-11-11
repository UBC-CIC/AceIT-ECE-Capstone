# example API endpoints. source: https://github.com/UBC-CIC/LLM-Course-QA

from flask import Blueprint, request, jsonify
from ..business import queryService
from ..core.utils.authDecorator import login_required

queryBp = Blueprint('query', __name__, url_prefix='/queries')

@queryBp.route('', methods=['POST'])
@login_required
def query_llm(user):
    data = request.get_json()
    query_data = {
        'question': data['question'],
        'course_id': data['course_id'],
        'user_id': user.id, # add by middleware TODO
        'conversation_id': data['conversation_id']
    }
    query_response = queryService.query_llm(query_data)
    if query_response:
        return jsonify({'response': query_response["result"], 'conversation_id' : query_response['conversation_id'], 'sources': query_response["sources"]}), 200
    else:
        return jsonify({'error': 'Error creating response'}), 400

@queryBp.route('/conversations/<conversationId>', methods=['GET'])
def query_list(conversationId):
    query_data = {
        'conversation_id': conversationId,
    }
    response = queryService.query_list(query_data)
    if response:
        return jsonify({'queries': response["result"]}), 200
    else:
        return jsonify({'error': 'Error getting queries'}), 400

@queryBp.route('/<courseId>/conversations', methods=['GET'])
@login_required
def conversation_history(user, courseId):
    query_data = {
        'course_id': courseId,
        'user_id': user.id, # add by middleware TODO
    }
    response = queryService.conversation_history(query_data)
    if response:
        return jsonify({'conversations': response["result"], 'course_name' : response["course_name"]}), 200
    else:
        return jsonify({'error': 'Error getting conversations'}), 400