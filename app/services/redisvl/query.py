from redisvl.query import VectorQuery, RangeQuery
from redisvl.query.filter import Tag
from app.services.redisvl.initindex import filechunkindex, filesummaryindex, websummaryindex
from app.services.embedding_service import get_embeddings
import numpy as np
import json



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


def perform_vector_search_for_documents(query_embedding, roles):
    vector = np.array(query_embedding, dtype=np.float32).tobytes()
    t = Tag("roles") == roles
    rangequery = RangeQuery(
                vector=vector,
                vector_field_name="summary_embeddings",
                return_fields=['roles', 'original_filename'],
                filter_expression=t,
                distance_threshold=0.8
            )
    results = filesummaryindex.query(rangequery)
    related_docs = []
    for doc in results:       
        roles = json.loads(doc['roles'])
        original_filename = doc['original_filename']
        related_docs.append({
        'id': doc['id'], 
        'roles': roles[0],
        'original_filename': original_filename
        })

    return related_docs




def perform_vector_search_for_webpages(query_embedding, roles):
    vector = np.array(query_embedding, dtype=np.float32).tobytes()
    t = Tag("roles") == roles
    rangequery = RangeQuery(
                vector=vector,
                vector_field_name="summary_embeddings",
                return_fields=['roles', 'webpage_title'],
                filter_expression=t,
                distance_threshold=0.8
            )
    results = websummaryindex.query(rangequery)
    related_webpages = []
    for doc in results:       
        roles = json.loads(doc['roles'])
        webpage_title = doc['webpage_title']
        related_webpages.append({
        'id': doc['id'], 
        'roles': roles[0],
        'webpage_title': webpage_title
        })

    return related_webpages



# def perform_vector_search_for_webpages(query_embedding, roles):
#     vector = np.array(query_embedding, dtype=np.float32).tobytes()
#     role_filter = ""
#     for i, role in enumerate(roles):
#         if i > 0:
#             role_filter += " | "
#         role_filter += f"@roles:{{{role}}}"  
#         # role_filter = "*"
#     q = Query(f'({role_filter})=>[KNN 5 @vector $query_vec AS vector_score]')\
#                 .sort_by('vector_score')\
#                 .return_fields('vector_score','roles', 'webpage_title')\
#                 .dialect(4)


#     params = {"query_vec": vector}
#     results = redis_client.ft(WEBPAGE_SUMMARY_INDEX_NAME).search(q, query_params=params)

#     related_webpages = []
#     for doc in results.docs:
#         if float(doc.vector_score) <= 0.8:
#             roles = json.loads(doc.roles)
#             webpage_title = json.loads(doc.webpage_title)[0]
#             related_webpages.append({
#             'id': doc.id, 
#             'roles': roles[0],
#             'webpage_title': webpage_title
#         })
#     return related_webpages

