"""
Модель session для отслеживания сеансов пользователей.
"""
from app import db
from datetime import datetime

class Session(db.Model):
    # Создать таблицу sessions
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(255), primary_key=True)  
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Session {self.id[:8]}... for user {self.user_id}>'
    
    def is_valid(self):
        """Проверить действителен ли сеанс по-прежнему"""
        return datetime.utcnow() < self.expires_at
    
    def to_dict(self):
        """Преобразить сеанс в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }