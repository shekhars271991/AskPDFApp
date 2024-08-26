from redisvl.index import SearchIndex
import redis

CHUNK_INDEX_NAME = "idxpdfchunk"
SUMMARY_INDEX_NAME = "idxpdfsumm"
CACHE_INDEX_NAME = "idxcache"
WEBPAGE_SUMMARY_INDEX_NAME = "idxwebsumm"
WEB_CHUNK_INDEX_NAME = "idxwebchunk"


REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD= ""

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD
)


# MODEL= SentenceTransformer('all-MiniLM-L6-v2')
file_summary_schema = {
    "index": {
        "name": SUMMARY_INDEX_NAME,
        "prefix": "file_",
        "storage_type": "json",
    },
    "fields": [
        {"name": "roles", "type": "tag"},
        {"name": "original_filename", "type": "tag"},
        {
            "name": "summary_embeddings",
            "type": "vector",
            "attrs": {
                "dims": 384,
                "distance_metric": "cosine",
                "algorithm": "HNSW",
                "datatype": "float32"
            }

        }
    ],
}
file_chunk_schema = {
    "index": {
        "name": CHUNK_INDEX_NAME,
        "prefix": "chunk_",
        "storage_type": "json",
    },
    "fields": [
        {"name": "chunk", "type": "tag"},
        {"name": "roles", "type": "tag"},
        {"name": "doc_name", "type": "tag"},
        {
            "name": "embedding",
            "type": "vector",
            "attrs": {
                "dims": 384,
                "distance_metric": "cosine",
                "algorithm": "HNSW",
                "datatype": "float32"
            }

        }
    ],
}
web_chunk_schema = {
    "index": {
        "name": WEB_CHUNK_INDEX_NAME,
        "prefix": "webchunk_",
        "storage_type": "json",
    },
    "fields": [
        {"name": "chunk", "type": "tag"},
        {"name": "roles", "type": "tag"},
        {"name": "webpage_title", "type": "text"},
        {
            "name": "embedding",
            "type": "vector",
            "attrs": {
                "dims": 384,
                "distance_metric": "cosine",
                "algorithm": "HNSW",
                "datatype": "float32"
            }

        }
    ],
}
web_summary_schema = {
    "index": {
        "name": WEBPAGE_SUMMARY_INDEX_NAME,
        "prefix": "webpage_",
        "storage_type": "json",
    },
    "fields": [
        {"name": "roles", "type": "tag"},
        {"name": "webpage_title", "type": "tag"},
        {
            "name": "summary_embeddings",
            "type": "vector",
            "attrs": {
                "dims": 384,
                "distance_metric": "cosine",
                "algorithm": "HNSW",
                "datatype": "float32"
            }

        }
    ],
}



webchunkindex = SearchIndex.from_dict(web_chunk_schema)
websummaryindex = SearchIndex.from_dict(web_summary_schema)

filechunkindex = SearchIndex.from_dict(file_chunk_schema)
filesummaryindex = SearchIndex.from_dict(file_summary_schema)


for index in [filechunkindex, filesummaryindex, webchunkindex, websummaryindex]:
    index.set_client(redis_client)
