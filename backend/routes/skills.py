"""
Skill assessment routes for student skill verification
"""

import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.student_skill import StudentSkill
from models.skill_assessment import SkillAssessment, SkillAssessmentResult
from utils.decorators import student_required

skills_bp = Blueprint('skills', __name__)

PASSING_THRESHOLD = 70.0  # Configurable passing score percentage


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

        existing = StudentSkill.query.filter_by(user_id=user_id, skill_name=skill_name).first()
        if existing:
            return jsonify({
                'message': 'Skill already exists',
                'skill': existing.to_dict()
            }), 200

        skill = StudentSkill(user_id=user_id, skill_name=skill_name, status='unverified')
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
        skills = StudentSkill.query.filter_by(user_id=user_id).order_by(StudentSkill.skill_name).all()
        return jsonify({
            'skills': [s.to_dict() for s in skills]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@skills_bp.route('/assessment/<skill_name>', methods=['GET'])
@jwt_required()
@student_required
def get_assessment(skill_name):
    """Get MCQ assessment questions for a skill"""
    try:
        skill_name = skill_name.strip()
        questions = SkillAssessment.query.filter_by(skill_name=skill_name).limit(8).all()
        if not questions:
            return jsonify({'error': f'No assessment available for skill: {skill_name}'}), 404
        # Return questions without correct_option (for security)
        result = []
        for q in questions:
            result.append({
                'id': q.id,
                'skill_name': q.skill_name,
                'question_text': q.question_text,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
            })
        return jsonify({'questions': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@skills_bp.route('/assess/<int:student_skill_id>', methods=['POST'])
@jwt_required()
@student_required
def submit_assessment(student_skill_id):
    """Submit assessment answers and get result"""
    try:
        user_id = int(get_jwt_identity())
        student_skill = StudentSkill.query.get(student_skill_id)
        if not student_skill or student_skill.user_id != user_id:
            return jsonify({'error': 'Skill not found'}), 404

        data = request.get_json()
        answers = data.get('answers')  # {question_id: 'a'|'b'|'c'|'d'}
        if not isinstance(answers, dict):
            return jsonify({'error': 'answers must be an object mapping question_id to option'}), 400

        q_ids = []
        for k in answers.keys():
            try:
                q_ids.append(int(k))
            except (ValueError, TypeError):
                pass
        if not q_ids:
            return jsonify({'error': 'No valid question IDs'}), 400

        questions = SkillAssessment.query.filter(
            SkillAssessment.id.in_(q_ids),
            SkillAssessment.skill_name == student_skill.skill_name
        ).all()
        if not questions:
            return jsonify({'error': 'No valid questions found'}), 400

        correct = 0
        total = len(questions)
        for q in questions:
            sid = str(q.id)
            if sid in answers and answers[sid].lower() in ['a', 'b', 'c', 'd']:
                if answers[sid].lower() == q.correct_option.lower():
                    correct += 1

        score = (correct / total * 100) if total > 0 else 0
        passed = score >= PASSING_THRESHOLD

        result = SkillAssessmentResult(
            student_skill_id=student_skill_id,
            answers=json.dumps(answers),
            score=score,
            passed=passed
        )
        db.session.add(result)

        if passed:
            from datetime import datetime
            student_skill.status = 'verified'
            student_skill.assessment_score = score
            student_skill.assessed_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'score': round(score, 1),
            'passed': passed,
            'correct': correct,
            'total': total,
            'skill': student_skill.to_dict()
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
        skills = StudentSkill.query.filter_by(user_id=user_id, status='verified').all()
        return jsonify({
            'skills': [{'skill_name': s.skill_name, 'score': s.assessment_score} for s in skills]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
