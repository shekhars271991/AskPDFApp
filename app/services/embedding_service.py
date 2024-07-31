from app.services.redis_service import set_json
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embeddings(chunks):
    embeddings = model.encode(chunks)
    return embeddings

def store_chunks_in_vectorDB(doc_name, chunks, embeddings, roles):
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        key = f"chunk_{doc_name}_{i}"
        value = {
            "chunk": chunk,
            "doc_name":doc_name,
            "embedding": embedding.tolist(),
            "roles": roles
        }
        set_json(key, '.', value)
   
