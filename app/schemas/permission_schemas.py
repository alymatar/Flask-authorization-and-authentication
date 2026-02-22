"""
Схемы разрешений для валидации запросов и ответов
"""
from marshmallow import Schema, fields, validate, validates, ValidationError

class PermissionRuleSchema(Schema):
    """Схема для создания/обновления правил разрешений"""
    
    role_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            'required': 'Требуется ID роли',
            'min': 'ID роли должен быть положительным'
        }
    )
    
    element_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            'required': 'Требуется ID элемента',
            'min': 'ID элемента должен быть положительным'
        }
    )
    
    read_permission = fields.Bool(missing=False)
    read_all_permission = fields.Bool(missing=False)
    create_permission = fields.Bool(missing=False)
    update_permission = fields.Bool(missing=False)
    update_all_permission = fields.Bool(missing=False)
    delete_permission = fields.Bool(missing=False)
    delete_all_permission = fields.Bool(missing=False)
    
    @validates('role_id')
    def validate_role_exists(self, value):
        """Проверка существования роли"""
        from app.models import Role
        if not Role.query.get(value):
            raise ValidationError('Роль не найдена')
    
    @validates('element_id')
    def validate_element_exists(self, value):
        """Проверка существования бизнес-элемента"""
        from app.models import BusinessElement
        if not BusinessElement.query.get(value):
            raise ValidationError('Бизнес-элемент не найден')


class RoleCreateSchema(Schema):
    """Схема для создания роли"""
    
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=50),
        error_messages={
            'required': 'Требуется название роли',
            'min': 'Название роли должно содержать минимум 2 символа'
        }
    )
    
    description = fields.Str(allow_none=True, validate=validate.Length(max=255))


class BusinessElementCreateSchema(Schema):
    """Схема для создания бизнес-элемента"""
    
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={
            'required': 'Требуется название элемента',
            'min': 'Название элемента должно содержать минимум 2 символа'
        }
    )
    
    description = fields.Str(allow_none=True, validate=validate.Length(max=255))