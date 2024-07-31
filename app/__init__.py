from flask import Flask
from flask_cors import CORS
from config import DevConfig, ProdConfig  # Import configurations
from .services.redis_service import create_vector_index  # Import the function
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_app(config_class='config.DevConfig'):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)

    # Import routes
    from app.api.routes import api_bp
    app.register_blueprint(api_bp)
    create_vector_index()

    return app
