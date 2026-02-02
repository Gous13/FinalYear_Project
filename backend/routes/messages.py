"""
Internal messaging routes - universal for Students, Mentors, and Admins
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.message import Message
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/recipients', methods=['GET'])
@jwt_required()
def get_recipients():
    """Get users matching email search (for composing messages). Filter by ?q=email"""
    try:
        current_user_id = int(get_jwt_identity())
        q = request.args.get('q', '').strip().lower()
        query = User.query.filter(User.id != current_user_id, User.is_active == True)
        if q:
            query = query.filter(db.func.lower(User.email).contains(q))
        users = query.limit(20).all()
        return jsonify({
            'users': [u.to_dict() for u in users]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get list of conversations (users with message exchange) with last message and unread count"""
    try:
        current_user_id = int(get_jwt_identity())
        # Get all messages where current user is sender or receiver (not deleted)
        sent = db.session.query(Message.receiver_id).filter(
            Message.sender_id == current_user_id
        ).distinct()
        received = db.session.query(Message.sender_id).filter(
            Message.receiver_id == current_user_id,
            Message.deleted_by_receiver_at == None
        ).distinct()
        other_ids = set()
        for r in sent:
            other_ids.add(r[0])
        for r in received:
            other_ids.add(r[0])
        
        conversations = []
        for other_id in other_ids:
            other = User.query.get(other_id)
            if not other or not other.is_active:
                continue
            last_msg = Message.query.filter(
                ((Message.sender_id == current_user_id) & (Message.receiver_id == other_id)) |
                ((Message.sender_id == other_id) & (Message.receiver_id == current_user_id) & (Message.deleted_by_receiver_at == None))
            ).order_by(Message.created_at.desc()).first()
            if not last_msg:
                continue
            unread = Message.query.filter(
                Message.sender_id == other_id,
                Message.receiver_id == current_user_id,
                Message.deleted_by_receiver_at == None,
                Message.is_read == False
            ).count()
            conversations.append({
                'other_user': other.to_dict(),
                'last_message': last_msg.to_dict(include_sender=True),
                'unread_count': unread,
                'last_at': last_msg.created_at.isoformat() if last_msg.created_at else None
            })
        conversations.sort(key=lambda x: x['last_at'] or '', reverse=True)
        return jsonify({'conversations': conversations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversations/<int:other_user_id>', methods=['GET'])
@jwt_required()
def get_thread(other_user_id):
    """Get full thread with a user. Mark messages from them as read."""
    try:
        current_user_id = int(get_jwt_identity())
        other = User.query.get(other_user_id)
        if not other:
            return jsonify({'error': 'User not found'}), 404
        
        messages = Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.receiver_id == other_user_id)) |
            ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user_id) & (Message.deleted_by_receiver_at == None))
        ).order_by(Message.created_at.asc()).all()
        
        # Mark received messages as read
        for m in messages:
            if m.receiver_id == current_user_id and not m.is_read:
                m.is_read = True
        db.session.commit()
        
        result = []
        for m in messages:
            d = m.to_dict(include_sender=True)
            d['is_mine'] = m.sender_id == current_user_id
            result.append(d)
        
        return jsonify({
            'other_user': other.to_dict(),
            'messages': result
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messages_bp.route('', methods=['POST'])
@jwt_required()
def send_message():
    """Send a message to another user"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()
        
        if not receiver_id:
            return jsonify({'error': 'receiver_id is required'}), 400
        if not content:
            return jsonify({'error': 'Message content is required'}), 400
        
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({'error': 'Recipient not found'}), 404
        if not receiver.is_active:
            return jsonify({'error': 'Cannot message inactive user'}), 400
        
        msg = Message(
            sender_id=current_user_id,
            sender_role=current_user.role.name if current_user.role else 'unknown',
            receiver_id=receiver_id,
            receiver_role=receiver.role.name if receiver.role else 'unknown',
            content=content
        )
        db.session.add(msg)
        db.session.commit()
        
        return jsonify({
            'message': 'Message sent',
            'msg': msg.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messages_bp.route('', methods=['GET'])
@jwt_required()
def get_inbox():
    """Get inbox - messages where current user is receiver, not deleted"""
    try:
        current_user_id = int(get_jwt_identity())
        messages = Message.query.filter(
            Message.receiver_id == current_user_id,
            Message.deleted_by_receiver_at == None
        ).order_by(Message.created_at.desc()).all()
        
        result = []
        for m in messages:
            d = m.to_dict(include_sender=True)
            result.append(d)
        
        return jsonify({
            'messages': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get count of unread messages for current user"""
    try:
        current_user_id = int(get_jwt_identity())
        count = Message.query.filter(
            Message.receiver_id == current_user_id,
            Message.deleted_by_receiver_at == None,
            Message.is_read == False
        ).count()
        return jsonify({'unread_count': count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/<int:msg_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(msg_id):
    """Mark a message as read"""
    try:
        current_user_id = int(get_jwt_identity())
        msg = Message.query.get(msg_id)
        if not msg:
            return jsonify({'error': 'Message not found'}), 404
        if msg.receiver_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        if msg.deleted_by_receiver_at:
            return jsonify({'error': 'Message not found'}), 404
        
        msg.is_read = True
        db.session.commit()
        return jsonify({'message': 'Marked as read', 'msg': msg.to_dict(include_sender=True)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/<int:msg_id>', methods=['DELETE'])
@jwt_required()
def clear_message(msg_id):
    """Clear/delete message from receiver's inbox (soft delete - does not affect sender)"""
    try:
        current_user_id = int(get_jwt_identity())
        msg = Message.query.get(msg_id)
        if not msg:
            return jsonify({'error': 'Message not found'}), 404
        if msg.receiver_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        if msg.deleted_by_receiver_at:
            return jsonify({'error': 'Message already cleared'}), 400
        
        msg.deleted_by_receiver_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Message cleared'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
