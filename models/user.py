#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المستخدم
User Model
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    """نموذج المستخدم في اللعبة"""
    
    __tablename__ = 'users'
    
    # المعرف الأساسي
    id = db.Column(db.Integer, primary_key=True)
    
    # معلومات المستخدم الأساسية
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # معلومات الملف الشخصي
    display_name = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # معلومات الحالة
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_online = db.Column(db.Boolean, default=False, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # معلومات التسجيل
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # إحصائيات اللعبة
    total_games = db.Column(db.Integer, default=0, nullable=False)
    games_won = db.Column(db.Integer, default=0, nullable=False)
    games_lost = db.Column(db.Integer, default=0, nullable=False)
    
    # العلاقات
    players = db.relationship('Player', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    statistics = db.relationship('UserStatistics', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, username, display_name, password=None, email=None):
        """إنشاء مستخدم جديد"""
        self.username = username
        self.display_name = display_name
        self.email = email
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """تعيين كلمة مرور مشفرة"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_seen(self):
        """تحديث آخر ظهور"""
        self.last_seen = datetime.utcnow()
        self.is_online = True
        db.session.commit()
    
    def set_offline(self):
        """تعيين المستخدم كغير متصل"""
        self.is_online = False
        self.last_seen = datetime.utcnow()
        db.session.commit()
    
    def get_win_rate(self):
        """حساب معدل الفوز"""
        if self.total_games == 0:
            return 0.0
        return (self.games_won / self.total_games) * 100
    
    def update_game_stats(self, won=False):
        """تحديث إحصائيات اللعبة"""
        self.total_games += 1
        if won:
            self.games_won += 1
        else:
            self.games_lost += 1
        db.session.commit()
    
    def to_dict(self, include_stats=False):
        """تحويل المستخدم إلى قاموس"""
        data = {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat()
        }
        
        if include_stats:
            data.update({
                'total_games': self.total_games,
                'games_won': self.games_won,
                'games_lost': self.games_lost,
                'win_rate': self.get_win_rate()
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def __str__(self):
        return self.display_name