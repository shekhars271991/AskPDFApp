from flask import Blueprint, request, jsonify
from app.services.document_service import list_uploaded_documents,get_context_from_similar_entries, get_docs_related_to_query
from app.services.llama_service import ask_llama
from app.services.redis_service import get_keys, delete_doc
from app.services.sematic_cache_service import insert_in_semantic_cache, check_sematic_cache, get_data_from_cache
import os
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.redis_service import add_to_stream
from app.services.webpage_service import get_webpages_related_to_query, get_web_context_from_similar_entries, get_allowed_domains
from app.services.utility_functions_service import get_unique_filename
from app.services.webpage_service import get_urls, list_indexed_webpages

api_bp = Blueprint('api', __name__)
UPLOAD_DIRECTORY = 'app/uploadedFiles'
MAX_URLS = 50

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
        related_queries = check_sematic_cache(query, roles)
        if(related_queries):
            resp = get_data_from_cache(related_queries[0])
            return jsonify({
                'answer': resp['response'],
                'relatedQuery': resp['query'],
                'relatedDocs': resp['related_docs'],
                'relatedWebpages': resp['related_webpages'],
                'fromCache': "true"
            })

    related_docs = []
    related_webpages = []

    if 'files' in doc_types:
        related_docs = get_docs_related_to_query(query, roles)

    if 'webpages' in doc_types:
        related_webpages = get_webpages_related_to_query(query, roles)

    context_doc = ""
    context_web = ""
    if related_docs:
        access_level = set(related_docs[0][1])
        # Intersect with roles of all other documents
        for _, roles in related_docs[1:]:
            access_level.intersection_update(roles)
        access_level = list(access_level)
    else:
        access_level = []
        
    if not related_docs and not related_webpages:
        return jsonify({'answer': "No related documents or webpages found.", 'relatedDocs': []})

    if related_docs:
        context_doc = get_context_from_similar_entries(query, [doc[0] for doc in related_docs])
    
    if related_webpages:
        context_web = get_web_context_from_similar_entries(query, [webpage[0] for webpage in related_webpages])
    
    context = context_doc + "\n\n" + context_web
    answer = ask_llama(context, query)
    access_level.append(username)

    # Combine related webpages and titles
    related_webpages_combined = [
        {
            "id": webpage_id,
            "roles": roles,
            "title": webpage_title
        }
        for (webpage_id, roles, webpage_title) in related_webpages
    ]

    # Combine related docs and filenames
    related_docs_combined = [
        {
            "id": doc_id,
            "roles": roles,
            "filename": doc_filename
        }
        for (doc_id, roles, doc_filename) in related_docs
    ]

    # insert in semantic cache
    insert_in_semantic_cache(query, answer, access_level, related_docs_combined, related_webpages_combined)

    return jsonify({
        'answer': answer,
        'relatedDocs': related_docs_combined,
        'relatedWebpages': related_webpages_combined
    })

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

DEFAULT_MAX_COUNT = 20
@api_bp.route('/index_webpage', methods=['POST'])
@jwt_required()
def fetch_html():
    jwt_identity = get_jwt_identity()
    data = request.get_json()
    url = data.get('url')
    level = data.get('level')
    maxcount = data.get('maxcount')
    if not maxcount:
        maxcount = DEFAULT_MAX_COUNT
    if level is None:
        level = 0
    allowed_domains = data.get('allowed_domains')
    if not url:
        return jsonify({'error': 'Missing URL in request body'}), 400
    
    # If allowed_domains is not provided, extract the domain from the main URL
    allowed_domains_updated = get_allowed_domains(allowed_domains, url)
    if allowed_domains_updated == 'error':
        return jsonify({'error': 'Malformed URL'}), 400
  
    
    caller_roles = jwt_identity.get('roles', [])  # Check if user is admin
    
    try:
        # Fetch reachable and unreachable URLs
        reachable_urls, unreachable_urls = get_urls(url, allowed_domains_updated, level,MAX_URLS)

        # Add only reachable URLs to the stream
        for reachable_url in reachable_urls:
            task_data = {
                'url': reachable_url,
                'roles': ','.join(caller_roles)
            }
            add_to_stream('webpage_indexing_stream', task_data)

        # Return response with both reachable and unreachable URLs
        return jsonify({
            'message': 'Webpage enqueued for processing',
            'enqued_for_indexing': list(reachable_urls),
            'unreachable_urls': list(unreachable_urls)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to enqueue webpage: {str(e)}'}), 500

@api_bp.route('/webpages', methods=['GET'])
@jwt_required()
def get_indexed_documents():
    jwt_identity = get_jwt_identity()
    username = jwt_identity.get('username', "")
    roles = jwt_identity.get('roles', []) + [username]
    webpages = list_indexed_webpages(roles)
    return jsonify({'indexed_webpages': webpages})