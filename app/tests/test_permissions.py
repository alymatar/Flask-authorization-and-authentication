"""
Тесты разрешений
"""
import pytest
import json
from app import create_app, db
from app.models import User, Role, BusinessElement, AccessRoleRule

@pytest.fixture
def app():
    """Создание тестового приложения с данными разрешений"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()

        # Создание ролей
        admin_role = Role(name='admin', description='Admin', is_system_role=True)
        user_role = Role(name='user', description='User', is_system_role=True)
        db.session.add_all([admin_role, user_role])
        db.session.commit()
        db.session.refresh(admin_role)
        db.session.refresh(user_role)
        
        # Создание бизнес-элементов
        products = BusinessElement(name='products', description='Products')
        orders = BusinessElement(name='orders', description='Orders')
        db.session.add_all([products, orders])
        db.session.commit()
        db.session.refresh(products)
        db.session.refresh(orders)
        
        # Создание правил разрешений для роли пользователя
        # Товары - может читать все, создавать, обновлять/удалять свои
        user_products_rule = AccessRoleRule(
            role_id=user_role.id,
            element_id=products.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=False,
            delete_permission=True,
            delete_all_permission=False
        )
        db.session.add(user_products_rule)
        
        # Заказы - может управлять только своими заказами
        user_orders_rule = AccessRoleRule(
            role_id=user_role.id,
            element_id=orders.id,
            read_permission=True,
            read_all_permission=False,
            create_permission=True,
            update_permission=True,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        )
        db.session.add(user_orders_rule)
        
        # Создание правил разрешений для роли администратора (полный доступ)
        admin_products_rule = AccessRoleRule(
            role_id=admin_role.id,
            element_id=products.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=True
        )
        db.session.add(admin_products_rule)
        
        admin_orders_rule = AccessRoleRule(
            role_id=admin_role.id,
            element_id=orders.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=True
        )
        db.session.add(admin_orders_rule)
        
        db.session.commit()
        
        # Создание тестовых пользователей
        admin_user = User(
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            role_id=admin_role.id
        )
        admin_user.set_password('Admin123!')
        db.session.add(admin_user)
        
        regular_user = User(
            email='user@test.com',
            first_name='Regular',
            last_name='User',
            role_id=user_role.id
        )
        regular_user.set_password('User123!')
        db.session.add(regular_user)
        
        db.session.commit()

        regular_user2= User(
            email='user2@test.com',
            first_name='Regular',
            last_name='User2',
            role_id=user_role.id
        )
        regular_user2.set_password('User123!')
        db.session.add(regular_user2)
        
        db.session.commit()
        
        # Проверка созданных разрешений
        user_permissions = AccessRoleRule.query.filter_by(role_id=user_role.id).all()
        print(f"\nСоздано {len(user_permissions)} правил разрешений для роли пользователя:")
        for rule in user_permissions:
            element = BusinessElement.query.get(rule.element_id)
            print(f"  - {element.name}: чтение={rule.read_permission}, чтение_всех={rule.read_all_permission}, создание={rule.create_permission}, обновление={rule.update_permission}")
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Создание тестового клиента"""
    return app.test_client()

def test_admin_can_access_admin_route(client):
    """Тест доступа администратора к маршрутам администратора"""
    # Вход как администратор
    login_response = client.post('/api/auth/login', json={
        'email': 'admin@test.com',
        'password': 'Admin123!'
    })
    
    assert login_response.status_code == 200
    access_token = json.loads(login_response.data)['access_token']
    
    # Доступ к статистике администратора
    response = client.get('/api/admin/stats', headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    assert response.status_code == 200

def test_user_cannot_access_admin_route(client):
    """Тест, что обычный пользователь не может получить доступ к маршрутам администратора"""
    # Вход как обычный пользователь
    login_response = client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'User123!'
    })
    
    assert login_response.status_code == 200
    access_token = json.loads(login_response.data)['access_token']
    
    # Попытка доступа к статистике администратора
    response = client.get('/api/admin/stats', headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    assert response.status_code == 403

def test_user_can_read_all_products(client):
    """Тест, что пользователь может читать все товары"""
    # Вход как обычный пользователь
    login_response = client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'User123!'
    })
    
    assert login_response.status_code == 200
    access_token = json.loads(login_response.data)['access_token']
    
    # Получение товаров
    response = client.get('/api/products', headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['products']) > 0


def test_user_can_create_product(client):
    """Тест, что пользователь может создавать товар"""
    # Вход как обычный пользователь
    login_response = client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'User123!'
    })
    
    assert login_response.status_code == 200
    access_token = json.loads(login_response.data)['access_token']
    
    # Создание товара
    response = client.post('/api/products', json={
        'name': 'Test Product',
        'price': 99.99,
        'category': 'Test'
    }, headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    assert response.status_code == 201

def test_admin_can_update_others_product(client):
    """Тест, что администратор может обновлять чужой товар"""
    # Сначала вход как обычный пользователь для создания товара
    user_login = client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'User123!'
    })
    
    assert user_login.status_code == 200
    user_token = json.loads(user_login.data)['access_token']
    
    # Создание товара как обычный пользователь
    create_response = client.post('/api/products', json={
        'name': 'User Product',
        'price': 99.99
    }, headers={
        'Authorization': f'Bearer {user_token}'
    })
    
    assert create_response.status_code == 201
    product_data = json.loads(create_response.data)
    product_id = product_data['product']['id']
    
    # Вход как администратор
    admin_login = client.post('/api/auth/login', json={
        'email': 'admin@test.com',
        'password': 'Admin123!'
    })
    
    assert admin_login.status_code == 200
    admin_token = json.loads(admin_login.data)['access_token']
    
    # Попытка обновить товар пользователя как администратор (должно работать)
    response = client.put(f'/api/products/{product_id}', json={
        'name': 'Admin Updated Product',
        'price': 199.99
    }, headers={
        'Authorization': f'Bearer {admin_token}'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['product']['name'] == 'Admin Updated Product'

def test_user_cannot_update_others_product(client):
    """Тест, что пользователь не может обновлять чужой товар"""
    # Вход как пользователь1
    user1_login = client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'User123!'
    })
    
    assert user1_login.status_code == 200
    user1_token = json.loads(user1_login.data)['access_token']
    
    # Создание товара как пользователь1
    create_response = client.post('/api/products', json={
        'name': 'User1 Product',
        'price': 99.99
    }, headers={
        'Authorization': f'Bearer {user1_token}'
    })
    
    assert create_response.status_code == 201
    product_data = json.loads(create_response.data)
    product_id = product_data['product']['id']
    
    # Вход как пользователь2
    user2_login = client.post('/api/auth/login', json={
        'email': 'user2@test.com',
        'password': 'User123!'
    })
    
    assert user2_login.status_code == 200
    user2_token = json.loads(user2_login.data)['access_token']
    
    # Попробовать обновить продукт user2 как user1 (должен произойти сбой, потому что у user1 нет update_permission)
    response = client.put(f'/api/products/{product_id}', json={
        'name': 'Admin Updated',
        'price': 199.99
    }, headers={
        'Authorization': f'Bearer {user2_token}'
    })
    
    assert response.status_code == 403

def test_user_can_create_order(client):
    """Тест, что пользователь может создавать заказ"""
    #  Вход как обычный пользователь
    login_response = client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'User123!'
    })
    
    assert login_response.status_code == 200
    access_token = json.loads(login_response.data)['access_token']
    
    # Создание заказа
    response = client.post('/api/orders', json={
        'items': [{'product_id': 1, 'quantity': 1}],
        'total': 99.99
    }, headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    assert response.status_code == 201