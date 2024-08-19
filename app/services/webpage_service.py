import requests
from bs4 import BeautifulSoup
from app.services.summerization_model_service import summarize_text
from app.services.redis_service import set_json, get_user_webpages
from app.services.embedding_service import get_embeddings
from app.services.redis_service import perform_vector_search_for_webpages, perform_vector_search_for_web_chunks
from app.services.URL_crawler_service import get_urls_from_page
from urllib.parse import urlparse

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
        webpage_title = doc['webpage_title']
        # Remove the leading 'webpage_' and trailing '_metadata'
        if doc_id.startswith('webpage_') and doc_id.endswith('_metadata'):
            cleaned_doc_id = doc_id[len('webpage_'):-len('_metadata')]
            doc_id_and_role.append((cleaned_doc_id, roles, webpage_title))
    return doc_id_and_role


def get_web_context_from_similar_entries(query, related_webpage_titles):
    query_embedding = get_embeddings(query)
    context = perform_vector_search_for_web_chunks(query_embedding, related_webpage_titles)
    return context


def get_urls(url, alloweddomains, level, max_urls):
    reachable_urls, unreachable_urls = get_urls_from_page(url, level, max_urls, alloweddomains)
    return reachable_urls, unreachable_urls


def get_allowed_domains(allowed_domains, url):
    if not allowed_domains:
        parsed_url = urlparse(url)
        main_domain = parsed_url.netloc
        if not main_domain:
            return "error"
        allowed_domains = [main_domain]
        return allowed_domains
    else:
        return allowed_domains

def list_indexed_webpages(roles):
    userwebpages = get_user_webpages(roles)
    return userwebpages