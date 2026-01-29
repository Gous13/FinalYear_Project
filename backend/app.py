"""
SynapseLink Backend - Main Application Entry Point
Flask API server for intelligent student collaboration and peer matching
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from extensions import db
import os

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }})
    jwt = JWTManager(app)
    db.init_app(app)
    
    # Configure JWT error handlers
    from flask import jsonify
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': f'Invalid token: {str(error)}'}), 422
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is missing'}), 401
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.profiles import profiles_bp
    from routes.projects import projects_bp
    from routes.teams import teams_bp
    from routes.matching import matching_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(profiles_bp, url_prefix='/api/profiles')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(teams_bp, url_prefix='/api/teams')
    app.register_blueprint(matching_bp, url_prefix='/api/matching')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'message': 'SynapseLink API is running'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
