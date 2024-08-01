import numpy as np
from redis.commands.search.query import Query
from redis.commands.search.field import TextField, VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from sentence_transformers import SentenceTransformer
import redis
import bcrypt
from config.config import Config


redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB
)

# Your existing code for Redis interactions


CHUNK_INDEX_NAME = "idxpdf"
SUMMARY_INDEX_NAME = "idxsumm"
CACHE_INDEX_NAME = "idxcache"
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_vector_index_chunk():
    schema = [
        TextField("$.chunk", as_name='chunk'),
        TextField("$.roles", as_name='roles'),
        TextField("$.doc_name", as_name='doc_name'),
        VectorField('$.embedding', "HNSW", {
            "TYPE": 'FLOAT32',
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE"
        }, as_name='vector')
    ]

    idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['chunk_'])

    try:
        redis_client.ft(CHUNK_INDEX_NAME).dropindex()
    except:
        pass

    redis_client.ft(CHUNK_INDEX_NAME).create_index(schema, definition=idx_def)

def perform_vector_search_for_chunks(query_embedding, related_docs):
    # Convert query embedding to a binary format for Redis
    vector = np.array(query_embedding, dtype=np.float32).tobytes()   
    doc_name_filter = ""
    for i, doc in enumerate(related_docs):
        if i > 0:
            doc_name_filter += " | "
        doc_name_filter += f"@doc_name:{doc}"    
    

    q = Query(f'({doc_name_filter})=>[KNN 3 @vector $query_vec AS vector_score]')\
                .sort_by('vector_score')\
                .return_fields('vector_score', 'chunk')\
                .dialect(3)

    # Set the parameters for the query, including the vector for similarity search
    params = {"query_vec": vector}
    # Execute the search query on Redis
    results = redis_client.ft(CHUNK_INDEX_NAME).search(q, query_params=params)
    # Extract the chunks of text from the search results
    matching_chunks = [doc.chunk for doc in results.docs]
    # Join the matching chunks to form the context
    context = "\n\n".join(matching_chunks)
    return context

def create_vector_index_summary():
    schema = [
        TagField("$.roles", as_name='roles'),
        VectorField('$.summary_embeddings', "HNSW", {
            "TYPE": 'FLOAT32',
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE"
        }, as_name='vector')
    ]

    idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['file_'])

    try:
        redis_client.ft(SUMMARY_INDEX_NAME).dropindex()
    except:
        pass

    redis_client.ft(SUMMARY_INDEX_NAME).create_index(schema, definition=idx_def)

def perform_vector_search_for_documents(query_embedding, roles):
    vector = np.array(query_embedding, dtype=np.float32).tobytes()
    role_filter = ""
    for i, role in enumerate(roles):
        if i > 0:
            role_filter += " | "
        role_filter += f"@roles:{{{role}}}"  
        # role_filter = "*"
    q = Query(f'({role_filter})=>[KNN 5 @vector $query_vec AS vector_score]')\
                .sort_by('vector_score')\
                .return_fields('vector_score')\
                .dialect(3)


    params = {"query_vec": vector}

    results = redis_client.ft(SUMMARY_INDEX_NAME).search(q, query_params=params)
    related_docs = [doc.id for doc in results.docs if float(doc.vector_score) <= 0.8]

    return related_docs

def delete_doc(key):
    return redis_client.delete(key)

def get_keys(doc_name):
    return redis_client.keys(doc_name)

def set_json(key,path,value):
    return redis_client.json().set(key, path, value)

def get_json(key):
    return redis_client.json().get(key)


def create_vector_index_cache():
    schema = [
        TagField("$.query", as_name='query'),
        TagField("$.response", as_name='response'),
        VectorField('$.query_embeddings', "HNSW", {
            "TYPE": 'FLOAT32',
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE"
        }, as_name='vector')
    ]

    idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['semcache_'])

    try:
        redis_client.ft(CACHE_INDEX_NAME).dropindex()
    except:
        pass
    redis_client.ft(CACHE_INDEX_NAME).create_index(schema, definition=idx_def)

def perform_vector_search_for_cache(query_embedding):
    vector = np.array(query_embedding, dtype=np.float32).tobytes()
    q = Query(f'(*)=>[KNN 1 @vector $query_vec AS vector_score]')\
                .sort_by('vector_score')\
                .return_fields('vector_score', 'query', 'response')\
                .dialect(2)


    params = {"query_vec": vector}

    results = redis_client.ft(CACHE_INDEX_NAME).search(q, query_params=params)
    related_queries = [doc.id for doc in results.docs if float(doc.vector_score) <= 0.5]

    return related_queries


def get_user(username):
    keyname = f"user:{username}"
    return redis_client.json().get(keyname)

def add_user(username, password, roles):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_data = {
        "password": hashed_password.decode('utf-8'),
        "roles": roles
    }
    redis_client.json().set(f"user:{username}", '.',user_data)

def check_key(key):
    return redis_client.exists(key)