import redis
import os
from app.services.document_service import store_file_metadata, extract_text_from_pdf, chunk_text, get_embeddings
from app.services.embedding_service import store_chunks_in_vectorDB
from app.services.file_description_service import summarize_llama

r = redis.StrictRedis(host='localhost', port=6379, db=0)

def process_upload(entry_id, data):
    try:
        doc_name = data['doc_name']
        file_path = data['file_path']
        roles = data['roles'].split(',')
        upload_time = data['upload_time']
        
        # Extract text and process the document
        text = extract_text_from_pdf(file_path)
        summary = summarize_llama(text)
        summary_embeddings = get_embeddings(summary).tolist()
        chunks = chunk_text(text)
        embeddings = get_embeddings(chunks)
        
        # Store metadata and chunks
        store_file_metadata(doc_name, data['original_filename'], upload_time, roles, summary, summary_embeddings)
        store_chunks_in_vectorDB(doc_name, chunks, embeddings, roles)

        # Remove the file after processing
        os.remove(file_path)
        
        # Acknowledge the processing of the entry
        r.xack('document_upload_stream', 'document_upload_group', entry_id)
        print(f"Processed document: {doc_name}")
        
    except Exception as e:
        print(f"Failed to process document: {str(e)}")


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

    
def consume_stream():
    stream_name = 'document_upload_stream'
    group_name = 'document_upload_group'
    consumer_name = 'document_upload_consumer'

    # Ensure stream and group are created
    create_stream_and_group(stream_name, group_name)

    while True:
        entries = r.xreadgroup(group_name, consumer_name, {stream_name: '>'}, count=1, block=100)
        if entries:
            for stream, messages in entries:
                for message in messages:
                    entry_id, data = message  # Unpacking the tuple
                    # `data` is a dictionary of field-value pairs
                    print(f"Received entry ID: {entry_id}, data: {data}")
                    
                    # Pass the data dictionary to your processing function
                    process_upload(entry_id, data)
                    
if __name__ == "__main__":
    consume_stream()
