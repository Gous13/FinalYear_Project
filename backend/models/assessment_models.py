from extensions import db
from datetime import datetime

class SkillAssessment(db.Model):
    """
    TABLE: skill_assessments
    Fields: id, user_id, skill_name, status, score, last_attempted_at
    """
    __tablename__ = 'skill_assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    skill_name = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(20), default='unverified', nullable=False)  # unverified, passed, failed
    score = db.Column(db.Integer, default=0)
    assigned_set_id = db.Column(db.Integer)  # To keep questions consistent for an attempt
    last_attempted_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'skill_name', name='unique_user_skill_new'),)

    @staticmethod
    def get_total_verified_score(user_id):
        """Calculate the sum of scores for all passed assessments for a user"""
        result = db.session.query(db.func.sum(SkillAssessment.score)).filter(
            SkillAssessment.user_id == user_id,
            SkillAssessment.status == 'passed'
        ).scalar()
        return int(result) if result else 0

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'skill_name': self.skill_name,
            'status': self.status,
            'score': self.score,
            'assigned_set_id': self.assigned_set_id,
            'last_attempted_at': self.last_attempted_at.isoformat() if self.last_attempted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class AssessmentQuestion(db.Model):
    """
    TABLE: assessment_questions
    Fields: id, skill_name, difficulty, title, description, input_format, output_format, 
            sample_input, sample_output, constraints, schema_details, test_cases_json, created_at
    """
    __tablename__ = 'assessment_questions'

    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), nullable=False, index=True)
    set_id = db.Column(db.Integer, index=True) # group_id for sets
    difficulty = db.Column(db.String(20), nullable=False)  # easy, hard
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    input_format = db.Column(db.Text)
    output_format = db.Column(db.Text)
    sample_input = db.Column(db.Text)
    sample_output = db.Column(db.Text)
    constraints = db.Column(db.Text)
    schema_details = db.Column(db.Text)  # Used for SQL questions (table DDL)
    test_cases_json = db.Column(db.Text, nullable=False)  # Hidden test cases
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'skill_name': self.skill_name,
            'set_id': self.set_id,
            'difficulty': self.difficulty,
            'title': self.title,
            'description': self.description,
            'input_format': self.input_format,
            'output_format': self.output_format,
            'sample_input': self.sample_input,
            'sample_output': self.sample_output,
            'constraints': self.constraints,
            'schema_details': self.schema_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class AssessmentAttempt(db.Model):
    """
    TABLE: assessment_attempts
    Fields: id, user_id, skill_name, question_id, score, passed, created_at
    """
    __tablename__ = 'assessment_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    skill_name = db.Column(db.String(100), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('assessment_questions.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    passed = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'skill_name': self.skill_name,
            'question_id': self.question_id,
            'score': self.score,
            'passed': self.passed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
