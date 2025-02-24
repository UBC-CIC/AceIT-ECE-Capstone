def translate_document_names(documents, target_language, translate_client):
    """
    Translates only the document names while keeping other fields unchanged.
    """
    translated_docs = []

    for doc in documents:
        translated_name = translate_text(doc["documentName"], target_language, translate_client)
        translated_docs.append({
            "documentName": translated_name,  # Translated name
            "sourceUrl": doc["sourceUrl"],  # Unchanged
            "documentContent": doc["documentContent"]  # Unchanged
        })

    return translated_docs

def translate_text(text, target_language, translate_client):
    """Translates text to the student's preferred language using Amazon Translate."""
    try:
        response = translate_client.translate_text(
            Text=text,
            SourceLanguageCode="auto",  # Auto-detect source language
            TargetLanguageCode=target_language
        )
        return response["TranslatedText"]
    except Exception as e:
        print(f"Error translating text: {e}")
        return text  # Return original text if translation fails