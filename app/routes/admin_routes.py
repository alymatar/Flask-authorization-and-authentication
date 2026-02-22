"""
Административные маршруты для управления ролями, разрешениями и пользователями
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Role, User, BusinessElement, AccessRoleRule
from app.utils.decorators import admin_required
from app.schemas.permission_schemas import PermissionRuleSchema

admin_bp = Blueprint('admin', __name__)

# ========== Управление ролями ==========

@admin_bp.route('/roles', methods=['GET'])
@admin_required
def get_roles():
    """Получить все роли"""
    roles = Role.query.all()
    return jsonify({'roles': [r.to_dict() for r in roles]})

@admin_bp.route('/roles', methods=['POST'])
@admin_required
def create_role():
    """Создать новую роль"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Требуется название роли'}), 400
    
    if Role.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Роль уже существует'}), 400
    
    role = Role(
        name=data['name'],
        description=data.get('description', ''),
        is_system_role=False
    )
    
    db.session.add(role)
    db.session.commit()
    
    return jsonify({
        'message': 'Роль успешно создана',
        'role': role.to_dict()
    }), 201

@admin_bp.route('/roles/<int:role_id>', methods=['PUT'])
@admin_required
def update_role(role_id):
    """Обновить роль"""
    role = Role.query.get_or_404(role_id)
    
    if role.is_system_role:
        return jsonify({'error': 'Нельзя изменять системную роль'}), 400
    
    data = request.get_json()
    
    if 'name' in data:
        role.name = data['name']
    if 'description' in data:
        role.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Роль успешно обновлена',
        'role': role.to_dict()
    })

@admin_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@admin_required
def delete_role(role_id):
    """Удаление роли"""
    role = Role.query.get_or_404(role_id)
    
    if role.is_system_role:
        return jsonify({'error': 'Нельзя удалять системную роль'}), 400
    
    
    if role.users.count() > 0:
        return jsonify({'error': 'Нельзя удалять роль, назначенную пользователям'}), 400
    
    db.session.delete(role)
    db.session.commit()
    
    return jsonify({'message': 'Роль успешно удалена'})

# ========== Управление бизнес-элементами ==========

@admin_bp.route('/elements', methods=['GET'])
@admin_required
def get_elements():
    """Получить все бизнес-элементы."""
    elements = BusinessElement.query.all()
    return jsonify({'elements': [e.to_dict() for e in elements]})

@admin_bp.route('/elements', methods=['POST'])
@admin_required
def create_element():
    """Создать новый бизнес-элемент"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Требуется название элемента'}), 400
    
    if BusinessElement.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Элемент уже существует'}), 400
    
    element = BusinessElement(
        name=data['name'],
        description=data.get('description', '')
    )
    
    db.session.add(element)
    db.session.commit()
    
    return jsonify({
        'message': 'Бизнес-элемент успешно создан',
        'element': element.to_dict()
    }), 201

# ========== Управление правилами разрешений ==========

@admin_bp.route('/permissions', methods=['GET'])
@admin_required
def get_permissions():
    """ Получить все правила доступа """
    rules = AccessRoleRule.query.all()
    return jsonify({'permissions': [r.to_dict() for r in rules]})

@admin_bp.route('/permissions', methods=['POST'])
@admin_required
def create_permission():
    """Создать новое правило разрешений"""
    data = request.get_json()
    
    schema = PermissionRuleSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    existing = AccessRoleRule.query.filter_by(
        role_id=data['role_id'],
        element_id=data['element_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'Правило доступа для этой роли и элемента уже существует'}), 400
    
    rule = AccessRoleRule(**data)
    db.session.add(rule)
    db.session.commit()
    
    return jsonify({
        'message': 'Правило доступа успешно создано',
        'permission': rule.to_dict()
    }), 201

@admin_bp.route('/permissions/<int:rule_id>', methods=['PUT'])
@admin_required
def update_permission(rule_id):
    """ Обновить правило доступа """
    rule = AccessRoleRule.query.get_or_404(rule_id)
    data = request.get_json()
    
    permission_fields = [
        'read_permission', 'read_all_permission', 'create_permission',
        'update_permission', 'update_all_permission', 'delete_permission',
        'delete_all_permission'
    ]
    
    for field in permission_fields:
        if field in data:
            setattr(rule, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Правило доступа успешно обновлено',
        'permission': rule.to_dict()
    })

@admin_bp.route('/permissions/<int:rule_id>', methods=['DELETE'])
@admin_required
def delete_permission(rule_id):
    """ Удалить правило доступа """
    rule = AccessRoleRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    
    return jsonify({'message': 'Правило доступа успешно удалено'})

# ========== Управление ролями пользователей ==========

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """ Получить всех пользователей """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = User.query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'users': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def change_user_role(user_id):
    """ Изменить роль пользователя """
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    role_id = data.get('role_id')
    if not role_id:
        return jsonify({'error': 'Требуется ID роли'}), 400
    
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'error': 'Роль не найдена'}), 404
    
    old_role = user.role.name
    user.role_id = role_id
    db.session.commit()
    
    return jsonify({
        'message': f'Роль пользователя изменена с {old_role} на {role.name}',
        'user': user.to_dict()
    })

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """ Получить статистику """
    from datetime import datetime, timedelta
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_roles = Role.query.count()
    total_permissions = AccessRoleRule.query.count()
    
    # Users registered in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    new_users = User.query.filter(User.created_at > yesterday).count()
    
    return jsonify({
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'total_roles': total_roles,
            'total_permissions': total_permissions,
            'new_users_24h': new_users
        }
    })