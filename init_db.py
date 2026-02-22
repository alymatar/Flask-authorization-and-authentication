#!/usr/bin/env python
"""
Complete database initialization script.
Run this to create all tables and populate with initial data.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models import User, Role, BusinessElement, AccessRoleRule, Session
import bcrypt
from datetime import datetime

def init_database():
    """Initialize the entire database with tables and initial data."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("FLASK СИСТЕМА АВТОРИЗАЦИИ - ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
        print("="*60)
        
        # Step 1: Create all tables
        print("\n[1/5] Создание таблиц базы данных...")
        db.create_all()
        print("✅ Таблицы успешно созданы!")
        
        # Step 2: Create roles
        print("\n[2/5] Создание ролей...")
        roles_data = [
            {'name': 'admin', 'description': 'Full system access - can do everything', 'is_system_role': True},
            {'name': 'manager', 'description': 'Can manage content but not system settings', 'is_system_role': True},
            {'name': 'user', 'description': 'Regular user with basic permissions', 'is_system_role': True},
            {'name': 'guest', 'description': 'Read-only access - can only view', 'is_system_role': True}
        ]
        
        created_roles = {}
        for role_data in roles_data:
            role = Role(**role_data)
            db.session.add(role)
            created_roles[role_data['name']] = role
            print(f"  - Создана роль: {role_data['name']}")
        
        db.session.commit()
        print("✅ Роли успешно созданы!")
        
        # Step 3: Create business elements
        print("\n[3/5] Создание бизнес-элементов...")
        elements_data = [
            {'name': 'products', 'description': 'Product management - create, read, update, delete products'},
            {'name': 'orders', 'description': 'Order management - create, view, update orders'},
            {'name': 'users', 'description': 'User management - view and manage user profiles'},
            {'name': 'permissions', 'description': 'Permission management - control access rules'},
            {'name': 'reports', 'description': 'Reports and analytics - view system reports'},
            {'name': 'settings', 'description': 'System settings - configure application'}
        ]
        
        created_elements = {}
        for element_data in elements_data:
            element = BusinessElement(**element_data)
            db.session.add(element)
            created_elements[element_data['name']] = element
            print(f"  - Создан элемент: {element_data['name']}")
        
        db.session.commit()
        print("✅ Бизнес-элементы успешно созданы!")
        
        # Step 4: Create permission rules
        print("\n[4/5] Создание правил разрешений...")
        
        # Admin role - full access to everything
        admin_role = created_roles['admin']
        for element_name, element in created_elements.items():
            rule = AccessRoleRule(
                role_id=admin_role.id,
                element_id=element.id,
                read_permission=True,
                read_all_permission=True,
                create_permission=True,
                update_permission=True,
                update_all_permission=True,
                delete_permission=True,
                delete_all_permission=True
            )
            db.session.add(rule)
        print(f"  - Admin: Полный доступ ко всем {len(created_elements)} элементам")
        
        # Manager role permissions
        manager_role = created_roles['manager']
        
        # Products - full CRUD but cannot delete others
        rule = AccessRoleRule(
            role_id=manager_role.id,
            element_id=created_elements['products'].id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=False
        )
        db.session.add(rule)
        print(f"  - Manager: Продукты - полный доступ, кроме удаления чужих")
        
        # Orders - can view all, create, update own
        rule = AccessRoleRule(
            role_id=manager_role.id,
            element_id=created_elements['orders'].id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        )
        db.session.add(rule)
        print(f"  - Manager: Заказы - просмотр всех, создание, обновление своих")
        
        # Users - can view all but not modify
        rule = AccessRoleRule(
            role_id=manager_role.id,
            element_id=created_elements['users'].id,
            read_permission=True,
            read_all_permission=True,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        )
        db.session.add(rule)
        print(f"  - Manager: Пользователи - только просмотр")
        
        # Reports - can view all
        rule = AccessRoleRule(
            role_id=manager_role.id,
            element_id=created_elements['reports'].id,
            read_permission=True,
            read_all_permission=True,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        )
        db.session.add(rule)
        print(f"  - Manager: Отчеты - просмотр всех")
        
        # Regular User role permissions
        user_role = created_roles['user']
        
        # Products - can read all, create, update/delete own
        rule = AccessRoleRule(
            role_id=user_role.id,
            element_id=created_elements['products'].id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=False,
            delete_permission=True,
            delete_all_permission=False
        )
        db.session.add(rule)
        print(f"  - User: Продукты - чтение всех, создание, обновление/удаление своих")
        
        # Orders - can only manage own orders
        rule = AccessRoleRule(
            role_id=user_role.id,
            element_id=created_elements['orders'].id,
            read_permission=True,
            read_all_permission=False,
            create_permission=True,
            update_permission=True,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        )
        db.session.add(rule)
        print(f"  - User: Заказы - управление только своими заказами")
        
        # Guest role permissions
        guest_role = created_roles['guest']
        
        # Products - read only
        rule = AccessRoleRule(
            role_id=guest_role.id,
            element_id=created_elements['products'].id,
            read_permission=True,
            read_all_permission=True,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        )
        db.session.add(rule)
        print(f"  - Guest: Продукты - только чтение")
        
        db.session.commit()
        
        rule_count = AccessRoleRule.query.count()
        print(f"✅ Успешно создано {rule_count} правил разрешений!")
        
        # Step 5: Create test users
        print("\n[5/5] Создание тестовых пользователей...")
        
        test_users = [
            {
                'email': 'admin@example.com',
                'password': 'Admin123!',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin'
            },
            {
                'email': 'manager@example.com',
                'password': 'Manager123!',
                'first_name': 'Manager',
                'last_name': 'User',
                'role': 'manager'
            },
            {
                'email': 'user@example.com',
                'password': 'User123!',
                'first_name': 'Regular',
                'last_name': 'User',
                'role': 'user'
            },
            {
                'email': 'guest@example.com',
                'password': 'Guest123!',
                'first_name': 'Guest',
                'last_name': 'User',
                'role': 'guest'
            }
        ]
        
        for user_data in test_users:
            role_name = user_data.pop('role')
            role = created_roles[role_name]
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"  - Пользователь {user_data['email']} уже существует, пропускаем...")
                continue
            
            user = User(
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role_id=role.id,
                is_active=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"  - Создан пользователь: {user_data['email']} ({role_name})")
        
        db.session.commit()
        
        user_count = User.query.count()
        print(f"✅ Успешно создано {user_count} тестовых пользователей!")
        
        # Final summary
        print("\n" + "="*60)
        print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ЗАВЕРШЕНА!")
        print("="*60)
        print("\n📊 СВОДКА БАЗЫ ДАННЫХ:")
        print(f"   - Роли: {Role.query.count()}")
        for role in Role.query.all():
            user_count = User.query.filter_by(role_id=role.id).count()
            print(f"     • {role.name}: {user_count} пользователей")
        
        print(f"\n   - Бизнес-элементы: {BusinessElement.query.count()}")
        for element in BusinessElement.query.all():
            print(f"     • {element.name}")
        
        print(f"\n   - Правила разрешений: {AccessRoleRule.query.count()}")
        print(f"   - Всего пользователей: {User.query.count()}")
        
        print("\n🔑 ТЕСТОВЫЕ ПОЛЬЗОВАТЕЛИ:")
        print("   • admin@example.com / Admin123! (admin)")
        print("   • manager@example.com / Manager123! (manager)")
        print("   • user@example.com / User123! (user)")
        print("   • guest@example.com / Guest123! (guest)")
        
        print("\n🚀 ГОТОВО К ИСПОЛЬЗОВАНИЮ!")
        print("   Запустите приложение Flask: python run.py")
        print("   Тестовые эндпоинты: http://localhost:5000/api/auth/login")
        print("="*60)

if __name__ == "__main__":
    init_database()