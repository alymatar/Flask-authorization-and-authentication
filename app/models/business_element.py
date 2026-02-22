"""
Модель business_element - представляет ресурсы, которые нуждаются в защите
"""
from app import db
from datetime import datetime

class BusinessElement(db.Model):
    # Создать таблицу business_elements
    __tablename__ = 'business_elements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # отношение с таблицей AccessRoleRule
    access_rules = db.relationship('AccessRoleRule', backref='element', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BusinessElement {self.name}>'
    
    def to_dict(self):
        """Преобразить элемент в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }