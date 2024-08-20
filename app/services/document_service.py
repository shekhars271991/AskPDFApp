
from datetime import datetime
from app.services.DB.redis_service import (set_json, 
                                        get_keys, 
                                        get_json, 
                                        perform_vector_search_for_chunks, 
                                        perform_vector_search_for_documents, 
                                        get_user_docs)
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

def list_uploaded_documents(roles):
    userdocs = get_user_docs(roles)
    return userdocs

def get_docs_related_to_query(query, roles):
    query_embedding = get_embeddings(query)
    doc_details = perform_vector_search_for_documents(query_embedding, roles)
    return get_ids_and_roles(doc_details)


def get_ids_and_roles(doc_details):
    doc_id_and_role = []
    for doc in doc_details:
        doc_id = doc['id']
        roles = doc['roles']
        original_filename = doc['original_filename']
        # Remove the leading 'file_' and trailing '_metadata'
        if doc_id.startswith('file_') and doc_id.endswith('_metadata'):
            cleaned_doc_id = doc_id[len('file_'):-len('_metadata')]
            doc_id_and_role.append((cleaned_doc_id, roles, original_filename))
    return doc_id_and_role
