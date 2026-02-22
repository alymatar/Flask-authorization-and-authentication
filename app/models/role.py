"""
модель role - для управления доступом на основе ролей
"""
from app import db
from datetime import datetime

class Role(db.Model):
    # Создать таблицу roles
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    is_system_role = db.Column(db.Boolean, default=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # отношение с таблицей AccessRoleRule
    access_rules = db.relationship('AccessRoleRule', backref='role', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def to_dict(self):
        """Преобразить роль в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_system_role': self.is_system_role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }