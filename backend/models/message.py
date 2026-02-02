"""
Internal messaging model - universal for Students, Mentors, and Admins
"""

from extensions import db
from datetime import datetime

class Message(db.Model):
    """Internal message - any user can message any other user"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_role = db.Column(db.String(50), nullable=False)  # student, mentor, admin
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    # When set, message is hidden from receiver's inbox (clear/delete by receiver)
    deleted_by_receiver_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], lazy=True)
    receiver = db.relationship('User', foreign_keys=[receiver_id], lazy=True)
    
    def to_dict(self, include_sender=False):
        data = {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_role': self.sender_role,
            'receiver_id': self.receiver_id,
            'receiver_role': self.receiver_role,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_sender and self.sender:
            data['sender_name'] = self.sender.full_name
        return data
