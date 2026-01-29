"""
Project and Hackathon routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.project import Project, Hackathon
from services.nlp_service import get_nlp_service
from utils.decorators import mentor_or_admin_required
from datetime import datetime

projects_bp = Blueprint('projects', __name__)
nlp_service = get_nlp_service()

@projects_bp.route('/projects', methods=['POST'])
@jwt_required()
@mentor_or_admin_required
def create_project():
    """Create a new project"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int for database query
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('description'):
            return jsonify({'error': 'Title and description are required'}), 400
        
        # Create project
        project = Project(
            title=data['title'],
            description=data['description'],
            required_skills=data.get('required_skills', ''),
            creator_id=user_id,
            min_team_size=data.get('min_team_size', 3),
            max_team_size=data.get('max_team_size', 5),
            preferred_team_size=data.get('preferred_team_size', 4),
            status=data.get('status', 'open'),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None
        )
        
        # Generate embedding
        project_text = f"{project.description} {project.required_skills}"
        embedding = nlp_service.encode_text(project_text)
        import json
        project.description_embedding = json.dumps(embedding.tolist())
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project created successfully',
            'project': project.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    """Get all projects"""
    try:
        projects = Project.query.all()
        return jsonify({
            'projects': [project.to_dict() for project in projects]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get project by ID"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        return jsonify({
            'project': project.to_dict(include_teams=True)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/hackathons', methods=['POST'])
@jwt_required()
@mentor_or_admin_required
def create_hackathon():
    """Create a new hackathon"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int for database query
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('description'):
            return jsonify({'error': 'Title and description are required'}), 400
        if not data.get('start_date') or not data.get('end_date'):
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        # Create hackathon
        hackathon = Hackathon(
            title=data['title'],
            description=data['description'],
            theme=data.get('theme', ''),
            required_skills=data.get('required_skills', ''),
            creator_id=user_id,
            min_team_size=data.get('min_team_size', 3),
            max_team_size=data.get('max_team_size', 5),
            preferred_team_size=data.get('preferred_team_size', 4),
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            registration_deadline=datetime.fromisoformat(data['registration_deadline']) if data.get('registration_deadline') else None,
            status=data.get('status', 'upcoming')
        )
        
        # Generate embedding
        hackathon_text = f"{hackathon.description} {hackathon.required_skills} {hackathon.theme}"
        embedding = nlp_service.encode_text(hackathon_text)
        import json
        hackathon.description_embedding = json.dumps(embedding.tolist())
        
        db.session.add(hackathon)
        db.session.commit()
        
        return jsonify({
            'message': 'Hackathon created successfully',
            'hackathon': hackathon.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/hackathons', methods=['GET'])
@jwt_required()
def get_hackathons():
    """Get all hackathons"""
    try:
        hackathons = Hackathon.query.all()
        return jsonify({
            'hackathons': [hackathon.to_dict() for hackathon in hackathons]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/hackathons/<int:hackathon_id>', methods=['GET'])
@jwt_required()
def get_hackathon(hackathon_id):
    """Get hackathon by ID"""
    try:
        hackathon = Hackathon.query.get(hackathon_id)
        if not hackathon:
            return jsonify({'error': 'Hackathon not found'}), 404
        
        return jsonify({
            'hackathon': hackathon.to_dict(include_teams=True)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
