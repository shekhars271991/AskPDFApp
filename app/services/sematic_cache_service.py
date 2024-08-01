from app.services.embedding_service import get_embeddings
from app.services.redis_service import perform_vector_search_for_cache, set_json, get_json
import hashlib
from datetime import datetime
import uuid


def check_sematic_cache(query):
    query_embedding = get_embeddings(query)
    docs = perform_vector_search_for_cache(query_embedding)
    return docs


def generate_uuid():
    return str(uuid.uuid4())


def insert_in_semantic_cache(query, response):
    query_embedding = get_embeddings(query)
    unique_id = generate_uuid()
    
    cache_key = f"semcache_{unique_id}"
    cache_value = {
        "query_embeddings": query_embedding.tolist(),
        "query":query,
        "response": response,
        "createdAt": datetime.now().isoformat()
    }
    set_json(cache_key, '.', cache_value)


def hash_query(query):
    # Encode the input string to bytes
    encoded_string = query.encode('utf-8')
    # Create a new SHA-256 hash object
    hash_object = hashlib.sha256(encoded_string)
    # Get the hexadecimal representation of the hash
    hashed_query = hash_object.hexdigest()
    return hashed_query


def get_data_from_cache(key):
    return get_json(key)