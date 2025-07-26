#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نماذج قاعدة البيانات
Database Models Package
"""

from flask_sqlalchemy import SQLAlchemy

# إنشاء كائن قاعدة البيانات
db = SQLAlchemy()

def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    # استيراد جميع النماذج
    from .user import User
    from .room import Room
    from .game import Game
    from .player import Player
    from .message import Message
    from .game_log import GameLog
    from .statistics import UserStatistics
    
    # إنشاء الجداول
    db.create_all()
    print("✅ تم إنشاء جداول قاعدة البيانات بنجاح")

# تصدير النماذج للاستخدام الخارجي
from .user import User
from .room import Room
from .game import Game
from .player import Player
from .message import Message
from .game_log import GameLog
from .statistics import UserStatistics

__all__ = [
    'db', 'init_db', 'User', 'Room', 'Game', 
    'Player', 'Message', 'GameLog', 'UserStatistics'
]