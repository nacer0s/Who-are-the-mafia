#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أحداث الغرف عبر WebSocket
Room WebSocket Events
"""

from flask import current_app
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from datetime import datetime
from models.message import Message

def register_room_events(socketio):
    """تسجيل أحداث الغرف"""
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """الانضمام إلى غرفة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_code = data.get('room_code', '').upper()
            password = data.get('password')
            
            # الانضمام عبر RoomManager
            room_manager = current_app.room_manager
            success, message = room_manager.join_room(current_user.id, room_code, password)
            
            if success:
                # الانضمام إلى غرفة WebSocket
                join_room(room_code)
                
                # الحصول على معلومات الغرفة
                room = room_manager.get_room(room_code)
                
                # إشعار المستخدم بنجاح الانضمام
                emit('room_joined', {
                    'room': room.to_dict(include_players=True) if room else None,
                    'message': message
                })
                
                # إشعار باقي اللاعبين بانضمام لاعب جديد
                emit('player_joined', {
                    'user_id': current_user.id,
                    'display_name': current_user.display_name,
                    'avatar_url': current_user.avatar_url
                }, room=room_code, include_self=False)
                
                # رسالة نظام
                Message.create_system_message(
                    room.id,
                    f"🎮 انضم {current_user.display_name} إلى الغرفة"
                )
                
                # إرسال الرسالة لجميع اللاعبين
                emit('new_message', {
                    'message': {
                        'id': None,
                        'content': f"🎮 انضم {current_user.display_name} إلى الغرفة",
                        'sender_name': "النظام",
                        'message_type': 'system',
                        'sent_at': datetime.utcnow().isoformat()
                    }
                }, room=room_code)
                
            else:
                emit('error', {'message': message})
                
        except Exception as e:
            emit('error', {'message': f'خطأ في الانضمام: {str(e)}'})
    
    @socketio.on('leave_room')
    def handle_leave_room():
        """مغادرة الغرفة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_manager = current_app.room_manager
            
            # الحصول على الغرفة الحالية
            room = room_manager.get_user_room(current_user.id)
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            room_code = room.room_code
            
            # المغادرة عبر RoomManager
            success, message = room_manager.leave_room(current_user.id)
            
            if success:
                # مغادرة غرفة WebSocket
                leave_room(room_code)
                
                # إشعار المستخدم
                emit('room_left', {'message': message})
                
                # إشعار باقي اللاعبين
                emit('player_left', {
                    'user_id': current_user.id,
                    'display_name': current_user.display_name
                }, room=room_code)
                
                # رسالة نظام
                Message.create_system_message(
                    room.id,
                    f"👋 غادر {current_user.display_name} الغرفة"
                )
                
                # إرسال الرسالة لجميع اللاعبين
                emit('new_message', {
                    'message': {
                        'id': None,
                        'content': f"👋 غادر {current_user.display_name} الغرفة",
                        'sender_name': "النظام",
                        'message_type': 'system',
                        'sent_at': datetime.utcnow().isoformat()
                    }
                }, room=room_code)
                
            else:
                emit('error', {'message': message})
                
        except Exception as e:
            emit('error', {'message': f'خطأ في المغادرة: {str(e)}'})
    
    @socketio.on('set_ready')
    def handle_set_ready(data):
        """تعيين حالة الاستعداد"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            ready = data.get('ready', True)
            
            room_manager = current_app.room_manager
            success, message = room_manager.set_player_ready(current_user.id, ready)
            
            if success:
                # الحصول على الغرفة
                room = room_manager.get_user_room(current_user.id)
                
                if room:
                    # إشعار جميع اللاعبين بتغيير حالة الاستعداد
                    emit('player_ready_changed', {
                        'user_id': current_user.id,
                        'display_name': current_user.display_name,
                        'ready': ready
                    }, room=room.room_code)
                    
                    # التحقق من إمكانية البدء التلقائي
                    if ready and room.auto_start:
                        players = room_manager.get_room_players(room.room_code)
                        all_ready = all(p.is_ready for p in players)
                        enough_players = len(players) >= room.min_players
                        
                        if all_ready and enough_players:
                            # بدء اللعبة تلقائياً
                            game_manager = current_app.game_manager
                            game_success, game_message, game = game_manager.start_game(room.id)
                            
                            if game_success:
                                emit('game_starting', {
                                    'message': 'تم بدء اللعبة تلقائياً!',
                                    'game': game.to_dict() if game else None
                                }, room=room.room_code)
                
                emit('ready_status_updated', {
                    'ready': ready,
                    'message': message
                })
                
            else:
                emit('error', {'message': message})
                
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('update_room_settings')
    def handle_update_room_settings(data):
        """تحديث إعدادات الغرفة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            # التحقق من الصلاحية
            if room.creator_id != current_user.id:
                emit('error', {'message': 'ليس لديك صلاحية تعديل إعدادات الغرفة'})
                return
            
            success, message = room_manager.update_room_settings(
                room.room_code,
                current_user.id,
                **data
            )
            
            if success:
                # إشعار جميع اللاعبين بتحديث الإعدادات
                updated_room = room_manager.get_room(room.room_code)
                emit('room_settings_updated', {
                    'room': updated_room.to_dict(include_players=True),
                    'message': message
                }, room=room.room_code)
                
            else:
                emit('error', {'message': message})
                
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('get_room_info')
    def handle_get_room_info():
        """الحصول على معلومات الغرفة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if room:
                emit('room_info', {
                    'room': room.to_dict(include_players=True)
                })
            else:
                emit('room_info', {'room': None})
                
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """قطع الاتصال"""
        if current_user.is_authenticated:
            try:
                room_manager = current_app.room_manager
                room = room_manager.get_user_room(current_user.id)
                
                if room:
                    room_code = room.room_code
                    
                    # إشعار باقي اللاعبين بقطع الاتصال
                    emit('player_disconnected', {
                        'user_id': current_user.id,
                        'display_name': current_user.display_name
                    }, room=room_code)
                
                # تحديث حالة المستخدم
                room_manager.remove_player_from_all_rooms(current_user.id)
                
            except Exception as e:
                print(f"خطأ في قطع الاتصال: {e}")
    
    return socketio