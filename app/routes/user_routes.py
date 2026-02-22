"""
Маршруты для управления пользователями
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils.decorators import login_required, permission_required
from app.schemas.user_schemas import UserUpdateSchema

user_bp = Blueprint('users', __name__)

@user_bp.route('/<int:user_id>', methods=['GET'])
@login_required
@permission_required('users', 'read')
def get_user(user_id):
    """Получение пользователя по ID"""
    user = User.query.get_or_404(user_id)
    
    current_user = request.user
    if not current_user.has_permission('users', 'read', user_id):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    return jsonify({'user': user.to_dict()})

@user_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Обновление профиля пользователя"""
    if request.user.id != user_id:
        return jsonify({'error': 'Доступ запрещен', 'message': 'Вы можете обновлять только свой профиль'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    schema = UserUpdateSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'patronymic' in data:
        user.patronymic = data['patronymic']
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email уже используется'}), 400
        user.email = data['email']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Профиль успешно обновлен',
        'user': user.to_dict()
    })

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Мягкое удаление учетной записи пользователя"""
    if request.user.id != user_id:
        return jsonify({'error': 'Доступ запрещен', 'message': 'Вы можете удалить только свой аккаунт'}), 403
    
    user = User.query.get_or_404(user_id)
 
    user.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Аккаунт успешно удален'})

@user_bp.route('/<int:user_id>/sessions', methods=['GET'])
@login_required
def get_user_sessions(user_id):
    """Получение всех активных сессий пользователя."""
    if request.user.id != user_id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    from app.models import Session
    from datetime import datetime
    
    sessions = Session.query.filter(
        Session.user_id == user_id,
        Session.expires_at > datetime.utcnow()
    ).all()
    
    return jsonify({
        'sessions': [s.to_dict() for s in sessions]
    })

@user_bp.route('/<int:user_id>/sessions/<string:session_id>', methods=['DELETE'])
@login_required
def terminate_session(user_id, session_id):
    """Завершение конкретной сессии."""
    if request.user.id != user_id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    from app.models import Session
    
    session = Session.query.filter_by(id=session_id, user_id=user_id).first_or_404()
    
    current_session_id = request.cookies.get('session_id')
    if current_session_id == session_id:
        return jsonify({'error': 'Невозможно завершить текущую сессию'}), 400
    
    db.session.delete(session)
    db.session.commit()
    
    return jsonify({'message': 'Сессия успешно завершена'})