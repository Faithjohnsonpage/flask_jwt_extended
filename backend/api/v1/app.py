#!/usr/bin/python3
"""Flask Application with Redis JWT Token Blacklisting"""
import os
import redis
from datetime import timedelta

from api.v1.views import app_views
from flask import Flask, jsonify
from flask_caching import Cache
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import storage

app = Flask(__name__)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    hours=1
)  # Access token expires in 1 hour
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
    days=30
)  # Refresh token expires in 30 days
app.config["JWT_ALGORITHM"] = "HS256"
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_IDENTITY_CLAIM"] = "user_id"

# Initialize JWT Manager
jwt = JWTManager(app)

# Configure cache (Using Redis as a caching backend)
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_HOST"] = "localhost"
app.config["CACHE_REDIS_PORT"] = 6379
app.config["CACHE_DEFAULT_TIMEOUT"] = 300
cache = Cache(app)
app.cache = cache

# Setup Redis connection for JWT blacklisting (separate from cache)
# Use a different Redis database to avoid conflicts with cache
jwt_redis_blocklist = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("JWT_REDIS_DB", 2)),  # Use db=2 for JWT blacklist
    decode_responses=True
)

# Rate limiter setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379/1"),
)
app.limiter = limiter

# Make Redis blocklist available to the app
app.jwt_redis_blocklist = jwt_redis_blocklist


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """
    Check if a JWT token has been revoked/blacklisted
    Uses Redis directly for better performance and consistency
    """
    jti = jwt_payload["jti"]
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    """
    Callback function for when a revoked token is used
    """
    return jsonify({"error": "Token has been revoked"}), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """
    Callback function for when an expired token is used
    """
    return jsonify({"error": "Token has expired"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    """
    Callback function for when an invalid token is used
    """
    return jsonify({"error": "Invalid token"}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """
    Callback function for when no token is provided
    """
    return jsonify({"error": "Authorization token is required"}), 401


# Helper function to revoke tokens
def revoke_token(jti, token_type="access"):
    """
    Revoke a token by adding it to the Redis blacklist
    """
    # Set TTL based on token type
    if token_type == "refresh":
        ttl = int(app.config["JWT_REFRESH_TOKEN_EXPIRES"].total_seconds())
    else:
        ttl = int(app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())

    # Add token to blacklist with appropriate TTL
    jwt_redis_blocklist.set(jti, "", ex=ttl)


# Make helper function available to the app
app.revoke_token = revoke_token

# Register blueprint for routing
app.register_blueprint(app_views)

# Enable Cross-Origin Resource Sharing (CORS)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.teardown_appcontext
def close_db(error: Exception = None) -> None:
    """Close Storage at the end of the request"""
    storage.close()


@app.errorhandler(404)
def not_found(error: Exception) -> str:
    """Handle 404 errors (Resource Not Found)"""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(401)
def unauthorized(error: Exception) -> str:
    """Handle 401 errors (Unauthorized access)"""
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(403)
def forbidden(error: Exception) -> str:
    """Handle 403 errors (Forbidden access)"""
    return jsonify({"error": "Forbidden"}), 403


# Health check endpoint to verify Redis connection
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        jwt_redis_blocklist.ping()
        cache_status = "connected"
    except Exception as e:
        cache_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy",
        "redis_blacklist": cache_status,
        "version": "1.0.0"
    }), 200


# Run the Flask app
if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = os.getenv("API_PORT", "5000")
    app.run(host=host, port=port)
