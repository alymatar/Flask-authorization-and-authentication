"""
permission_service - вспомогательные функции для проверки прав доступа
"""
from app.models import AccessRoleRule, BusinessElement

def check_permission(user, element_name, permission_type, resource_owner_id=None):
    """
    Проверка наличия у пользователя разрешения.
    Обертка вокруг user.has_permission для сервисного слоя
    """
    return user.has_permission(element_name, permission_type, resource_owner_id)

def get_user_permissions(user):
    """
   Получение всех разрешений пользователя, сгруппированных по элементам
    """
    rules = AccessRoleRule.query.filter_by(role_id=user.role_id).all()
    
    permissions = {}
    for rule in rules:
        element_name = rule.element.name
        permissions[element_name] = {
            'read': rule.read_permission,
            'read_all': rule.read_all_permission,
            'create': rule.create_permission,
            'update': rule.update_permission,
            'update_all': rule.update_all_permission,
            'delete': rule.delete_permission,
            'delete_all': rule.delete_all_permission
        }
    
    return permissions

def has_any_permission(user, element_name, permissions):
    """
    Проверка наличия у пользователя любого из указанных разрешений
    """
    for permission_type in permissions:
        if user.has_permission(element_name, permission_type):
            return True
    return False

def get_accessible_resources(user, element_name, resources):
    """
    Фильтрация ресурсов на основе разрешений пользователя
    """
    if user.has_permission(element_name, 'read_all'):
        return resources
    
    return [r for r in resources if r.get('owner_id') == user.id]