def create_system_prompt(settings):
    """
    Generate a system prompt for the course assistant based on professor's settings,
    emphasizing both enabled and disabled features.
    :param settings: A dictionary containing course assistant configuration.
    :return: A formatted system prompt string.
    """
    # Extract settings
    supported_questions = settings.get("selectedSupportedQuestions", {})
    custom_response_format = settings.get("customResponseFormat", "Provide clear and helpful responses.")

    # Define mappings for question types
    question_types = {
        "RECOMMENDATIONS": "provide study recommendations",
        "PRACTICE_PROBLEMS": "provide practice problems",
        "SOLUTION_REVIEW": "review solutions",
        "EXPLANATION": "offer detailed explanations"
    }

    # Separate enabled and disabled features
    enabled_features = [
        phrase for key, phrase in question_types.items() if supported_questions.get(key, False)
    ]
    disabled_features = [
        phrase for key, phrase in question_types.items() if not supported_questions.get(key, False)
    ]

    # Format the enabled features into a readable list
    enabled_features_list = ", ".join(enabled_features[:-1])
    if len(enabled_features) > 1:
        enabled_features_list += f", and {enabled_features[-1]}"  # Add "and" before the last item
    elif enabled_features:
        enabled_features_list = enabled_features[0]

    # Format the disabled features into a readable list
    disabled_features_list = ", ".join(disabled_features[:-1])
    if len(disabled_features) > 1:
        disabled_features_list += f", and {disabled_features[-1]}"
    elif disabled_features:
        disabled_features_list = disabled_features[0]

    # Construct the system prompt
    system_prompt = f"""
You are a course assistant designed to help students in their learning journey. Your role is to:
{enabled_features_list}.
Do not:
{disabled_features_list}.
Respond to all student inquiries in the following style: {custom_response_format}.
Ensure your responses are always accurate, engaging, respectful, and inform students when you have questions unsure or encountering a controversial topic.
"""
    print(system_prompt.strip())


if __name__ == '__main__':
    create_system_prompt({"selectedSupportedQuestions": {
        "RECOMMENDATIONS": True,
        "PRACTICE_PROBLEMS": False,
        "SOLUTION_REVIEW": True,
        "EXPLANATION": True
    }, "customResponseFormat": "guide the user step by step solving the problems"})