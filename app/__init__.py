from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import DevConfig, ProdConfig  # Import configurations
from app.services.DB.create_redis_index import create_vector_index_chunk, create_vector_index_summary, \
    create_vector_index_cache, create_vector_index_web_chunk, create_vector_index_web_summary
from dotenv import load_dotenv
from app.api.routes import api_bp
from app.auth import auth_bp
import os
import threading  # Import threading module
from app.services.process_document_consumer import consume_stream_doc
from app.services.process_webpages_consumer import consume_stream_web

# Load environment variables from .env file
load_dotenv()

def create_app(config_class='config.DevConfig'):
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_secret')  # Use environment variable or default

    jwt = JWTManager(app)
    CORS(app)
    app.config.from_object(config_class)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create vector indexes
    create_vector_index_chunk()
    create_vector_index_summary()
    create_vector_index_cache()
    create_vector_index_web_summary()
    create_vector_index_web_chunk()

    # Start doc Redis consumer in a separate thread
    doc_consumer_thread = threading.Thread(target=consume_stream_doc, daemon=True)
    doc_consumer_thread.start()

    web_consumer_thread = threading.Thread(target=consume_stream_web, daemon=True)
    web_consumer_thread.start()


    return app
