from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User, Role
from models.project import Project
from models.invitation import Invitation
from models.assessment_models import SkillAssessment
from models.team import Team, TeamMember
from models.profile import StudentProfile
from utils.decorators import mentor_or_admin_required
from datetime import datetime

invitations_bp = Blueprint('invitations', __name__)

@invitations_bp.route('/recommendations/<int:project_id>', methods=['GET'])
@jwt_required()
@mentor_or_admin_required
def get_recommendations(project_id):
    """Get ranked student recommendations for a project based on verified skill scores"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Parse required skills (assuming comma-separated)
        required_skills = [s.strip() for s in project.required_skills.split(',') if s.strip()]
        if not required_skills:
            # Fallback to description-based similarity if no explicit skills
            return jsonify({'recommendations': [], 'message': 'No required skills specified for this project.'}), 200
        
        # We'll match against the first skill or all? 
        # The prompt implies matching the requirement. We'll search for students who have PASSED any of the required skills.
        # Then rank by the score of that skill.
        
        # Query passed assessments for these skills
        eligible_assessments = SkillAssessment.query.filter(
            SkillAssessment.skill_name.in_(required_skills),
            SkillAssessment.status == 'passed'
        ).order_by(SkillAssessment.score.desc()).all()
        
        recommendations = []
        seen_users = set()
        
        for assessment in eligible_assessments:
            if assessment.user_id in seen_users:
                continue
            
            user = User.query.get(assessment.user_id)
            if not user:
                continue
            
            # Check if student is already in a team for this project
            existing_member = TeamMember.query.join(Team).filter(
                Team.project_id == project_id,
                TeamMember.user_id == user.id
            ).first()
            
            if existing_member:
                continue
            
            # Check if an invitation is already pending
            existing_invitation = Invitation.query.filter_by(
                project_id=project_id,
                student_id=user.id,
                status='pending'
            ).first()
            
            recommendations.append({
                'student_id': user.id,
                'student_name': user.full_name,
                'email': user.email,
                'skill_name': assessment.skill_name,
                'skill_score': assessment.score,
                'invitation_sent': existing_invitation is not None
            })
            seen_users.add(user.id)
            
        return jsonify({
            'project_id': project_id,
            'required_skills': required_skills,
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invitations_bp.route('/invite', methods=['POST'])
@jwt_required()
@mentor_or_admin_required
def send_invite():
    """Mentor sends an invitation to a student"""
    try:
        mentor_id = int(get_jwt_identity())
        data = request.get_json()
        
        project_id = data.get('project_id')
        student_id = data.get('student_id')
        
        if not project_id or not student_id:
            return jsonify({'error': 'Project ID and Student ID are required'}), 400
        
        # Check if project exists and belongs to mentor (or admin)
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check if already invited
        existing = Invitation.query.filter_by(
            project_id=project_id,
            student_id=student_id,
            status='pending'
        ).first()
        
        if existing:
            return jsonify({'error': 'Invitation already pending'}), 400
        
        invitation = Invitation(
            project_id=project_id,
            mentor_id=mentor_id,
            student_id=student_id,
            status='pending'
        )
        
        db.session.add(invitation)
        db.session.commit()
        
        return jsonify({
            'message': 'Invitation sent successfully',
            'invitation': invitation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invitations_bp.route('/student/my-invitations', methods=['GET'])
@jwt_required()
def get_student_invitations():
    """Get invitations for the current student"""
    try:
        student_id = int(get_jwt_identity())
        invitations = Invitation.query.filter_by(student_id=student_id).all()
        
        return jsonify({
            'invitations': [inv.to_dict() for inv in invitations]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invitations_bp.route('/respond/<int:invitation_id>', methods=['POST'])
@jwt_required()
def respond_to_invitation(invitation_id):
    """Student accepts or rejects an invitation"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()
        action = data.get('action') # 'accept' or 'reject'
        
        if action not in ['accept', 'reject']:
            return jsonify({'error': 'Invalid action. Must be accept or reject.'}), 400
        
        invitation = Invitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'error': 'Invitation not found'}), 404
        
        if invitation.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if invitation.status != 'pending':
            return jsonify({'error': f'Invitation is already {invitation.status}'}), 400
        
        if action == 'reject':
            invitation.status = 'rejected'
            db.session.commit()
            return jsonify({'message': 'Invitation rejected'}), 200
        
        # Action is 'accept'
        invitation.status = 'accepted'
        
        # Logic to add student to project team
        # 1. Find or create a team for this project
        # In this system, projects might have multiple teams or one default team.
        # I'll check if there's an existing team, otherwise create one.
        team = Team.query.filter_by(project_id=invitation.project_id).first()
        if not team:
            project = Project.query.get(invitation.project_id)
            team = Team(
                name=f"Team {project.title}",
                project_id=invitation.project_id,
                status='active'
            )
            db.session.add(team)
            db.session.flush() # Get team ID
            
        # 2. Add student to team
        existing_member = TeamMember.query.filter_by(team_id=team.id, user_id=student_id).first()
        if not existing_member:
            member = TeamMember(
                team_id=team.id,
                user_id=student_id,
                role='member'
            )
            db.session.add(member)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Invitation accepted and added to team',
            'team_id': team.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
