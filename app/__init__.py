"""
Фабрика приложения Flask
"""
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()

import click
from flask.cli import with_appcontext

def init_db_command():
    """Инициализация базы данных со всеми таблицами"""
    import click
    from app.models import Role, BusinessElement, AccessRoleRule, User, Session
    
    click.echo('Создание всех таблиц базы данных...')
    db.create_all()
    
    click.echo('Создание ролей...')
    roles = [
        {'name': 'admin', 'description': 'Full system access - can do everything', 'is_system_role': True},
        {'name': 'manager', 'description': 'Can manage content but not system settings', 'is_system_role': True},
        {'name': 'user', 'description': 'Regular user with basic permissions', 'is_system_role': True},
        {'name': 'guest', 'description': 'Read-only access', 'is_system_role': True}
    ]
    
    created_roles = {}
    for role_data in roles:
        role = Role(**role_data)
        db.session.add(role)
        created_roles[role_data['name']] = role
    
    db.session.commit()
    click.echo(f"Созданы роли: {', '.join([r.name for r in Role.query.all()])}")
    
    click.echo('Создание бизнес-элементов...')
    elements = [
        {'name': 'products', 'description': 'Product management - create, read, update, delete products'},
        {'name': 'orders', 'description': 'Order management - create, view, update orders'},
        {'name': 'users', 'description': 'User management - view and manage user profiles'},
        {'name': 'permissions', 'description': 'Permission management - control access rules'},
        {'name': 'reports', 'description': 'Reports and analytics'},
        {'name': 'settings', 'description': 'System settings and configuration'}
    ]
    
    created_elements = {}
    for element_data in elements:
        element = BusinessElement(**element_data)
        db.session.add(element)
        created_elements[element_data['name']] = element
    
    db.session.commit()
    click.echo(f"Созданы элементы: {', '.join([e.name for e in BusinessElement.query.all()])}")
    
    click.echo('Создание правил разрешений...')
    
    # Роль администратора - полный доступ ко всему
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
    
    # Права для роли менеджера
    manager_role = created_roles['manager']
    
    # Товары - полное CRUD, но нельзя удалять чужие
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
    
    # Заказы - может просматривать все, создавать, обновлять свои
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
    
    #  Пользователи - может просматривать всех, но не изменять
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
    
    # Отчеты - может просматривать все
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
    
    # Права для роли обычного пользователя
    user_role = created_roles['user']
    
    # Товары - может читать все, создавать, обновлять/удалять свои
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
    
    # Заказы - может управлять только своими заказами
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
    
    # Права для роли гостя
    guest_role = created_roles['guest']
    
    # Товары - только чтение
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
    
    db.session.commit()
    
    permission_count = AccessRoleRule.query.count()
    click.echo(f"Created {permission_count} permission rules")
    
    click.echo('Creating test users...')
    
    # Создание тестовых пользователей с разными ролями
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
        
        user = User(
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            role_id=role.id
        )
        user.set_password(user_data['password'])
        db.session.add(user)
    
    db.session.commit()

    click.echo('\n' + '='*50)
    click.echo('ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ЗАВЕРШЕНА!')
    click.echo('='*50)
    click.echo('\nТестовые пользователи:')
    click.echo('  admin@example.com / Admin123!')
    click.echo('  manager@example.com / Manager123!')
    click.echo('  user@example.com / User123!')
    click.echo('  guest@example.com / Guest123!')
    click.echo('\nСозданные роли:')
    for role in Role.query.all():
        click.echo(f'  - {role.name}: {role.description}')
    click.echo('\nБизнес-элементы:')
    for element in BusinessElement.query.all():
        click.echo(f'  - {element.name}: {element.description}')


def create_app(config_class=Config):
    """
    Фабрика приложения
    Создает и настраивает Flask приложение
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, 
        resources={r"/api/*": {"origins": Config.CORS_ORIGINS}},
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Регистрация  blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.product_routes import product_bp
    from app.routes.order_routes import order_bp
    from app.routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Регистрация обработчиков ошибок
    register_error_handlers(app)
    
    # Создание таблиц базы данных
    with app.app_context():
        db.create_all()
    
    return app

def register_error_handlers(app):
    """Регистрация пользовательских обработчиков ошибок"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': 'Требуется аутентификация'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': 'У вас нет разрешения на доступ к этому ресурсу'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': 'Запрошенный ресурс не был найден'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': 'Что-то пошло не так'}), 500