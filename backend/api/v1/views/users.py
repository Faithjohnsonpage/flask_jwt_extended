#!/usr/bin/env python3
"""Users API for Sentinel OSINT with JWT Authentication and Redis Blacklisting"""
import os
import uuid
import imghdr
import logging
from datetime import timedelta
from flask import request, jsonify, url_for, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt
)
from PIL import Image
from models.user import User
from models import storage
from api.v1.views import app_views

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('users.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

UPLOAD_FOLDER = 'api/v1/uploads/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1000 * 1000


def allowed_file_type(file):
    file_type = imghdr.what(file)
    return file_type in ALLOWED_EXTENSIONS


@app_views.route('/auth/register', methods=['POST'], strict_slashes=False)
def register():
    """Register a new user"""
    # Handle both form data and JSON
    if request.is_json:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
    else:
        data = request.form.to_dict()
        if not data:
            return jsonify({"error": "No form data provided"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        logger.warning("Missing registration fields")
        return jsonify({"error": "Missing fields"}), 400

    if len(username) < 3 or len(username) > 30:
        return jsonify({"error": "Username must be between 3 and 30 characters"}), 400

    if storage.exists(User, email=email):
        return jsonify({"error": "Email already registered"}), 400

    if storage.filter_by(User, username=username):
        return jsonify({"error": "Username already exists"}), 400

    # Create and save the new user
    user = User()
    user.username = username
    user.email = email
    user.password = password
    storage.new(user)
    storage.save()

    logger.info(f"New user registered: {username}")
    return jsonify({"message": "User registered successfully", "userId": user.id}), 201


@app_views.route('/auth/login', methods=['POST'], strict_slashes=False)
def login():
    """Authenticate a user and issue JWT tokens"""
    # Handle both form data and JSON
    if request.is_json:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
    else:
        data = request.form.to_dict()
        if not data:
            return jsonify({"error": "No form data provided"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    user = storage.filter_by(User, email=email)
    if not user or not user.verify_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Add fresh token for sensitive operations
    access_token = create_access_token(identity=user.id, fresh=True)
    refresh_token = create_refresh_token(identity=user.id)

    logger.info(f"User {user.id} logged in successfully")
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200


@app_views.route('/auth/token/refresh', methods=['POST'], strict_slashes=False)
@jwt_required(refresh=True)
def refresh_token():
    """Refresh the access token"""
    identity = get_jwt_identity()
    # Non-fresh token for refresh
    access_token = create_access_token(identity=identity, fresh=False)
    return jsonify({"access_token": access_token}), 200


@app_views.route('/auth/logout', methods=['POST'], strict_slashes=False)
@jwt_required()
def logout():
    """Logout user and revoke current token"""
    jti = get_jwt()['jti']
    token_type = get_jwt()['type']

    # Use the helper function from the main app to revoke token
    current_app.revoke_token(jti, token_type)

    logger.info(f"User {get_jwt_identity()} logged out - {token_type} token revoked")
    return jsonify({"message": "Successfully logged out"}), 200


@app_views.route('/users/me', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_profile():
    """Return authenticated user's profile"""
    user_id = get_jwt_identity()
    user = storage.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "profile_picture_url": user.profile_picture_url
    }), 200


@app_views.route('/users/me', methods=['PUT'], strict_slashes=False)
@jwt_required()
def update_profile():
    """Update user's username"""
    user_id = get_jwt_identity()
    user = storage.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    new_username = data.get("username")

    if not new_username:
        return jsonify({"error": "Username required"}), 400

    if len(new_username) < 3 or len(new_username) > 30:
        return jsonify({"error": "Username must be between 3 and 30 characters"}), 400

    if storage.filter_by(User, username=new_username):
        return jsonify({"error": "Username already taken"}), 400

    user.username = new_username
    storage.save()
    return jsonify({"message": "Profile updated successfully"}), 200


@app_views.route('/users/me/password', methods=['PUT'], strict_slashes=False)
@jwt_required(fresh=True)  # Require fresh token for password change
def change_password():
    """Change user's password (requires fresh token)"""
    user_id = get_jwt_identity()
    user = storage.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    current_password = data.get("current_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not all([current_password, new_password, confirm_password]):
        return jsonify({"error": "All password fields are required"}), 400

    if not user.verify_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "New passwords do not match"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    user.password = new_password
    storage.save()

    logger.info(f"User {user_id} changed their password")
    return jsonify({"message": "Password changed successfully"}), 200


@app_views.route('/users/me/profile-picture', methods=['POST'], strict_slashes=False)
@jwt_required()
def update_profile_picture():
    """Upload and update profile picture"""
    user_id = get_jwt_identity()
    user = storage.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    file = request.files.get('file')

    if not file or not allowed_file_type(file):
        return jsonify({"error": "Invalid or missing file"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    path = os.path.join(UPLOAD_FOLDER, f"{user_id}_profile{ext}")
    file.save(path)

    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_thumbnail{ext}")
    try:
        image = Image.open(path)
        image.thumbnail((100, 100))
        image.save(thumbnail_path)
    except Exception as e:
        logger.error(f"Failed to process image: {e}")
        return jsonify({"error": "Image processing failed"}), 500

    user.profile_picture_url = thumbnail_path
    storage.save()

    return jsonify({"message": "Profile picture updated successfully"}), 200


@app_views.route('/users/<string:user_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required(fresh=True)  # Require fresh token for account deletion
def delete_user(user_id):
    """Delete a user account"""
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({"error": "Unauthorized to delete this user"}), 403

    user = storage.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Revoke current token before deleting user
    jti = get_jwt()['jti']
    token_type = get_jwt()['type']
    current_app.revoke_token(jti, token_type)

    storage.delete(user)
    storage.save()

    logger.info(f"User {user_id} deleted their account")
    return jsonify({"message": f"User {user_id} deleted successfully"}), 200


@app_views.route('/auth/reset-password', methods=['POST'], strict_slashes=False)
def request_password_reset():
    """Request a password reset by email"""
    # Handle both form data and JSON
    if request.is_json:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
    else:
        data = request.form.to_dict()
        if not data:
            return jsonify({"error": "No form data provided"}), 400

    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = storage.filter_by(User, email=email)
    if not user:
        logger.warning(f"Password reset requested for unknown email: {email}")
        return jsonify({"error": "User not found"}), 404

    # Generate token and store it
    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    storage.save()

    logger.info(f"Password reset token generated for user {user.id}")

    return jsonify({
        "message": "Password reset token generated",
        "reset_token": reset_token,
        "_links": {
            "reset": {
                "href": url_for("app_views.reset_password_with_token", _external=True)
            }
        }
    }), 200


@app_views.route('/auth/reset-password/confirm', methods=['POST'], strict_slashes=False)
def reset_password_with_token():
    """Reset password using a reset token"""
    # Handle both form data and JSON
    if request.is_json:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
    else:
        data = request.form.to_dict()
        if not data:
            return jsonify({"error": "No form data provided"}), 400

    token = data.get("token")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not token or not new_password or not confirm_password:
        return jsonify({"error": "Missing fields"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    user = storage.filter_by(User, reset_token=token)
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 400

    try:
        user.password = new_password  # will be hashed by property setter
        user.reset_token = None
        storage.save()
        logger.info(f"User {user.id} successfully reset their password.")
    except Exception as e:
        logger.error(f"Failed to reset password for user: {str(e)}")
        return jsonify({"error": "Failed to update password"}), 500

    return jsonify({
        "message": "Password reset successfully",
        "_links": {
            "login": {"href": url_for("app_views.login", _external=True)}
        }
    }), 200


@app_views.route('/auth/verify-token', methods=['GET'], strict_slashes=False)
@jwt_required()
def verify_token():
    """Verify if the current token is valid"""
    user_id = get_jwt_identity()
    user = storage.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    jwt_claims = get_jwt()

    return jsonify({
        "valid": True,
        "user_id": user_id,
        "token_type": jwt_claims.get('type'),
        "fresh": jwt_claims.get('fresh', False),
        "jti": jwt_claims.get('jti')
    }), 200


@app_views.route('/auth/token-status', methods=['GET'], strict_slashes=False)
@jwt_required()
def token_status():
    """Get detailed token status information"""
    jwt_claims = get_jwt()
    user_id = get_jwt_identity()

    # Check if token is blacklisted
    jti = jwt_claims.get('jti')
    is_blacklisted = current_app.jwt_redis_blocklist.get(jti) is not None

    return jsonify({
        "user_id": user_id,
        "token_type": jwt_claims.get('type'),
        "fresh": jwt_claims.get('fresh', False),
        "jti": jti,
        "is_blacklisted": is_blacklisted,
        "issued_at": jwt_claims.get('iat'),
        "expires_at": jwt_claims.get('exp')
    }), 200
