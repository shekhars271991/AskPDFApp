import requests
from bs4 import BeautifulSoup
from app.services.summerization_model_service import summarize_text
import os
import uuid
from app.services.redis_service import set_json

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