import requests
from bs4 import BeautifulSoup
from app.services.summerization_model_service import summarize_text
import os
import uuid
from app.services.redis_service import set_json
from app.services.embedding_service import get_embeddings
from app.services.redis_service import perform_vector_search_for_webpages, perform_vector_search_for_web_chunks

MAX_TITLE_LENGTH=5 # TOKENS
MIN_TITLE_LENGTH=5

def extract_text_from_url(url):
    try:
        # Fetch the HTML content from the URL
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text

    except requests.exceptions.RequestException as e:
        return "error"

def get_webpage_title(text):
    title = summarize_text(text)
    return title

def get_unique_webpagename(title):
    original_title= title
    filename_prefix = original_title[:3] if len(original_title) >= 3 else original_title
    unique_title= f"{filename_prefix}_{str(uuid.uuid4())[:8]}"
    return unique_title

def store_webpage_metadata(webpage_title, unique_name, roles, summary, summary_embeddings):
    metadata_key = f"webpage_{unique_name}_metadata"
    metadata = {
        "webpage_title": webpage_title,
        "unique_title":unique_name,
        "roles": roles,
        "summary": summary,
        "summary_embeddings":summary_embeddings
    }
    set_json(metadata_key, '.', metadata)



def get_webpages_related_to_query(query, roles):
    query_embedding = get_embeddings(query)
    doc_details = perform_vector_search_for_webpages(query_embedding, roles)
    return get_ids_and_roles(doc_details)

def get_ids_and_roles(doc_details):
    doc_id_and_role = []
    for doc in doc_details:
        doc_id = doc['id']
        roles = doc['roles']
        # Remove the leading 'webpage_' and trailing '_metadata'
        if doc_id.startswith('webpage_') and doc_id.endswith('_metadata'):
            cleaned_doc_id = doc_id[len('webpage_'):-len('_metadata')]
            doc_id_and_role.append((cleaned_doc_id, roles))
    return doc_id_and_role


def get_web_context_from_similar_entries(query, related_docs):
    query_embedding = get_embeddings(query)
    context = perform_vector_search_for_web_chunks(query_embedding, related_docs)
    return context
