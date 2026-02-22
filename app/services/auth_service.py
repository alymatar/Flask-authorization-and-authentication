"""
auth_service - обработка JWT токенов и сессий
"""
import jwt
import uuid
from datetime import datetime, timedelta
from flask import request, current_app
from app import db
from app.models import User, Session

def generate_tokens(user_id):
    """
    Генерация JWT access и refresh токенов
    """
    # Access token - короткоживущий
    access_token = jwt.encode(
        {
            'user_id': user_id,
            'type': 'access',
            'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': datetime.utcnow()
        },
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    # Refresh token - долгоживущий
    refresh_token = jwt.encode(
        {
            'user_id': user_id,
            'type': 'refresh',
            'exp': datetime.utcnow() + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            'iat': datetime.utcnow()
        },
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    return access_token, refresh_token

def create_session(user_id, request):
    """
    Создание новой сессии в базе данных
    """
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    session = Session(
        id=session_id,
        user_id=user_id,
        expires_at=expires_at,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string if request.user_agent else None
    )
    
    db.session.add(session)
    db.session.commit()
    
    return session_id

def get_current_user():
    """
    Получение текущего пользователя из запроса (JWT или сессия)  
    """
    user = None
    
    # Метод 1: JWT из заголовка Authorization
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            if payload.get('type') == 'access':
                user = User.query.get(payload['user_id'])
                
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass
    
    # Метод 2: Сессия из cookie
    if not user:
        session_id = request.cookies.get(current_app.config['SESSION_COOKIE_NAME'])
        if session_id:
            session = Session.query.filter(
                Session.id == session_id,
                Session.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                user = session.user
    
    if user and user.is_active:
        return user
    
    return None

def refresh_access_token(refresh_token):
    """
    Получение нового access токена с использованием refresh токена
    """
    try:
        payload = jwt.decode(
            refresh_token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        
        if payload.get('type') != 'refresh':
            return {'success': False, 'error': 'Неверный тип токена'}
        
        user_id = payload['user_id']
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return {'success': False, 'error': 'Пользователь не найден или неактивен'}
        
        # Генерация нового access токена
        access_token = jwt.encode(
            {
                'user_id': user_id,
                'type': 'access',
                'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
                'iat': datetime.utcnow()
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return {'success': True, 'access_token': access_token}
        
    except jwt.ExpiredSignatureError:
        return {'success': False, 'error': 'Refresh токен истек'}
    except jwt.InvalidTokenError:
        return {'success': False, 'error': 'Неверный refresh токен'}

def invalidate_user_sessions(user_id, exclude_session_id=None):
    """
    Инвалидация всех сессий пользователя
    """
    query = Session.query.filter_by(user_id=user_id)
    
    if exclude_session_id:
        query = query.filter(Session.id != exclude_session_id)
    
    query.delete()
    db.session.commit()