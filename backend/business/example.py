# example business level logic. source: https://github.com/UBC-CIC/LLM-Course-QA

from langchain_community.document_loaders import AmazonTextractPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..config import Config

# Extracts plain text from PDF stored in S3 using Textract
def extract_text(s3_path, document_id):
    client = Config.SESSION.client("textract", region_name=Config.REGION_NAME)
    loader = AmazonTextractPDFLoader(s3_path, client=client)
    document = loader.load()
    text_splitter = RecursiveCharacterTextSplitter (chunk_size=2048, chunk_overlap=64)
    documents = text_splitter.split_documents(document)
    return documents
