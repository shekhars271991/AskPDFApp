from flask import Blueprint, request, jsonify
from app.services.document_service import store_file_metadata, extract_text_from_pdf,list_uploaded_documents, chunk_text, get_unique_filename,get_context_from_similar_entries, get_docs_related_to_query
from app.services.embedding_service import get_embeddings
from app.services.classification_service import classify_task_type
from app.services.llama_service import ask_llama, summarize_llama
from app.services.redis_service import get_keys, delete_doc, store_web_chunks_in_vectorDB, set_json
from app.services.sematic_cache_service import insert_in_semantic_cache, check_sematic_cache, get_data_from_cache
import os
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.redis_service import add_to_stream
from app.services.webpage_service import extract_text_from_url, store_webpage_metadata
from app.services.webpage_service import get_webpage_title, extract_text_from_url,\
      get_unique_webpagename, get_webpages_related_to_query, get_web_context_from_similar_entries

api_bp = Blueprint('api', __name__)
UPLOAD_DIRECTORY = 'app/uploadedFiles'


@api_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask_question():
    data = request.get_json()
    query = data.get('query')
    doc_types = data.get('doc_types')
    if not doc_types:
        doc_types = ['files']
    jwt_identity = get_jwt_identity()
    username = jwt_identity.get('username')
    roles = jwt_identity.get('roles', []) + [username]
    roles = [role.strip() for role in roles]

    skip_cache = request.args.get('skip_cache', default='yes')
    # check in the semantic cache
    if(skip_cache == 'no'):
        related_queries = check_sematic_cache(query,roles)
        if(related_queries):
            resp = get_data_from_cache(related_queries[0])
            return jsonify({'answer': resp['response'], 'relatedQuery': resp['query'], 'relatedDocs':resp['related_docs'], 'fromCache': "true"})
    # doc_ids = []
    # Retrieve related documents based on the query
    if 'files' in doc_types:
        related_docs = get_docs_related_to_query(query, roles)
        # doc_ids.extend([doc_id for doc_id, _ in related_docs])

    if 'webpages' in doc_types:
        related_webpages = get_webpages_related_to_query(query, roles)
        # doc_ids.extend([doc_id for doc_id, _ in related_webpages])

    

    doc_ids = [doc_id for doc_id, _ in related_docs]
    webpage_ids = [webpage_id for webpage_id, _ in related_webpages]
    # Initialize access_level with the roles of the first document
    if related_docs:
        access_level = set(related_docs[0][1])
        # Intersect with roles of all other documents
        for _, roles in related_docs[1:]:
            access_level.intersection_update(roles)
        access_level = list(access_level)
    else:
        access_level = []
    if not related_docs:
        return jsonify({'answer': "No related documents found.", 'relatedDocs': []})

    context_doc = get_context_from_similar_entries(query, doc_ids)
    context_pdf = get_web_context_from_similar_entries(query, webpage_ids)
    answer = ask_llama(context_doc.join(context_pdf), query)

    # insert in semantic cache
    insert_in_semantic_cache(query, answer, access_level, related_docs)

    return jsonify({'answer': answer, 'relatedDocs': related_docs})

@api_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    jwt_identity = get_jwt_identity()
    username = jwt_identity.get('username', "")
    if(username == ""):
        return jsonify({'error': 'missing username from auth token'}), 403
    caller_roles = jwt_identity.get('roles', []) #check if he is admin
    if 'admin' not in caller_roles:
        roles = [username]
    else:    
        roles_string = request.form.get('roles')
        if roles_string is None or roles_string == "":
            return jsonify({'error': 'missing roles for the doc'}), 403
        roles = roles_string.split(',')  
        roles = [role.strip() for role in roles]

        if not isinstance(roles, list):
            return jsonify({'error': 'Roles should be provided as form input'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        # Generate a unique filename
        unique_filename = get_unique_filename(file.filename)
        file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)
        file.save(file_path)
        try:
            doc_name = os.path.splitext(unique_filename)[0]
            upload_time = datetime.now().isoformat()

            # Add to Redis stream for asynchronous processing
            task_data = {
                'doc_name': doc_name,
                'original_filename': file.filename,
                'file_path': file_path,
                'upload_time': upload_time,
                'roles': ','.join(roles)
            }
            add_to_stream('document_upload_stream', task_data)
            return jsonify({'message': 'Document enqueued for processing'}), 200

        except Exception as e:
            return jsonify({'error': f'Failed to enqueue document: {str(e)}'}), 500

@api_bp.route('/documents', methods=['GET'])
@jwt_required()
def get_uploaded_documents():
    jwt_identity = get_jwt_identity()
    username = jwt_identity.get('username', "")
    roles = jwt_identity.get('roles', []) + [username]
    documents = list_uploaded_documents(roles)
    return jsonify({'documents': documents})

@api_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_document():
    data = request.get_json()
    doc_name = data.get('doc_name')

    if not doc_name:
        return jsonify({'error': 'Missing document name'}), 400
    try:
        # Delete file from filesystem
        file_path = os.path.join(UPLOAD_DIRECTORY, f"{doc_name}.pdf")
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            return jsonify({'error': 'File not found in filesystem'}), 404
        # Delete metadata from Redis
        metadata_key = f"file_{doc_name}_metadata"
        delete_doc(metadata_key)
        # Delete chunks from Redis
        chunk_keys = get_keys(f"chunk_{doc_name}_*")
        for key in chunk_keys:
            delete_doc(key)
        return jsonify({'message': f'Document {doc_name} deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to delete document: {str(e)}'}), 500

@api_bp.route('/index_webpage', methods=['POST'])
@jwt_required()
def fetch_html():
    jwt_identity = get_jwt_identity()
    data = request.get_json()
    url = data.get('url')
    caller_roles = jwt_identity.get('roles', []) #check if he is admin

    if not url:
        return jsonify({'error': 'Missing URL in request body'}), 400
    text = extract_text_from_url(url)
    webpagesummary = summarize_llama(text)
    web_summary_embeddings = get_embeddings(webpagesummary).tolist()
    title = get_webpage_title(text)
    chunks = chunk_text(text)
    embeddings = get_embeddings(chunks)
    unique_title = get_unique_webpagename(title)
    store_webpage_metadata(title, unique_title, caller_roles, webpagesummary, web_summary_embeddings)
    store_web_chunks_in_vectorDB(unique_title, chunks, embeddings,url, caller_roles)

    return jsonify({'title': title, 'response': "uploaded successfully"}), 200
