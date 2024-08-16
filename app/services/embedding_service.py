from app.services.redis_service import set_json
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embeddings(chunks):
    embeddings = model.encode(chunks)
    return embeddings
