from redisvl.query import VectorQuery
from redisvl.query.filter import Tag
from app.services.redisvl.initindex import filechunkindex
from app.services.embedding_service import get_embeddings



def run_vector_query(query):
    t = Tag("doc_name") == "red_08ed1eca"
    q = query
    query_embedding = get_embeddings(q)

    v = VectorQuery(query_embedding,
                    "embedding",
                    return_fields=["vector_score", "roles", "original_filename"],
                    filter_expression=t)


    results = filechunkindex.query(v)
    return results
