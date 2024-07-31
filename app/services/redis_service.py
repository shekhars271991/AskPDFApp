import numpy as np
from redis.commands.search.query import Query
from redis.commands.search.field import TextField, VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from sentence_transformers import SentenceTransformer
import redis

from config.config import Config
import redis

redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB
)

# Your existing code for Redis interactions


CHUNK_INDEX_NAME = "idxpdf"
SUMMARY_INDEX_NAME = "idxsumm"
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

def perform_vector_search_for_chunks(query_embedding, role, related_docs):
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


def perform_vector_search_for_documents(query_embedding):
    vector = np.array(query_embedding, dtype=np.float32).tobytes()
    q = Query(f'(*)=>[KNN 2 @vector $query_vec AS vector_score]')\
                .sort_by('vector_score')\
                .return_fields('vector_score', 'unique_filename', 'original_filename')\
                .dialect(2)


    params = {"query_vec": vector}

    results = redis_client.ft(SUMMARY_INDEX_NAME).search(q, query_params=params)
    related_docs = [doc.id for doc in results.docs if float(doc.vector_score) <= 0.8]

    return related_docs



def create_vector_index_summary():
    schema = [
        TagField("$.original_filename", as_name='original_filename'),
        TagField("$.unique_filename", as_name='unique_filename'),
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

def delete_doc(key):
    return redis_client.delete(key)

def get_keys(doc_name):
    return redis_client.keys(doc_name)

def set_json(key,path,value):
    return redis_client.json().set(key, path, value)

def get_json(key):
    return redis_client.json().get(key)