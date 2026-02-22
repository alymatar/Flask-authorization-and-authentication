"""
Маршруты аутентификации - регистрация, вход в систему, выход из системы, обновление token
"""
from flask import Blueprint, request, jsonify, make_response
from app import db
from app.models import User, Session
from app.services.auth_service import generate_tokens, create_session, get_current_user, refresh_access_token
from app.schemas.user_schemas import UserRegisterSchema, UserLoginSchema, UserUpdateSchema
from app.utils.decorators import login_required
from datetime import datetime
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Зарегистрируйте нового пользователя"""
    data = request.get_json()
    schema = UserRegisterSchema(context={'password': data.get('password')})
    errors = schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email уже зарегистрирован'}), 400
    
    from app.models import Role
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        return jsonify({'error': 'Ошибка конфигурации системы'}), 500
    
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        patronymic=data.get('patronymic'),
        role_id=user_role.id
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'Пользователь успешно зарегистрирован',
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Вход пользователя в систему и возврат токенов + сессионный файл cookie"""
    data = request.get_json()
    
    schema = UserLoginSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    user = User.query.filter_by(email=data['email'], is_active=True).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Неверный email или пароль'}), 401
    
    access_token, refresh_token = generate_tokens(user.id)
    session_id = create_session(user.id, request)
    user.update_last_login(request.remote_addr)
    
    response_data = {
        'message': 'Вход выполнен успешно',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 3600  # 1 час
    }
    
    response = make_response(jsonify(response_data))
    
    # Установить сессионный файл cookie
    response.set_cookie(
        'session_id',
        session_id,
        httponly=True,
        secure=False, 
        max_age=7*24*60*60,  # 7 дней
        samesite='Lax'
    )
    
    return response

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Выход пользователя из системы - аннулирование сеанса и токенов."""
    session_id = request.cookies.get('session_id')
    
    if session_id:
        Session.query.filter_by(id=session_id).delete()
        db.session.commit()
    
    response = make_response(jsonify({'message': 'Выход выполнен успешно'}))
    response.delete_cookie('session_id')
    
    return response

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Получение нового токена доступа с помощью токена обновления."""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Требуется refresh токен'}), 400
    
    result = refresh_access_token(refresh_token)
    
    if result['success']:
        return jsonify({
            'access_token': result['access_token'],
            'expires_in': 3600
        })
    else:
        return jsonify({'error': result['error']}), 401

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user_info():
    """ Получение информации о текущем пользователе"""
    user = request.user
    return jsonify({'user': user.to_dict()})

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """ Проверка аутентификации пользователя"""
    user = get_current_user()
    
    if user:
        return jsonify({
            'authenticated': True,
            'user': user.to_dict()
        })
    else:
        return jsonify({
            'authenticated': False,
            'user': None
        })