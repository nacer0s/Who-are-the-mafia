#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعدادات التطبيق
Application Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """إعدادات التطبيق الأساسية"""
    
    # إعدادات Flask الأساسية
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # إعدادات قاعدة البيانات
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')
    
    if DATABASE_TYPE == 'mysql':
        MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
        MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
        MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
        MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'mafia_game')
        
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    else:
        # استخدام SQLite بشكل افتراضي
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mafia_game.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # إعدادات اللعبة
    MIN_PLAYERS = int(os.environ.get('MIN_PLAYERS', 4))
    MAX_PLAYERS = int(os.environ.get('MAX_PLAYERS', 20))
    GAME_TIME_LIMIT = int(os.environ.get('GAME_TIME_LIMIT', 300))  # 5 دقائق
    VOTE_TIME_LIMIT = int(os.environ.get('VOTE_TIME_LIMIT', 60))   # دقيقة واحدة
    
    # إعدادات الذكاء الاصطناعي
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # إعدادات الشبكة
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5000))
    
    # إعدادات الملفات
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # إعدادات الأمان
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # إعدادات اللغة
    LANGUAGES = ['ar']
    DEFAULT_LANGUAGE = 'ar'

class DevelopmentConfig(Config):
    """إعدادات التطوير"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """إعدادات الإنتاج"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """إعدادات الاختبار"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# تحديد الإعدادات حسب البيئة
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
