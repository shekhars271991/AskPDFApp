from flask import Blueprint, request, jsonify
from app.services.document_service import store_file_metadata, extract_text_from_pdf,list_uploaded_documents, chunk_text, get_unique_filename,get_context_from_similar_entries, get_docs_related_to_query
from app.services.embedding_service import store_chunks_in_vectorDB, get_embeddings
from app.services.classification_service import classify_task_type
from app.services.llama_service import ask_llama
from app.services.redis_service import get_keys, delete_doc
from app.services.file_description_service import summarize_llama
import os
from datetime import datetime


api_bp = Blueprint('api', __name__)
UPLOAD_DIRECTORY = 'app/uploadedFiles'


@api_bp.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    query = data['query']
    role = data['role']


    # before then get the relatable docs
    related_docs = get_docs_related_to_query(query)

    context = get_context_from_similar_entries(query, role, related_docs)
    answer = ask_llama(context,query)

    return jsonify({'answer': answer})


@api_bp.route('/upload', methods=['POST'])
def upload_file():
    roles_string = request.form.get('roles')
    roles = roles_string.split(',')
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

        # Process the PDF
        try:
            doc_name = os.path.splitext(unique_filename)[0]
            upload_time = datetime.now().isoformat()

            text = extract_text_from_pdf(file_path)
            chunks = chunk_text(text)
            embeddings = get_embeddings(chunks)

            # get doc summary
            summary = summarize_llama(text)
            summary_embeddings = get_embeddings(summary).tolist()
            store_file_metadata(doc_name, file.filename, upload_time, roles, summary, summary_embeddings)

            store_chunks_in_vectorDB(doc_name, chunks, embeddings, roles)
            
            return jsonify({'message': 'Document processed and embeddings stored in Redis'}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to process document: {str(e)}'}), 500

@api_bp.route('/documents', methods=['GET'])
def get_uploaded_documents():
    documents = list_uploaded_documents()
    return jsonify({'documents': documents})

@api_bp.route('/delete', methods=['DELETE'])
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
