import os
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import logging
from llm_utils import extract_company_name, extract_support_email
from config import GOOGLE_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL_NAME, DATA_FOLDER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_document_text(file_path: str) -> str:
    text = ""
    try:
        if file_path.endswith(".pdf"):
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
        elif file_path.endswith(".docx"):
            document = DocxDocument(file_path)
            for paragraph in document.paragraphs:
                text += paragraph.text + "\n"
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as txt_file:
                text = txt_file.read()
    except Exception as e:
        logger.error(f"Error reading file '{file_path}': {e}")
        raise
    return text

def process_documents(data_folder: str = DATA_FOLDER) -> tuple[str, str, str]:
    all_text = ""
    company_names = set()
    support_emails = set()
    
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        if filename.endswith((".pdf", ".docx", ".txt")):
            text = get_document_text(file_path)
            all_text += text + "\n\n"
            company_name = extract_company_name(text)
            support_email = extract_support_email(text)
            if company_name.lower() not in ["", "company", "organization"]:
                company_names.add(company_name)
            if support_email:
                support_emails.add(support_email)
    
    company_name = max(company_names, key=len) if company_names else "our company"
    support_email = support_emails.pop() if support_emails else ""
    logger.info(f"Extracted company name: {company_name}, support email: {support_email}")
    return all_text, company_name, support_email

def create_text_chunks(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_text(text)
    return chunks

def create_vectorstore(text_chunks: list[str]) -> FAISS:
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL_NAME, google_api_key=GOOGLE_API_KEY)
        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
        logger.info("Vectorstore created successfully")
        return vectorstore
    except Exception as e:
        logger.error(f"Error creating vectorstore: {e}")
        raise