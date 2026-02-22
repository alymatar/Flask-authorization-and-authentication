"""
Схемы пользователей для валидации запросов и ответов
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
import re

class UserRegisterSchema(Schema):
    """Схема для регистрации пользователя"""
    
    email = fields.Email(required=True, error_messages={
        'required': 'Требуется email',
        'invalid': 'Неверный формат email'
    })
    
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=50),
        error_messages={
            'required': 'Требуется пароль',
            'min': 'Пароль должен содержать минимум 6 символов'
        }
    )
    
    password_confirm = fields.Str(
        required=True,
        error_messages={'required': 'Требуется подтверждение пароля'}
    )
    
    first_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={
            'required': 'Требуется имя',
            'min': 'Имя не должно быть пустым'
        }
    )
    
    last_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={
            'required': 'Требуется фамилия',
            'min': 'Фамилия не должна быть пустой'
        }
    )
    
    patronymic = fields.Str(allow_none=True, validate=validate.Length(max=100))
    
    @validates('password')
    def validate_password_strength(self, value):
        """Проверка сложности пароля"""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Пароль должен содержать минимум одну заглавную букву')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Пароль должен содержать минимум одну строчную букву')
        if not re.search(r'[0-9]', value):
            raise ValidationError('Пароль должен содержать минимум одну цифру')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError('Пароль должен содержать минимум один специальный символ')
    
    @validates('password_confirm')
    def validate_password_match(self, value):
        """Проверка совпадения паролей."""
        if self.context.get('password') != value:
            raise ValidationError('Пароли не совпадают')
    
    @post_load
    def remove_password_confirm(self, data, **kwargs):
        """Удаление поля password_confirm после валидации"""
        data.pop('password_confirm', None)
        return data


class UserLoginSchema(Schema):
    """Схема для входа пользователя"""
    
    email = fields.Email(
        required=True,
        error_messages={
            'required': 'Email is required',
            'invalid': 'Invalid email format'
        }
    )
    
    password = fields.Str(
        required=True,
        error_messages={'required': 'Password is required'}
    )


class UserUpdateSchema(Schema):
    """Схема для обновления профиля пользователя."""
    
    first_name = fields.Str(
        validate=validate.Length(min=1, max=100),
        error_messages={'min': 'Имя не должно быть пустым'}
    )
    
    last_name = fields.Str(
        validate=validate.Length(min=1, max=100),
        error_messages={'min': 'Фамилия не должна быть пустой'}
    )
    
    patronymic = fields.Str(allow_none=True, validate=validate.Length(max=100))
    
    email = fields.Email(error_messages={'invalid': 'Неверный формат email'})
    
    @validates('email')
    def validate_email_unique(self, value):
        """Проверка уникальности email"""
        from app.models import User
        from flask import request
        
        if hasattr(request, 'user') and request.user.email == value:
            return
        
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email уже используется')