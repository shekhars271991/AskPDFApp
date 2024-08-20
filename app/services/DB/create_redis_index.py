from redis.commands.search.query import Query
from redis.commands.search.field import TextField, VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
import redis
from config.config import Config

redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    password=Config.REDIS_PASSWORD
)

CHUNK_INDEX_NAME = Config.CHUNK_INDEX_NAME
SUMMARY_INDEX_NAME = Config.SUMMARY_INDEX_NAME
CACHE_INDEX_NAME = Config.CACHE_INDEX_NAME
WEBPAGE_SUMMARY_INDEX_NAME = Config.WEBPAGE_SUMMARY_INDEX_NAME
WEB_CHUNK_INDEX_NAME = Config.WEB_CHUNK_INDEX_NAME



def create_vector_index_web_summary():
    schema = [
        TagField("$.roles", as_name='roles'),
        TagField("$.webpage_title", as_name='webpage_title'),
        VectorField('$.summary_embeddings', "HNSW", {
            "TYPE": 'FLOAT32',
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE"
        }, as_name='vector')
    ]

    idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['webpage_'])

    try:
        redis_client.ft(WEBPAGE_SUMMARY_INDEX_NAME).dropindex()
    except:
        pass
    redis_client.ft(WEBPAGE_SUMMARY_INDEX_NAME).create_index(schema, definition=idx_def)

def create_vector_index_web_chunk():
    schema = [
        TextField("$.chunk", as_name='chunk'),
        TextField("$.roles", as_name='roles'),
        TextField('$.webpage_title', as_name='webpage_title'),
        VectorField('$.embedding', "HNSW", {
            "TYPE": 'FLOAT32',
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE"
        }, as_name='vector')
    ]

    idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['webchunk_'])

    try:
        redis_client.ft(WEB_CHUNK_INDEX_NAME).dropindex()
    except:
        pass
    redis_client.ft(WEB_CHUNK_INDEX_NAME).create_index(schema, definition=idx_def)


def create_vector_index_summary():
    schema = [
        TagField("$.roles", as_name='roles'),
        TagField("$.original_filename", as_name='original_filename'),
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



def create_vector_index_cache():
    schema = [
        TagField("$.roles", as_name='roles'),
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

