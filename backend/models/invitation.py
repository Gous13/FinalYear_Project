from extensions import db
from datetime import datetime

class Invitation(db.Model):
    """Invitation model for project collaboration"""
    __tablename__ = 'invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Status: pending, accepted, rejected
    status = db.Column(db.String(20), default='pending', nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='invitations', lazy=True)
    mentor = db.relationship('User', foreign_keys=[mentor_id], backref='sent_invitations', lazy=True)
    student = db.relationship('User', foreign_keys=[student_id], backref='received_invitations', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_title': self.project.title if self.project else None,
            'project_required_skills': self.project.required_skills if self.project else None,
            'mentor_id': self.mentor_id,
            'mentor_name': self.mentor.full_name if self.mentor else 'Unknown',
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else 'Unknown',
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
