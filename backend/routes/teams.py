"""
Team management routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.team import Team, TeamMember
from models.project import Project, Hackathon

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('', methods=['POST'])
@jwt_required()
def create_team():
    """Create a new team or join existing team for a project"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int for database query
        data = request.get_json()
        
        project_id = data.get('project_id')
        hackathon_id = data.get('hackathon_id')
        
        if not project_id and not hackathon_id:
            return jsonify({'error': 'Either project_id or hackathon_id is required'}), 400
        
        # Verify project/hackathon exists
        if project_id:
            project = Project.query.get(project_id)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
        if hackathon_id:
            hackathon = Hackathon.query.get(hackathon_id)
            if not hackathon:
                return jsonify({'error': 'Hackathon not found'}), 404
        
        # Check if user is already in a team for this project/hackathon
        existing_member = TeamMember.query.join(Team).filter(
            TeamMember.user_id == user_id,
            (Team.project_id == project_id if project_id else False) | 
            (Team.hackathon_id == hackathon_id if hackathon_id else False)
        ).first()
        
        if existing_member:
            # User is already in a team for this project
            team = existing_member.team
            # Ensure relationships are loaded
            if team.members:
                for member in team.members:
                    if member.user_id:
                        _ = member.user
            return jsonify({
                'message': 'You are already in a team for this project',
                'team': team.to_dict()
            }), 200
        
        # Check if there's an existing team for this project that has space
        if project_id:
            existing_team = Team.query.filter_by(project_id=project_id).first()
        else:
            existing_team = Team.query.filter_by(hackathon_id=hackathon_id).first()
        
        if existing_team:
            # Check if team has space
            current_size = len(existing_team.members) if existing_team.members else 0
            max_size = (project.max_team_size if project_id and project else None) or \
                      (hackathon.max_team_size if hackathon_id and hackathon else None) or 5
            
            if current_size < max_size:
                # Join existing team
                member = TeamMember(
                    team_id=existing_team.id,
                    user_id=user_id,
                    role='member',
                    status='active'
                )
                db.session.add(member)
                db.session.commit()
                
                # Reload team
                existing_team = Team.query.get(existing_team.id)
                if existing_team.members:
                    for member in existing_team.members:
                        if member.user_id:
                            _ = member.user
                
                return jsonify({
                    'message': 'Successfully joined existing team',
                    'team': existing_team.to_dict()
                }), 200
        
        # Create new team if no existing team or existing team is full
        team_name = data.get('name') or f"{project.title if project_id else hackathon.title} - Team"
        team = Team(
            name=team_name,
            project_id=project_id,
            hackathon_id=hackathon_id,
            description=data.get('description', f"Team for {project.title if project_id else hackathon.title}"),
            status='forming'
        )
        
        db.session.add(team)
        db.session.flush()
        
        # Add creator as team leader
        member = TeamMember(
            team_id=team.id,
            user_id=user_id,
            role='leader',
            status='active'
        )
        db.session.add(member)
        db.session.commit()
        
        # Reload team to ensure relationships are loaded
        team = Team.query.get(team.id)
        # Ensure user relationships are loaded for members
        if team and team.members:
            for member in team.members:
                if member.user_id:
                    _ = member.user  # Trigger lazy load
        
        return jsonify({
            'message': 'Team created successfully',
            'team': team.to_dict() if team else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@teams_bp.route('', methods=['GET'])
@jwt_required()
def get_teams():
    """Get all teams (filtered by user's context)"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int for database query
        user = User.query.get(user_id)
        
        # Get teams user is member of
        user_teams = Team.query.join(TeamMember).filter(TeamMember.user_id == user_id).all()
        
        # Ensure relationships are loaded before calling to_dict()
        def load_team_relationships(teams):
            for team in teams:
                if team.members:
                    for member in team.members:
                        if member.user_id:
                            _ = member.user  # Trigger lazy load
        
        load_team_relationships(user_teams)
        
        # If admin/mentor, get all teams
        if user.role.name in ['admin', 'mentor']:
            all_teams = Team.query.all()
            load_team_relationships(all_teams)
            return jsonify({
                'teams': [team.to_dict() for team in all_teams],
                'my_teams': [team.to_dict() for team in user_teams]
            }), 200
        
        return jsonify({
            'teams': [team.to_dict() for team in user_teams]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@teams_bp.route('/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team(team_id):
    """Get team by ID"""
    try:
        team = Team.query.get(team_id)
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        
        # Ensure user relationships are loaded for members
        if team.members:
            for member in team.members:
                if member.user_id:
                    _ = member.user  # Trigger lazy load
        
        return jsonify({
            'team': team.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@teams_bp.route('/<int:team_id>/members', methods=['POST'])
@jwt_required()
def add_member(team_id):
    """Add member to team"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int for database query
        team = Team.query.get(team_id)
        
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        
        if team.is_locked:
            return jsonify({'error': 'Team is locked'}), 400
        
        data = request.get_json()
        member_user_id = data.get('user_id', user_id)  # Default to current user
        
        # Check if user is already in team
        existing = TeamMember.query.filter_by(team_id=team_id, user_id=member_user_id).first()
        if existing:
            return jsonify({'error': 'User is already a member of this team'}), 400
        
        # Check team size limits
        project = team.project
        hackathon = team.hackathon
        max_size = (project.max_team_size if project else None) or (hackathon.max_team_size if hackathon else None) or 5
        
        if len(team.members) >= max_size:
            return jsonify({'error': 'Team is at maximum capacity'}), 400
        
        # Add member
        member = TeamMember(
            team_id=team_id,
            user_id=member_user_id,
            role=data.get('role', 'member'),
            status='active'
        )
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'message': 'Member added successfully',
            'member': member.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@teams_bp.route('/<int:team_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_member(team_id, member_id):
    """Remove member from team"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int for database query
        team = Team.query.get(team_id)
        
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        
        if team.is_locked:
            return jsonify({'error': 'Team is locked'}), 400
        
        member = TeamMember.query.get(member_id)
        if not member or member.team_id != team_id:
            return jsonify({'error': 'Member not found'}), 404
        
        # Only team leader or admin can remove members
        current_user = User.query.get(user_id)
        is_leader = any(m.user_id == user_id and m.role == 'leader' for m in team.members)
        
        if not is_leader and current_user.role.name != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(member)
        db.session.commit()
        
        return jsonify({
            'message': 'Member removed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
