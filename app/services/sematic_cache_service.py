from app.services.embedding_service import get_embeddings
from app.services.DB.redis_service import set_json, get_json
from app.services.redisvl.sematiccache import perform_vector_search_for_cache
import hashlib
from datetime import datetime
import uuid


def check_sematic_cache(query,roles):
    docs = perform_vector_search_for_cache(query,roles)
    return docs


def generate_uuid():
    return str(uuid.uuid4())


def generate_id_from_query(query):
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()
    # Update the hash object with the bytes of the query
    hash_object.update(query.encode('utf-8'))
    # Get the hexadecimal representation of the hash
    unique_id = hash_object.hexdigest()
    return unique_id


def insert_in_semantic_cache(query, response, access_level, related_docs, related_webpages):
    if response == "I don't know." or response == "I don't know":
        return
        
    query_embedding = get_embeddings(query)
    unique_id = generate_id_from_query(query)
    
    cache_key = f"semcache_{unique_id}"
    cache_value = {
        "query_embeddings": query_embedding.tolist(),
        "query":query,
        "response": response,
        "createdAt": datetime.now().isoformat(),
        "roles": access_level,
        "related_docs": related_docs,
        "related_webpages": related_webpages


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