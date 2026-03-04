"""
Matching and team formation routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.profile import StudentProfile
from models.project import Project, Hackathon
from models.team import Team, TeamMember
from models.matching import SimilarityScore, MatchExplanation
from models.assessment_models import SkillAssessment
from services.nlp_service import get_nlp_service
from services.optimization_service import OptimizationService
from services.explanation_service import ExplanationService
from utils.decorators import student_required
import json

matching_bp = Blueprint('matching', __name__)
nlp_service = get_nlp_service()
optimization_service = OptimizationService()
explanation_service = ExplanationService()

def _compute_profile_project_similarity(project_embedding, profile):
    """
    Compute semantic similarity using ONLY:
    - skills_description
    - interests_description
    - experience_description
    Uses embeddings + cosine similarity, and returns:
      (overall, skills_sim, interests_sim, experience_sim)
    """
    # Ensure per-field embeddings exist (do not embed availability/year/gpa)
    skills_emb = json.loads(profile.skills_embedding) if profile.skills_embedding else None
    interests_emb = json.loads(profile.interests_embedding) if profile.interests_embedding else None
    experience_emb = json.loads(profile.experience_embedding) if profile.experience_embedding else None

    # Lazily compute missing embeddings
    if skills_emb is None:
        skills_emb = nlp_service.encode_text(profile.skills_description or '').tolist()
        profile.skills_embedding = json.dumps(skills_emb)
    if interests_emb is None:
        interests_emb = nlp_service.encode_text(profile.interests_description or '').tolist()
        profile.interests_embedding = json.dumps(interests_emb)
    if experience_emb is None:
        experience_emb = nlp_service.encode_text(profile.experience_description or '').tolist()
        profile.experience_embedding = json.dumps(experience_emb)

    skills_sim = nlp_service.compute_similarity(project_embedding, skills_emb)
    interests_sim = nlp_service.compute_similarity(project_embedding, interests_emb) if (profile.interests_description or '').strip() else None
    experience_sim = nlp_service.compute_similarity(project_embedding, experience_emb) if (profile.experience_description or '').strip() else None

    sims = [skills_sim]
    if interests_sim is not None:
        sims.append(interests_sim)
    if experience_sim is not None:
        sims.append(experience_sim)
    overall = float(sum(sims) / max(len(sims), 1))

    return overall, skills_sim, interests_sim, experience_sim

def _auto_form_teams_for_project(project_id):
    """
    Helper function to automatically form teams for a project when enough students have joined.
    This function:
    1. Gets all students who have joined the project (via TeamMember)
    2. Checks if we have enough students (>= preferred_team_size)
    3. Checks if teams haven't been auto-formed yet (status is 'open' or teams are 'forming')
    4. If yes, uses optimization to form optimal teams
    5. Deletes old ad-hoc teams and creates optimized teams
    
    Returns: (success: bool, teams_formed: int, message: str)
    """
    try:
        project = Project.query.get(project_id)
        if not project:
            return False, 0, 'Project not found'
        
        # Check if teams have already been auto-formed (status is 'team_forming' or 'in_progress')
        if project.status in ['team_forming', 'in_progress']:
            # Check if teams exist and are not just 'forming' status
            existing_teams = Team.query.filter_by(project_id=project_id).all()
            if existing_teams and any(t.status != 'forming' for t in existing_teams):
                return False, 0, 'Teams already formed'
        
        # Get all students who have joined this project (via TeamMember)
        joined_members = TeamMember.query.join(Team).filter(
            Team.project_id == project_id
        ).all()
        
        if not joined_members:
            return False, 0, 'No students have joined yet'
        
        # Get unique user IDs who have joined
        joined_user_ids = list(set([m.user_id for m in joined_members]))
        
        # Check if we have enough students (need at least preferred_team_size)
        if len(joined_user_ids) < project.preferred_team_size:
            return False, 0, f'Not enough students yet ({len(joined_user_ids)}/{project.preferred_team_size})'
        
        # Get profiles for these users
        joined_profiles = StudentProfile.query.filter(
            StudentProfile.user_id.in_(joined_user_ids)
        ).all()
        
        if len(joined_profiles) < project.min_team_size:
            return False, 0, f'Not enough profiles ({len(joined_profiles)}/{project.min_team_size})'
        
        # Get similarity scores for these profiles (skills/interests/experience ONLY)
        similarity_scores = {}
        for profile in joined_profiles:
            similarity = SimilarityScore.query.filter_by(
                profile_id=profile.id,
                project_id=project_id
            ).first()
            
            if similarity:
                similarity_scores[profile.id] = similarity.overall_similarity
            else:
                # Compute on the fly if missing
                project_embedding = json.loads(project.description_embedding) if project.description_embedding else None
                if not project_embedding:
                    project_text = f"{project.description} {project.required_skills}"
                    project_embedding = nlp_service.encode_text(project_text).tolist()
                    project.description_embedding = json.dumps(project_embedding)

                overall_sim, skills_sim, interests_sim, experience_sim = _compute_profile_project_similarity(project_embedding, profile)
                similarity_scores[profile.id] = overall_sim

                # Store for reuse (no schema change; uses existing columns)
                s = SimilarityScore(
                    profile_id=profile.id,
                    project_id=project_id,
                    overall_similarity=overall_sim,
                    skills_similarity=skills_sim,
                    interests_similarity=interests_sim,
                    experience_similarity=experience_sim
                )
                db.session.add(s)
        
        # Form teams using optimization (only for joined students)
        constraints = {
            'min_team_size': project.min_team_size,
            'max_team_size': project.max_team_size,
            'preferred_team_size': project.preferred_team_size
        }
        team_assignments = optimization_service.form_teams(
            joined_profiles, project, similarity_scores, constraints
        )

        # IMPORTANT: Never delete existing teams unless optimizer produced a valid assignment.
        # This preserves the student->team mapping used by "My Teams" even if optimization
        # cannot currently find a feasible solution (e.g., constraints too tight).
        if not team_assignments or not any(team_assignments):
            db.session.rollback()
            return False, 0, 'Optimization could not form teams yet; keeping current team memberships'

        # Delete existing ad-hoc teams for this project (we'll recreate them optimally)
        existing_teams = Team.query.filter_by(project_id=project_id).all()
        for team in existing_teams:
            db.session.delete(team)
        db.session.flush()
        
        # Create optimized teams in database
        team_ids = []
        for idx, team_profile_ids in enumerate(team_assignments):
            if not team_profile_ids:
                continue
            
            team = Team(
                name=f"{project.title} - Team {idx + 1}",
                project_id=project_id,
                status='active',  # Teams are ready when auto-formed
                description=f"AI-optimized team for {project.title}"
            )
            db.session.add(team)
            db.session.flush()
            team_ids.append(team.id)
            
            # Add members
            for profile_id in team_profile_ids:
                profile = StudentProfile.query.get(profile_id)
                if profile:
                    member = TeamMember(
                        team_id=team.id,
                        user_id=profile.user_id,
                        role='leader' if team_profile_ids.index(profile_id) == 0 else 'member',
                        status='active'
                    )
                    db.session.add(member)
        
        # If for any reason no teams were created, do not wipe memberships.
        if len(team_ids) == 0:
            db.session.rollback()
            return False, 0, 'Optimization produced no teams; keeping current team memberships'

        project.status = 'team_forming'
        db.session.commit()

        # Ensure project group chat exists for team collaboration
        try:
            from services.group_chat_service import ensure_project_group_chat
            ensure_project_group_chat(project_id)
            db.session.commit()
        except Exception:
            pass  # Don't fail team formation if group chat fails

        return True, len(team_ids), f'Successfully formed {len(team_ids)} team(s)'
        
    except Exception as e:
        db.session.rollback()
        return False, 0, f'Error forming teams: {str(e)}'

@matching_bp.route('/compute-similarities/<int:project_id>', methods=['POST'])
@jwt_required()
def compute_similarities(project_id):
    """Compute similarity scores for all profiles against a project"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get all student profiles that have at least one passed skill
        # Recruiter Rule: Don't suggest unverified candidates to mentors
        profiles = StudentProfile.query.join(User).join(SkillAssessment, SkillAssessment.user_id == User.id).filter(
            SkillAssessment.status.in_(['passed', 'verified'])
        ).distinct().all()
        
        if not profiles:
            return jsonify({'error': 'No verified student profiles found for matching.'}), 404
        
        # Get project embedding
        project_embedding = json.loads(project.description_embedding) if project.description_embedding else None
        if not project_embedding:
            # Generate if missing
            project_text = f"{project.description} {project.required_skills}"
            project_embedding = nlp_service.encode_text(project_text).tolist()
            project.description_embedding = json.dumps(project_embedding)
            db.session.commit()
        
        similarity_results = []
        
        for profile in profiles:
            overall_sim, skills_sim, interests_sim, experience_sim = _compute_profile_project_similarity(project_embedding, profile)
            
            # Store similarity score
            similarity = SimilarityScore.query.filter_by(
                profile_id=profile.id,
                project_id=project_id
            ).first()
            
            if similarity:
                similarity.overall_similarity = overall_sim
                similarity.skills_similarity = skills_sim
                similarity.interests_similarity = interests_sim
                similarity.experience_similarity = experience_sim
            else:
                similarity = SimilarityScore(
                    profile_id=profile.id,
                    project_id=project_id,
                    overall_similarity=overall_sim,
                    skills_similarity=skills_sim,
                    interests_similarity=interests_sim,
                    experience_similarity=experience_sim
                )
                db.session.add(similarity)
            
            similarity_results.append({
                'profile_id': profile.id,
                'user_id': profile.user_id,
                'user_name': profile.user.full_name if profile.user else None,
                'similarity': overall_sim,
                'profile': profile.to_dict()
            })

        db.session.commit()
        
        # Sort by similarity
        similarity_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return jsonify({
            'message': 'Similarities computed successfully',
            'similarities': similarity_results,
            'project': project.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@matching_bp.route('/form-teams/<int:project_id>', methods=['POST'])
@jwt_required()
def form_teams(project_id):
    """Form optimal teams for a project using optimization"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int for database query
        user = User.query.get(user_id)
        
        # Only mentors/admins can trigger team formation
        if user.role.name not in ['mentor', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Some clients may call this endpoint without a JSON body or with a non-JSON
        # Content-Type (e.g. form-encoded). Using silent=True prevents Flask from
        # raising an UnsupportedMediaType error in those cases and lets us fallback
        # to empty constraints by default, which keeps existing behavior intact.
        data = request.get_json(silent=True) or {}
        constraints = data.get('constraints', {})
        
        # Get all student profiles that have at least one passed skill
        profiles = StudentProfile.query.join(User).join(SkillAssessment, SkillAssessment.user_id == User.id).filter(
            SkillAssessment.status.in_(['passed', 'verified'])
        ).distinct().all()
        
        if len(profiles) < project.min_team_size:
            return jsonify({'error': f'Not enough verified students (need at least {project.min_team_size})'}), 400
        
        # Get similarity scores
        similarity_scores = {}
        for profile in profiles:
            similarity = SimilarityScore.query.filter_by(
                profile_id=profile.id,
                project_id=project_id
            ).first()
            
            if similarity:
                similarity_scores[profile.id] = similarity.overall_similarity
            else:
                # Compute on the fly
                similarity_scores[profile.id] = 0.5  # Default
        
        # Form teams using optimization
        team_assignments = optimization_service.form_teams(
            profiles, project, similarity_scores, constraints
        )
        
        # Create teams in database
        team_ids = []
        for idx, team_profile_ids in enumerate(team_assignments):
            if not team_profile_ids:
                continue
            
            team = Team(
                name=f"{project.title} - Team {idx + 1}",
                project_id=project_id,
                status='forming',
                description=f"AI-generated team for {project.title}"
            )
            db.session.add(team)
            db.session.flush()
            team_ids.append(team.id)
            
            # Add members
            for profile_id in team_profile_ids:
                profile = StudentProfile.query.get(profile_id)
                if profile:
                    member = TeamMember(
                        team_id=team.id,
                        user_id=profile.user_id,
                        role='leader' if team_profile_ids.index(profile_id) == 0 else 'member',
                        status='active'
                    )
                    db.session.add(member)
        
        project.status = 'team_forming'
        db.session.commit()

        # Ensure project group chat exists for team collaboration
        try:
            from services.group_chat_service import ensure_project_group_chat
            ensure_project_group_chat(project_id)
            db.session.commit()
        except Exception:
            pass  # Don't fail team formation if group chat fails

        # Query teams fresh to ensure relationships are loaded
        created_teams = []
        for team_id in team_ids:
            team = Team.query.get(team_id)
            if team:
                created_teams.append(team.to_dict())
        
        # Reload project to ensure creator relationship is loaded
        project = Project.query.get(project_id)
        # Ensure creator relationship is loaded
        if project and project.creator_id:
            _ = project.creator  # Trigger lazy load
        
        return jsonify({
            'message': f'Formed {len(created_teams)} teams successfully',
            'teams': created_teams,
            'project': project.to_dict() if project else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@matching_bp.route('/explanation/<int:similarity_id>', methods=['GET'])
@jwt_required()
def get_explanation(similarity_id):
    """Get explainable AI explanation for a match"""
    try:
        similarity = SimilarityScore.query.get(similarity_id)
        if not similarity:
            return jsonify({'error': 'Similarity score not found'}), 404
        
        profile = similarity.profile
        project = similarity.project or similarity.hackathon
        
        if not profile or not project:
            return jsonify({'error': 'Profile or project not found'}), 404
        
        # Check if explanation exists
        explanation = MatchExplanation.query.filter_by(similarity_score_id=similarity_id).first()
        
        if not explanation:
            # Generate explanation
            explanation_data = explanation_service.generate_explanation(profile, project, similarity)
            
            explanation = MatchExplanation(
                similarity_score_id=similarity_id,
                explanation_text=explanation_data['explanation_text'],
                overlapping_skills=json.dumps(explanation_data['overlapping_skills']),
                strengths=json.dumps(explanation_data['strengths']),
                recommendations=json.dumps(explanation_data['recommendations'])
            )
            db.session.add(explanation)
            db.session.commit()
        
        return jsonify({
            'explanation': explanation.to_dict(),
            'similarity': similarity.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@matching_bp.route('/explanation/project/<int:project_id>', methods=['GET'])
@jwt_required()
def get_explanation_by_project(project_id):
    """Get explainable AI explanation for a match by project ID (when similarity_id not available)"""
    try:
        user_id = int(get_jwt_identity())
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        project = Project.query.get(project_id)
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Compute similarity on the fly if needed
        project_embedding = json.loads(project.description_embedding) if project.description_embedding else None
        profile_embedding = json.loads(profile.skills_embedding) if profile.skills_embedding else None
        
        if project_embedding and profile_embedding:
            overall_sim = nlp_service.compute_similarity(project_embedding, profile_embedding)
        else:
            overall_sim = 0.5
        
        # Create a temporary similarity object for explanation
        from models.matching import SimilarityScore
        temp_similarity = SimilarityScore(
            profile_id=profile.id,
            project_id=project.id,
            overall_similarity=overall_sim
        )
        
        # Generate explanation
        explanation_data = explanation_service.generate_explanation(profile, project, temp_similarity)
        
        return jsonify({
            'explanation': explanation_data,
            'similarity': overall_sim
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@matching_bp.route('/recommendations', methods=['GET'])
@jwt_required()
@student_required
def get_recommendations():
    """Get project recommendations for current student"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int for database query
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            return jsonify({'error': 'Profile not found. Please create a profile first.'}), 404
        
        # Get all open projects (case-insensitive)
        from sqlalchemy import func
        projects = Project.query.filter(Project.status.ilike('open')).all()
        
        # Get project IDs where user is already in an ACTIVE team
        from models.team import Team, TeamMember
        active_memberships = TeamMember.query.filter(
            TeamMember.user_id == user_id,
            TeamMember.status == 'active'
        ).all()
        joined_project_ids = {Team.query.get(m.team_id).project_id for m in active_memberships if Team.query.get(m.team_id) and Team.query.get(m.team_id).project_id}
        
        recommendations = []

        # Mandatory Skill Verification: Only PASSED or VERIFIED skills count for recommendations
        verified_skills = SkillAssessment.query.filter(
            SkillAssessment.user_id == user_id,
            func.lower(SkillAssessment.status).in_(['passed', 'verified'])
        ).all()
        
        student_skill_names = {s.skill_name.lower().strip() for s in verified_skills}
        import re
        
        for project in projects:
            # Skip projects user has already joined
            if project.id in joined_project_ids:
                continue
            
            # Extract project metadata for matching
            project_title = (project.title or '').lower()
            project_required = (project.required_skills or '').lower()
            project_desc = (project.description or '').lower()
            project_search_text = f"{project_title} {project_required} {project_desc}"
            project_search_tokens = set(re.findall(r'\b\w+\b', project_search_text))
            
            # Check skill overlap - robust token-based matching
            skill_overlap = set()
            for sk in student_skill_names:
                sk_tokens = set(re.findall(r'\b\w+\b', sk))
                if not sk_tokens: continue
                
                if len(sk) < 4:
                    # For short skills (SQL, Java, C++), require an exact token match
                    if sk_tokens & project_search_tokens:
                        skill_overlap.add(sk)
                else:
                    # For longer skills (Data Science, Python Programming), allow substring or token match
                    if sk in project_search_text or (sk_tokens & project_search_tokens):
                        skill_overlap.add(sk)

            # Strict Rule: If project has REQUIRED skills, user MUST have at least one match
            if not skill_overlap and project.required_skills:
                continue
            
            # Get or compute similarity
            similarity = SimilarityScore.query.filter_by(
                profile_id=profile.id,
                project_id=project.id
            ).first()
            
            if not similarity:
                # Compute on the fly if missing
                project_embedding = json.loads(project.description_embedding) if project.description_embedding else None
                profile_embedding = json.loads(profile.skills_embedding) if profile.skills_embedding else None
                
                if project_embedding and profile_embedding:
                    overall_sim = nlp_service.compute_similarity(project_embedding, profile_embedding)
                else:
                    # Fallback similarity based on overlap
                    overall_sim = min(0.7, 0.4 + (len(skill_overlap) * 0.1)) if skill_overlap else 0.3
                
                # Store the computed similarity
                similarity = SimilarityScore(
                    profile_id=profile.id,
                    project_id=project.id,
                    overall_similarity=overall_sim
                )
                db.session.add(similarity)
                db.session.flush()
            else:
                overall_sim = similarity.overall_similarity
            
            # Priority Rule: If they have a verified skill match, don't skip due to NLP score
            if overall_sim < 0.5 and len(skill_overlap) < 1:
                continue
            
            recommendations.append({
                'project': project.to_dict(),
                'similarity': overall_sim,
                'similarity_id': similarity.id,
                'skill_overlap_count': len(skill_overlap),
                'matching_skills': list(skill_overlap)[:10]
            })
        
        db.session.commit()
        recommendations.sort(key=lambda x: x['similarity'], reverse=True)
        
        return jsonify({
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
