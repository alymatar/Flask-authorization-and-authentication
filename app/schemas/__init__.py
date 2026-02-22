"""
Пакет схем
"""
from app.schemas.user_schemas import UserRegisterSchema, UserLoginSchema, UserUpdateSchema
from app.schemas.permission_schemas import PermissionRuleSchema

__all__ = [
    'UserRegisterSchema',
    'UserLoginSchema',
    'UserUpdateSchema',
    'PermissionRuleSchema'
]