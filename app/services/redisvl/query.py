from redisvl.query import VectorQuery, RangeQuery, FilterQuery
from redisvl.query.filter import Tag
from app.services.redisvl.initindex import filechunkindex, filesummaryindex, websummaryindex, webchunkindex
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


def perform_vector_search_for_chunks(query_embedding, related_docs):
    vector = np.array(query_embedding, dtype=np.float32).tobytes()
    t = Tag("doc_name") == related_docs
    rangequery = RangeQuery(
                vector=vector,
                vector_field_name="embedding",
                return_fields=['chunk'],
                filter_expression=t,
                distance_threshold=0.8
            )
    results = filechunkindex.query(rangequery)
    matching_chunks = []
    # Extract the chunks of text from the search results
    matching_chunks = [doc['chunk'] for doc in results]
    # Join the matching chunks to form the context
    context = "\n\n".join(matching_chunks)
    return context

def perform_vector_search_for_web_chunks(query_embedding, related_webpage_titles):
    vector = np.array(query_embedding, dtype=np.float32).tobytes()
    t = Tag("webpage_title") == related_webpage_titles
    rangequery = RangeQuery(
                vector=vector,
                vector_field_name="embedding",
                return_fields=['chunk'],
                filter_expression=t,
                distance_threshold=0.8
            )
    results = webchunkindex.query(rangequery)
    matching_chunks = []
    # Extract the chunks of text from the search results
    matching_chunks = [doc['chunk'] for doc in results]
    # Join the matching chunks to form the context
    context = "\n\n".join(matching_chunks)
    return context



def get_user_webpages(roles):
    role_filter = Tag("roles") == roles
    filter_query = FilterQuery(
                    filter_expression=role_filter
                    )
    results = websummaryindex.query(filter_query)
    user_webpages = []
    for doc in results:
        # doc_data = json.loads(doc.json)[0]
        user_webpages.append({'id': doc['id'], 'unique_title':doc["unique_title"], 'webpage_title': doc["webpage_title"], 'roles': doc["roles"], 'summary': doc["summary"], 'url': doc['url'] })

    return user_webpages

    # role_filter = ""
    # for i, role in enumerate(roles):
    #     if i > 0:
    #         role_filter += " | "
    #     role_filter += f"@roles:{{{role}}}"  

    # q = Query(f'{role_filter}')\
    #             .dialect(4)
    # results = redis_client.ft(WEBPAGE_SUMMARY_INDEX_NAME).search(q)
    # user_webpages = []
    # for doc in results.docs:
    #     doc_data = json.loads(doc.json)[0]
    #     user_webpages.append({'id': doc.id, 'unique_title':doc_data["unique_title"], 'webpage_title': doc_data["webpage_title"], 'roles': doc_data["roles"], 'summary': doc_data["summary"] })

    # return user_webpages




