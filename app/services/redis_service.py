import numpy as np
from redis.commands.search.query import Query
from redis.commands.search.field import TextField, VectorField
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


INDEX_NAME = "idxpdf"
model = SentenceTransformer('all-MiniLM-L6-v2')



def search_similar_chunks(query, role):
    query_embedding = model.encode(query)
    vector = np.array(query_embedding, dtype=np.float32).tobytes()

    q = Query(f'(@roles:{role} | public)=>[KNN 3 @vector $query_vec AS vector_score]')\
                .sort_by('vector_score')\
                .return_fields('vector_score', 'chunk')\
                .dialect(3)

    params = {"query_vec": vector}

    results = redis_client.ft(INDEX_NAME).search(q, query_params=params)

    matching_chunks = [doc.chunk for doc in results.docs]
    context = "\n\n".join(matching_chunks)
    return context

def create_vector_index():
    schema = [
        TextField("$.chunk", as_name='chunk'),
        TextField("$.roles", as_name='roles'),
        VectorField('$.embedding', "HNSW", {
            "TYPE": 'FLOAT32',
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE"
        }, as_name='vector')
    ]

    idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['chunk_'])

    try:
        redis_client.ft(INDEX_NAME).dropindex()
    except:
        pass

    redis_client.ft(INDEX_NAME).create_index(schema, definition=idx_def)

def delete_doc(key):
    return redis_client.delete(key)

def get_keys(doc_name):
    return redis_client.keys(doc_name)

def set_json(key,path,value):
    return redis_client.json().set(key, path, value)

def get_json(key):
    return redis_client.json().get(key)