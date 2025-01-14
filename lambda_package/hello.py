# import json
# def lambda_handler(event, context):
#     print("Lambda function invoked!")
#     return {
#         'statusCode': 200,
#         'headers': {
#             'Access-Control-Allow-Headers': 'Content-Type',
#             'Access-Control-Allow-Origin': '*',
#             'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
#         },
#         'body': json.dumps('Hello from Lambda!')
#     }

# import json
# import boto3
# import io
# import pymupdf  # Use the updated pymupdf module
# from docx import Document  # python-docx for Word documents

# s3_client = boto3.client('s3')
# client_textract = boto3.client('textract')
# translate_client = boto3.client('translate')

# def read_pdf(file_data):
#     """Extract text from a PDF using pymupdf."""
#     pdf_text = ""
#     with pymupdf.open(stream=file_data, filetype="pdf") as pdf:
#         for page in pdf:
#             pdf_text += page.get_text()
#     return pdf_text

# def read_docx(file_data):
#     """Extract text from a DOCX file."""
#     doc_text = ""
#     doc = Document(io.BytesIO(file_data))  # Read docx from bytes
#     for para in doc.paragraphs:
#         doc_text += para.text + "\n"
#     return doc_text

# def lambda_handler(event, context):
#     bucket_name = 'bucketfortextextract'
#     file_name = 'sample.txt'
#     extracted_text = ''

#     s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
#     file_data = s3_response["Body"].read()

#     # Determine file type by extension
#     if file_name.endswith('.txt'):
#         extracted_text = file_data.decode('utf-8')  # Handle plain text
#     elif file_name.endswith('.pdf'):
#         extracted_text = read_pdf(file_data)  # Handle PDF
#     # elif file_name.endswith('.docx'):
#     #     extracted_text = read_docx(file_data)  # Handle DOCX
#     else:
#         return {
#             'statusCode': 400,
#             'body': json.dumps("Unsupported file type!")
#         }

#     return {
#         'statusCode': 200,
#         'headers': {
#             'Access-Control-Allow-Headers': 'Content-Type',
#             'Access-Control-Allow-Origin': '*',
#             'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
#         },
#         'body': json.dumps(str(extracted_text).upper())
#     }



import json
import boto3

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = 'bucketfortextextract'
    file_name = 'sample.txt'

    print("here")

    s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    print("s3_response:", s3_response)

    file_data = s3_response["Body"].read().decode('utf-8')
    print("file_data:", file_data)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(str(file_data).upper())
    }

# if __name__=='__main__':
#     print(lambda_handler(None, None))