from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import DevConfig, ProdConfig  # Import configurations
from .services.redis_service import create_vector_index_chunk, create_vector_index_summary, create_vector_index_cache
from dotenv import load_dotenv
from app.api.routes import api_bp
from app.auth import auth_bp
import os
import threading  # Import threading module
from app.services.process_document_consumer import consume_stream  

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

    # Start Redis consumer in a separate thread
    consumer_thread = threading.Thread(target=consume_stream, daemon=True)
    consumer_thread.start()

    return app
