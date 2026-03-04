"""
Skill assessment routes for student skill verification - REBUILT.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from utils.decorators import student_required
from datetime import datetime

skills_bp = Blueprint('skills', __name__)

from models.assessment_models import SkillAssessment, AssessmentQuestion, AssessmentAttempt
from services.sql_evaluator import evaluate_sql
from services.code_evaluator import evaluate_code
import random

@skills_bp.route('/add', methods=['POST'])
@jwt_required()
@student_required
def add_skill():
    """Add a skill (initially unverified)"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        skill_name = (data.get('skill_name') or '').strip()
        if not skill_name:
            return jsonify({'error': 'skill_name is required'}), 400

        existing = SkillAssessment.query.filter_by(user_id=user_id, skill_name=skill_name).first()
        if existing:
            return jsonify({
                'message': 'Skill already exists',
                'skill': existing.to_dict()
            }), 200

        skill = SkillAssessment(user_id=user_id, skill_name=skill_name, status='unverified', score=0)
        db.session.add(skill)
        db.session.commit()
        return jsonify({
            'message': 'Skill added. Complete assessment to verify.',
            'skill': skill.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/my-skills', methods=['GET'])
@jwt_required()
@student_required
def get_my_skills():
    """List current user's skills with status"""
    try:
        user_id = int(get_jwt_identity())
        skills = SkillAssessment.query.filter_by(user_id=user_id).order_by(SkillAssessment.skill_name).all()
        return jsonify({
            'skills': [s.to_dict() for s in skills]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/assessment/<skill_name>', methods=['GET'])
@jwt_required()
@student_required
def get_assessment(skill_name):
    """Get assessment questions for a skill (SQL focus for now)"""
    try:
        skill_name = skill_name.strip()
        skill_lower = skill_lower = skill_name.lower()
        
        # Determine if it's a SQL or general coding assessment
        is_sql = skill_lower in ['sql', 'sqlite', 'mysql', 'postgresql']
        is_coding = skill_lower in ['python', 'java', 'c', 'c++', 'cpp', 'javascript', 'js']
        
        if not is_sql and not is_coding:
            return jsonify({'error': f'Assessment logic for {skill_name} not yet implemented'}), 501
            
        target_skill_for_questions = 'SQL' if is_sql else 'CODING'
            
        # Find the SkillAssessment record for this user and skill (e.g. "Python")
        user_id = int(get_jwt_identity())
        sa = SkillAssessment.query.filter_by(user_id=user_id, skill_name=skill_name).first()
        if not sa:
            sa = SkillAssessment(user_id=user_id, skill_name=skill_name, status='unverified', score=0)
            db.session.add(sa)
            db.session.flush()

        # Randomly assign a set ID (from the CODING or SQL questions)
        if sa.assigned_set_id is None:
            available_sets = db.session.query(AssessmentQuestion.set_id).filter_by(skill_name=target_skill_for_questions).distinct().all()
            if available_sets:
                set_ids = [s[0] for s in available_sets if s[0] is not None]
                if set_ids:
                    sa.assigned_set_id = random.choice(set_ids)
                    db.session.commit()
            
        if sa.assigned_set_id is None:
            return jsonify({'error': f'No assessment questions available for {skill_name} currently'}), 404

        # Fetch questions for the assigned set
        questions = AssessmentQuestion.query.filter_by(
            skill_name=target_skill_for_questions, 
            set_id=sa.assigned_set_id
        ).all()
        
        if not questions:
            return jsonify({'error': 'Assessment questions not found for the assigned set'}), 404
            
        # Ensure it returns [Easy, Hard]
        easy_q = next((q for q in questions if q.difficulty == 'easy'), None)
        hard_q = next((q for q in questions if q.difficulty == 'hard'), None)
        
        returned_questions = []
        if easy_q: returned_questions.append(easy_q.to_dict())
        if hard_q: returned_questions.append(hard_q.to_dict())

        return jsonify({
            'questions': returned_questions,
            'set_id': sa.assigned_set_id,
            'is_sql': is_sql,
            'is_coding': is_coding
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/run', methods=['POST'])
@jwt_required()
@student_required
def run_code():
    """Run code against sample tests (does NOT update status)"""
    try:
        data = request.get_json()
        code = data.get('code')
        question_id = data.get('question_id')
        language = data.get('language', 'python') # Default to python if not specified
        
        question = AssessmentQuestion.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
            
        import json
        all_cases = json.loads(question.test_cases_json)
        sample_cases = [tc for tc in all_cases if tc.get('is_sample')]
        
        # Dispatch to appropriate evaluator
        if question.skill_name == 'SQL':
            result = evaluate_sql(code, question.schema_details, json.dumps(sample_cases))
        else:
            # Mapping 'CODING' questions to the selected language
            result = evaluate_code(language, code, json.dumps(sample_cases))
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/submit', methods=['POST'])
@jwt_required()
@student_required
def submit_assessment():
    """Submit all answers for a skill verification and update status"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        answers = data.get('answers', {}) # Map of question_id to code
        skill_assessment_id = data.get('skill_assessment_id')
        language = data.get('language', 'python')
        
        sa = SkillAssessment.query.get(skill_assessment_id)
        if not sa or sa.user_id != user_id:
            return jsonify({'error': 'Invalid assessment record'}), 404
            
        if not sa.assigned_set_id:
             return jsonify({'error': 'No set assigned to this assessment. Please restart.'}), 400
             
        # Determine question set skill (SQL or CODING)
        skill_lower = sa.skill_name.lower()
        is_sql = skill_lower in ['sql', 'sqlite', 'mysql', 'postgresql']
        target_skill = 'SQL' if is_sql else 'CODING'

        questions = AssessmentQuestion.query.filter_by(
            skill_name=target_skill, 
            set_id=sa.assigned_set_id
        ).all()
        
        if not questions:
            return jsonify({'error': 'No questions found for the assigned set'}), 404
            
        total_points = 0
        max_points = 0
        all_results = {}
        
        for q in questions:
            user_code = answers.get(str(q.id)) or answers.get(q.id) or ""
            
            # Point calculation: Easy = 40, Hard = 60
            points_for_this_q = 60 if q.difficulty == 'hard' else 40
            max_points += points_for_this_q

            # Evaluate this question
            if is_sql:
                result = evaluate_sql(user_code, q.schema_details, q.test_cases_json)
            else:
                result = evaluate_code(language, user_code, q.test_cases_json)
            
            # Weighted score based on test cases passed
            # Actually, per requirement 12 & 13, maybe we just use the evaluator score * weighting
            # "Easy problem = 40 points, Hard problem = 60 points"
            # We'll award points proportional to test cases passed
            q_score_fraction = (result['passed_count'] / result['total_count']) if result['total_count'] > 0 else 0
            earned_points = points_for_this_q * q_score_fraction
            total_points += earned_points
            
            all_results[q.id] = result
            
            # Store per-question attempt
            attempt = AssessmentAttempt(
                user_id=user_id,
                skill_name=sa.skill_name,
                question_id=q.id,
                score=int(result['score']),
                passed=result['score'] >= 60
            )
            db.session.add(attempt)
            
        # Final cumulative score
        final_score = int(round(total_points))
        passed_assessment = final_score >= 60
        
        # Update skill assessment
        sa.score = final_score
        sa.status = 'passed' if passed_assessment else 'failed'
        sa.last_attempted_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'score': final_score,
            'passed': passed_assessment,
            'questions_evaluated': len(all_results),
            'skill': sa.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/verified-only', methods=['GET'])
@jwt_required()
@student_required
def get_verified_skills():
    """Get only verified skills for current user (used internally by matching)"""
    try:
        user_id = int(get_jwt_identity())
        skills = SkillAssessment.query.filter_by(user_id=user_id, status='passed').all()
        return jsonify({
            'skills': [{'skill_name': s.skill_name, 'score': s.score} for s in skills]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
