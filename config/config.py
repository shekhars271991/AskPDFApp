import os
from .secrets import REDIS_HOST, REDIS_PORT, REDIS_DB, LLAMA_API_URL, LLAMA_API_KEY, REDIS_PASSWORD

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-default-secret-key')
    REDIS_HOST = REDIS_HOST
    REDIS_PORT = REDIS_PORT
    REDIS_PASSWORD= REDIS_PASSWORD
    REDIS_DB = REDIS_DB
    LLAMA_API_URL = LLAMA_API_URL
    LLAMA_API_KEY = LLAMA_API_KEY

class DevConfig(Config):
    DEBUG = True

class ProdConfig(Config):
    DEBUG = False
