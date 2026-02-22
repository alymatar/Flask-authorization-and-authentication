"""
Тесты аутентификации
"""
import pytest
import json
from app import create_app, db
from app.models import User, Role, Session

@pytest.fixture
def app():
    """Создание тестового приложения"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Использование SQLite в памяти для тестов

    with app.app_context():
        db.create_all()

        # Создание тестовых ролей только если они не существуют
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Admin', is_system_role=True)
            db.session.add(admin_role)
        
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user', description='User', is_system_role=True)
            db.session.add(user_role)
        
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Создание тестового клиента"""
    return app.test_client()

def test_register_user(client):
    """Тест регистрации пользователя"""
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!',
        'password_confirm': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == 'Пользователь успешно зарегистрирован'
    assert data['user']['email'] == 'test@example.com'

def test_register_duplicate_email(client):
    """Тест регистрации с дублирующимся email"""
    # First registration
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!',
        'password_confirm': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    # Second registration with same email
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!',
        'password_confirm': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Email уже зарегистрирован'

def test_register_password_mismatch(client):
    """Тест регистрации с несовпадающими паролями"""
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!',
        'password_confirm': 'Test456!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'errors' in data

def test_register_password_too_weak(client):
    """Тест регистрации со слабым паролем"""
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'password',
        'password_confirm': 'password',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'password' in data['errors']

def test_login_success(client):
    """Тест успешного входа"""
    # Сначала регистрируем пользователя
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!',
        'password_confirm': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    # Вход
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'Test123!'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Вход выполнен успешно'
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert 'session_id' in response.headers.get('Set-Cookie', '')

def test_login_invalid_credentials(client):
    """Тест входа с неверными учетными данными"""
    response = client.post('/api/auth/login', json={
        'email': 'wrong@example.com',
        'password': 'wrongpass'
    })
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['error'] == 'Неверный email или пароль'

def test_logout(client):
    """Тест выхода"""
    # Регистрация и вхо
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!',
        'password_confirm': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    login_response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'Test123!'
    })
    
    # Получение cookie сессии
    session_cookie = login_response.headers.get('Set-Cookie')
    
    # Выход
    response = client.post('/api/auth/logout', headers={
        'Cookie': session_cookie
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Выход выполнен успешно'
    
    # Попытка доступа к защищенному маршруту
    response = client.get('/api/auth/me', headers={
        'Cookie': session_cookie
    })
    
    assert response.status_code == 401

def test_refresh_token(client):
    """Тест обновления токена"""
    # Регистрация и вход
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!',
        'password_confirm': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    login_response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'Test123!'
    })
    
    login_data = json.loads(login_response.data)
    refresh_token = login_data['refresh_token']
    
    # Обновление токена
    response = client.post('/api/auth/refresh', json={
        'refresh_token': refresh_token
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data

def test_get_current_user(client):
    """Тест получения текущего пользователя"""
    # Регистрация и вход
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!',
        'password_confirm': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    login_response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'Test123!'
    })
    
    login_data = json.loads(login_response.data)
    access_token = login_data['access_token']
    
    # Получение текущего пользователя
    response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['user']['email'] == 'test@example.com'