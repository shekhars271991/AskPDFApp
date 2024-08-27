from app.services.redisvl.initindex import llmcache
from redisvl.query.filter import Tag

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
