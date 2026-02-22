"""
Модель access_role_rule - определяет, что каждая роль может делать с каждым бизнес-элементом.
"""
from app import db
from datetime import datetime

class AccessRoleRule(db.Model):
# Создать таблицу с именем access_role_rules
    __tablename__ = 'access_role_rules'
      
    id = db.Column(db.Integer, primary_key=True)  
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)  
    element_id = db.Column(db.Integer, db.ForeignKey('business_elements.id'), nullable=False)  
    
 
    read_permission = db.Column(db.Boolean, default=False, nullable=False)  
    read_all_permission = db.Column(db.Boolean, default=False, nullable=False)  
    
   
    create_permission = db.Column(db.Boolean, default=False, nullable=False) 
        
    update_permission = db.Column(db.Boolean, default=False, nullable=False) 
    update_all_permission = db.Column(db.Boolean, default=False, nullable=False) 
       
    delete_permission = db.Column(db.Boolean, default=False, nullable=False)  
    delete_all_permission = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('role_id', 'element_id', name='unique_role_element'),
    )
    
    def __repr__(self):
        return f'<AccessRule role={self.role_id} element={self.element_id}>'
    
    def to_dict(self):
        """Преобразование правила в словарь"""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'element_id': self.element_id,
            'element_name': self.element.name if self.element else None,
            'read_permission': self.read_permission,
            'read_all_permission': self.read_all_permission,
            'create_permission': self.create_permission,
            'update_permission': self.update_permission,
            'update_all_permission': self.update_all_permission,
            'delete_permission': self.delete_permission,
            'delete_all_permission': self.delete_all_permission,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }