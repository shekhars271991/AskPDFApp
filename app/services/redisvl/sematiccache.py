from app.services.redisvl.initindex import llmcache
from redisvl.query.filter import Tag



# def perform_vector_search_for_cache(query_embedding,roles):
#     role_filter = ""
#     for i, role in enumerate(roles):
#         if i > 0:
#             role_filter += " | "
#         role_filter += f"@roles:{{{role}}}" 
#     vector = np.array(query_embedding, dtype=np.float32).tobytes()
#     q = Query(f'({role_filter})=>[KNN 1 @vector $query_vec AS vector_score]')\
#                 .sort_by('vector_score')\
#                 .return_fields('vector_score', 'query', 'response')\
#                 .dialect(4)


#     params = {"query_vec": vector}

#     results = redis_client.ft(CACHE_INDEX_NAME).search(q, query_params=params)
#     related_queries = [doc.id for doc in results.docs if float(doc.vector_score) <= 0.5]

#     return related_queries


# if response := llmcache.check(prompt=question):
#     print(response)
# else:
#     print("Empty cache")

def insert_in_semantic_cache(query, response, access_level, related_docs, related_webpages):
    roles_separated_string = ', '.join(access_level)
    llmcache.store(
        prompt=query,
        response=response,
        filters={"roles": roles_separated_string},
        metadata={"related_docs": related_docs, "related_webpages": related_webpages}
    )
def perform_vector_search_for_cache(query,roles):
    role_filter = Tag("roles") == roles
    response = llmcache.check(
        prompt=query,
        filter_expression=role_filter,
        num_results=2
        )
    return response

#     role_filter = ""
#     for i, role in enumerate(roles):
#         if i > 0:
#             role_filter += " | "
#         role_filter += f"@roles:{{{role}}}" 
#     vector = np.array(query_embedding, dtype=np.float32).tobytes()
#     q = Query(f'({role_filter})=>[KNN 1 @vector $query_vec AS vector_score]')\
#                 .sort_by('vector_score')\
#                 .return_fields('vector_score', 'query', 'response')\
#                 .dialect(4)


#     params = {"query_vec": vector}

#     results = redis_client.ft(CACHE_INDEX_NAME).search(q, query_params=params)
#     related_queries = [doc.id for doc in results.docs if float(doc.vector_score) <= 0.5]

#     return related_queries


# if response := llmcache.check(prompt=question):
#     print(response)
# else:
#     print("Empty cache")