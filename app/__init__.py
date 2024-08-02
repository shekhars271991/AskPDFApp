from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import DevConfig, ProdConfig  # Import configurations
from .services.redis_service import create_vector_index_chunk,create_vector_index_summary, create_vector_index_cache
from dotenv import load_dotenv
from app.api.routes import api_bp
from app.auth import auth_bp
import os



# Load environment variables from .env file
load_dotenv()


def create_app(config_class='config.DevConfig'):
    app = Flask(__name__)
    # app.config['JWT_SECRET_KEY'] = 'secret' 
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_secret')  # Use environment variable or default

    jwt = JWTManager(app)
    CORS(app)
    app.config.from_object(config_class)

    # Import routes
    # from app.api.routes import api_bp
    # app.register_blueprint(api_bp)



    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')

    create_vector_index_chunk()
    create_vector_index_summary()
    create_vector_index_cache()

    return app
