import os
import uuid
from datetime import datetime
from app.services.redis_service import set_json, get_keys, get_json, perform_vector_search_for_chunks, perform_vector_search_for_documents
from app.services.embedding_service import get_embeddings
import PyPDF2
# from sentence_transformers import SentenceTransformer


UPLOAD_DIRECTORY = 'AskPDF/backend_llama/uploadedFiles'
# model = SentenceTransformer('all-MiniLM-L6-v2')


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

def get_unique_filename(filename):
    original_filename = filename
    filename_prefix = original_filename[:3] if len(original_filename) >= 3 else original_filename
    filename, file_extension = os.path.splitext(original_filename)
    unique_filename = f"{filename_prefix}_{str(uuid.uuid4())[:8]}{file_extension}"
    return unique_filename


def get_context_from_similar_entries(query, related_docs):
    query_embedding = get_embeddings(query)
    context = perform_vector_search_for_chunks(query_embedding, related_docs)
    return context

def store_file_metadata(doc_name, original_filename, upload_time, roles, summary, summary_embeddings):
    metadata_key = f"file_{doc_name}_metadata"
    metadata = {
        "uploaded_time": upload_time,
        "original_filename": original_filename,
        "unique_filename":doc_name,
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
                "uploaded_time":metadata['uploaded_time'],
                "orignal_filename":metadata['original_filename'],
                "summary":metadata['summary']
            })
    return documents

def get_docs_related_to_query(query, roles):
    query_embedding = get_embeddings(query)
    doc_ids = perform_vector_search_for_documents(query_embedding, roles)
    return clean_filenames(doc_ids)


def clean_filenames(filenames):
    cleaned_filenames = []
    for filename in filenames:
        # Remove the leading 'file_' and trailing '_metadata'
        if filename.startswith('file_') and filename.endswith('_metadata'):
            cleaned_filename = filename[len('file_'):-len('_metadata')]
            cleaned_filenames.append(cleaned_filename)
    return cleaned_filenames