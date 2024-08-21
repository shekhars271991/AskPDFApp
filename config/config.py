import os
from .secrets import REDIS_HOST, REDIS_PORT, REDIS_DB, LLAMA_API_URL, LLAMA_API_KEY, REDIS_PASSWORD
from sentence_transformers import SentenceTransformer

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-default-secret-key')
    REDIS_HOST = REDIS_HOST
    REDIS_PORT = REDIS_PORT
    REDIS_PASSWORD= REDIS_PASSWORD
    REDIS_DB = REDIS_DB
    LLAMA_API_URL = LLAMA_API_URL
    LLAMA_API_KEY = LLAMA_API_KEY
    CHUNK_INDEX_NAME = "idxpdf"
    SUMMARY_INDEX_NAME = "idxsumm"
    CACHE_INDEX_NAME = "idxcache"
    WEBPAGE_SUMMARY_INDEX_NAME = "summidx"
    WEB_CHUNK_INDEX_NAME = "idxweb"
    MODEL= SentenceTransformer('all-MiniLM-L6-v2')

class DevConfig(Config):
    DEBUG = True

class ProdConfig(Config):
    DEBUG = False
