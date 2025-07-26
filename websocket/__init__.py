#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حزمة WebSocket
WebSocket Package
"""

from .game_events import register_game_events
from .room_events import register_room_events
from .chat_events import register_chat_events
from .voice_events import register_voice_events

__all__ = [
    'register_game_events',
    'register_room_events',
    'register_chat_events', 
    'register_voice_events'
]