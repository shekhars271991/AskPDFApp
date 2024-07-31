from app.services.redis_service import set_json

def store_chunks_in_vectorDB(doc_name, chunks, embeddings, roles):
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        key = f"chunk_{doc_name}_{i}"
        value = {
            "chunk": chunk,
            "embedding": embedding.tolist(),
            "roles": roles
        }
        set_json(key, '.', value)
   
