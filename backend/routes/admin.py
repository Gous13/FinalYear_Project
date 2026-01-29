"""
Admin routes for system management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User, Role
from models.analytics import SystemLog
from models.project import Project
from models.team import Team
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_stats():
    """Get system statistics"""
    try:
        stats = {
            'users': {
                'total': User.query.count(),
                'students': User.query.join(Role).filter(Role.name == 'student').count(),
                'mentors': User.query.join(Role).filter(Role.name == 'mentor').count(),
                'admins': User.query.join(Role).filter(Role.name == 'admin').count(),
                'active': User.query.filter_by(is_active=True).count()
            },
            'projects': {
                'total': Project.query.count(),
                'open': Project.query.filter_by(status='open').count(),
                'in_progress': Project.query.filter_by(status='in_progress').count(),
                'completed': Project.query.filter_by(status='completed').count()
            },
            'teams': {
                'total': Team.query.count(),
                'forming': Team.query.filter_by(status='forming').count(),
                'active': Team.query.filter_by(status='active').count()
            },
            'logs': {
                'total': SystemLog.query.count()
            }
        }
        
        return jsonify({
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
@admin_required
def get_logs():
    """Get system logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        logs = SystemLog.query.order_by(SystemLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in logs.items],
            'total': logs.total,
            'page': page,
            'per_page': per_page,
            'pages': logs.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/init-roles', methods=['POST'])
@jwt_required()
@admin_required
def init_roles():
    """Initialize default roles"""
    try:
        roles_data = [
            {'name': 'student', 'description': 'Student user'},
            {'name': 'mentor', 'description': 'Mentor/Faculty user'},
            {'name': 'admin', 'description': 'Administrator'}
        ]
        
        created = []
        for role_data in roles_data:
            role = Role.query.filter_by(name=role_data['name']).first()
            if not role:
                role = Role(**role_data)
                db.session.add(role)
                created.append(role_data['name'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Roles initialized',
            'created': created
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
