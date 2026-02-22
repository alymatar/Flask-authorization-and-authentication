"""
Пользовательские декораторы для аутентификации и авторизации
"""
from functools import wraps
from flask import request, jsonify
from app.services.auth_service import get_current_user

def login_required(f):
    """
    Декоратор, требующий аутентификации
    
    Использование:
        @app.route('/protected')
        @login_required
        def protected():
            return {'message': 'Вы аутентифицированы'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if not user:
            return jsonify({
                'error': 'Не авторизован',
                'message': 'Требуется аутентификация'
            }), 401
        
        # Attach user to request for use in view
        request.user = user
        
        return f(*args, **kwargs)
    
    return decorated_function

def permission_required(element_name, permission_type='read'):
    """
    Декоратор для проверки конкретных разрешений
        
    Использование:
        @app.route('/products')
        @permission_required('products', 'read')
        def get_products():
            return {'products': [...]}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Authentication required'
                }), 401
            
            # Get resource owner ID from kwargs if present (for ownership checks)
            resource_owner_id = kwargs.get('user_id') or kwargs.get('owner_id')
            
            # Check permission
            if user.has_permission(element_name, permission_type, resource_owner_id):
                request.user = user
                return f(*args, **kwargs)
            else:
                return jsonify({
                    'error': 'Доступ запрещен',
                    'message': f'У вас нет разрешения на {permission_type} {element_name}'
                }), 403
        
        return decorated_function
    return decorator

def admin_required(f):
    """
    Декоратор для маршрутов, доступных только администраторам
    
    Использование:
        @app.route('/admin/users')
        @admin_required
        def admin_panel():
            return {'users': [...]}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if not user:
            return jsonify({
                'error': 'Не авторизован',
                'message': 'Требуется аутентификация'
            }), 401
        
        # Check if user has admin role
        if user.role.name != 'admin':
            return jsonify({
                'error': 'Доступ запрещен',
                'message': 'Требуются права администратора'
            }), 403
        
        request.user = user
        return f(*args, **kwargs)
    
    return decorated_function

def optional_login(f):
    """
    Декоратор, который не требует аутентификации, но прикрепляет пользователя, если он присутствует
    
    Использование:
        @app.route('/public')
        @optional_login
        def public():
            if hasattr(request, 'user'):
                return {'message': f'Привет, {request.user.email}'}
            return {'message': 'Привет, анонимный пользователь'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user:
            request.user = user
        return f(*args, **kwargs)
    
    return decorated_function