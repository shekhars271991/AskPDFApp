import redis
from app.services.webpage_service import extract_text_from_url, get_webpage_title, store_webpage_metadata
from app.services.llama_service import summarize_llama
from app.services.DB.redis_service import store_web_chunks_in_vectorDB
from app.services.embedding_service import get_embeddings
from app.services.utility_functions_service import chunk_text, get_unique_webpagename

r = redis.StrictRedis(host='localhost', port=6379, db=0)

def process_webpage(entry_id, data):
    try:
        # Decode byte strings to regular strings
        url = data[b'url'].decode('utf-8')
        roles = data[b'roles'].decode('utf-8').split(',')
        
        # Extract text and process the webpage
        text = extract_text_from_url(url)
        webpage_summary = summarize_llama(text)
        summary_embeddings = get_embeddings(webpage_summary).tolist()
        chunks = chunk_text(text)
        embeddings = get_embeddings(chunks)
        title = get_webpage_title(text)
        unique_title = get_unique_webpagename(title)
        
        # Store metadata and chunks
        store_webpage_metadata(title, unique_title, roles, webpage_summary, summary_embeddings)
        store_web_chunks_in_vectorDB(unique_title, chunks, embeddings, url, roles)

        # Acknowledge the processing of the entry
        r.xack('webpage_indexing_stream', 'webpage_indexing_group', entry_id)
        print(f"Processed webpage: {title}")
        
    except Exception as e:
        print(f"Failed to process webpage: {str(e)}")


def create_stream_and_group(stream_name, group_name):
    try:
        # Create the stream if it doesn't exist
        if not r.exists(stream_name):
            r.xadd(stream_name, {'message': 'initial'})
        
        # Create the consumer group if it doesn't exist
        r.xgroup_create(name=stream_name, groupname=group_name, id='0', mkstream=True)
    except redis.exceptions.ResponseError as e:
        # This error occurs if the group already exists, which we can safely ignore
        if 'BUSYGROUP Consumer Group name already exists' in str(e):
            print(f"Consumer group {group_name} already exists, proceeding...")
        else:
            raise e

    
def consume_stream_web():
    stream_name = 'webpage_indexing_stream'
    group_name = 'webpage_indexing_group'
    consumer_name = 'webpage_indexing_consumer'

    # Ensure stream and group are created
    create_stream_and_group(stream_name, group_name)

    while True:
        entries = r.xreadgroup(group_name, consumer_name, {stream_name: '>'}, count=1, block=100)
        if entries:
            for stream, messages in entries:
                for message in messages:
                    entry_id, data = message  # Unpacking the tuple
                    print(f"Received entry ID: {entry_id}, data: {data}")
                    
                    # Pass the data dictionary to your processing function
                    process_webpage(entry_id, data)
                    
if __name__ == "__main__":
    consume_stream_web()
