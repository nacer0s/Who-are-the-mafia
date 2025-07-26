#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حزمة واجهات برمجة التطبيقات
API Package
"""

from .auth_routes import auth_bp
from .game_routes import game_bp
from .room_routes import room_bp
from .stats_routes import stats_bp

__all__ = [
    'auth_bp',
    'game_bp', 
    'room_bp',
    'stats_bp'
]