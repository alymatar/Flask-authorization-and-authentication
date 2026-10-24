"""
Модель user для аутентификации и управления профилями
"""
from app import db
from datetime import datetime
import bcrypt

class User(db.Model):
    # Создать таблицу users
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    
    # отношение с таблицей roles и session
    role = db.relationship('Role', backref='users', lazy='joined')
    sessions = db.relationship('Session', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """
        Хешируються и устанавливается пароль с помощью bcrypt
        """
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """
        Проверить соответствие пароля сохраненному хэшу
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @property
    def full_name(self):
        """Получить полное имя пользователя"""
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)
    
    def to_dict(self):
        """Преобразить пользователя в словарь"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'patronymic': self.patronymic,
            'full_name': self.full_name,
            'role': self.role.name if self.role else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def has_permission(self, element_name, permission_type, resource_owner_id=None):
        """
        Проверить есть ли у пользователя определенные разрешения для бизнес-элемента
        """
        from app.models.access_role_rule import AccessRoleRule
        from app.models.business_element import BusinessElement
        
        # Получить правило разрешений для роли пользователя и элемента 
        rule = AccessRoleRule.query\
            .join(BusinessElement)\
            .filter(
                AccessRoleRule.role_id == self.role_id,
                BusinessElement.name == element_name
            ).first()
        
        if not rule:
            return False

        # "*_all" checks, used by list endpoints to decide whether to filter by owner
        if permission_type in ('read_all', 'update_all', 'delete_all'):
            return getattr(rule, f'{permission_type}_permission')

        # No specific resource yet (collection routes): allow if the role can act
        # on at least its own records; the view then filters by owner.
        if resource_owner_id is None and permission_type in ('read', 'update', 'delete'):
            return (getattr(rule, f'{permission_type}_permission')
                    or getattr(rule, f'{permission_type}_all_permission'))
        
        # Проверить конкретный тип разрешения
        if permission_type == 'read':
            if rule.read_all_permission:
                return True
            if rule.read_permission and resource_owner_id == self.id:
                return True
        
        elif permission_type == 'create':
            return rule.create_permission
        
        elif permission_type == 'update':
            if rule.update_all_permission:
                return True
            if rule.update_permission and resource_owner_id == self.id:
                return True
        
        elif permission_type == 'delete':
            if rule.delete_all_permission:
                return True
            if rule.delete_permission and resource_owner_id == self.id:
                return True
        
        return False
    
    def update_last_login(self, ip_address):
        """Обновить последнюю регистрационную информацию"""
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        db.session.commit()