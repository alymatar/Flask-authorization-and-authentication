import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask настройки
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Настройки базы данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:password3@localhost:5432/databse')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # Настройки JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)))
    
    # Настройки сессии
    SESSION_COOKIE_NAME = 'session_id'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 дней
    
    # CORS настройки
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000']
    
    # Пагинация
    ITEMS_PER_PAGE = 20