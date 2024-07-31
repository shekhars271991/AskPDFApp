import fitz
import os
import uuid
from datetime import datetime
from app.services.redis_service import set_json, get_keys, get_json
from sentence_transformers import SentenceTransformer


UPLOAD_DIRECTORY = 'AskPDF/backend_llama/uploadedFiles'
model = SentenceTransformer('all-MiniLM-L6-v2')


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

def get_embeddings(chunks):
    embeddings = model.encode(chunks)
    return embeddings

def get_unique_filename(filename):
    original_filename = filename
    filename_prefix = original_filename[:3] if len(original_filename) >= 3 else original_filename
    filename, file_extension = os.path.splitext(original_filename)
    unique_filename = f"{filename_prefix}_{str(uuid.uuid4())[:8]}{file_extension}"
    return unique_filename

def store_file_metadata(doc_name, original_filename, upload_time, roles, summary, summary_embeddings):
    metadata_key = f"file_{doc_name}_metadata"
    metadata = {
        "uploaded_time": upload_time,
        "original_filename": original_filename,
        "roles": roles,
        "summary": summary,
        "summary_embeddings":summary_embeddings
    }
    set_json(metadata_key, '.', metadata)

def list_uploaded_documents():
    document_keys = get_keys('file_*')
    documents = []
    for key in document_keys:
        if key.decode('utf-8').endswith('_metadata'):
            doc_name = key.decode('utf-8').split('_metadata')[0].split('file_')[1]
            metadata = get_json(key)
            documents.append({
                "doc_name": doc_name,
                "metadata": metadata
            })
    return documents
