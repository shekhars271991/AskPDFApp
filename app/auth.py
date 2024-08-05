# app/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
from app.services.redis_service import get_user, check_key, add_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = get_user(username)
    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            access_token = create_access_token(identity={ 'username':username, 'roles': user['roles']})
            return jsonify({
                'access_token': access_token,
                'roles': user['roles']  # Include roles in the response payload
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    else:
        return jsonify({"error": "User does not exist"}), 404

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    roles = data.get('roles', [])  # Default to an empty list if roles are not provided

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if check_key(f"user:{username}"):
        return jsonify({"error": "User already exists"}), 409

    # Add user with roles
    add_user(username, password, roles)

    return jsonify({"message": "User registered successfully"}), 201
