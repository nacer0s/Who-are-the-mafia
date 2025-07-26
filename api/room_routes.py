#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات الغرف
Room Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Room, Player
from models.room import RoomStatus

room_bp = Blueprint('room', __name__)

@room_bp.route('/create', methods=['POST'])
@login_required
def create_room():
    """إنشاء غرفة جديدة"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'اسم الغرفة مطلوب'
            }), 400
        
        # إعدادات الغرفة
        room_settings = {
            'description': data.get('description', ''),
            'max_players': min(int(data.get('max_players', 12)), 20),
            'min_players': max(int(data.get('min_players', 4)), 4),
            'password': data.get('password'),
            'allow_voice_chat': data.get('allow_voice_chat', True),
            'allow_text_chat': data.get('allow_text_chat', True),
            'auto_start': data.get('auto_start', False)
        }
        
        # إنشاء الغرفة عبر RoomManager
        room_manager = current_app.room_manager
        success, message, room = room_manager.create_room(
            current_user.id,
            data['name'],
            **room_settings
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'room': room.to_dict(include_players=True)
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء الغرفة: {str(e)}'
        }), 500

@room_bp.route('/join', methods=['POST'])
@login_required
def join_room():
    """الانضمام إلى غرفة"""
    try:
        data = request.get_json()
        
        if not data.get('room_code'):
            return jsonify({
                'success': False,
                'message': 'رمز الغرفة مطلوب'
            }), 400
        
        room_code = data['room_code'].upper()
        password = data.get('password')
        
        # الانضمام عبر RoomManager
        room_manager = current_app.room_manager
        success, message = room_manager.join_room(current_user.id, room_code, password)
        
        if success:
            room = room_manager.get_room(room_code)
            return jsonify({
                'success': True,
                'message': message,
                'room': room.to_dict(include_players=True) if room else None
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في الانضمام: {str(e)}'
        }), 500

@room_bp.route('/leave', methods=['POST'])
@login_required
def leave_room():
    """مغادرة الغرفة"""
    try:
        room_manager = current_app.room_manager
        success, message = room_manager.leave_room(current_user.id)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في المغادرة: {str(e)}'
        }), 500

@room_bp.route('/my-room', methods=['GET'])
@login_required
def get_my_room():
    """الحصول على الغرفة الحالية للمستخدم"""
    try:
        room_manager = current_app.room_manager
        room = room_manager.get_user_room(current_user.id)
        
        if room:
            return jsonify({
                'success': True,
                'room': room.to_dict(include_players=True)
            })
        else:
            return jsonify({
                'success': True,
                'room': None
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@room_bp.route('/list', methods=['GET'])
def list_rooms():
    """الحصول على قائمة الغرف"""
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
        room_type = request.args.get('type', 'public')  # public, all, my
        
        room_manager = current_app.room_manager
        
        if room_type == 'public':
            # الغرف العامة فقط
            rooms = room_manager.get_public_rooms(limit)
        elif room_type == 'all' and current_user.is_authenticated:
            # جميع الغرف (للمستخدمين المُسجّلين)
            rooms = Room.query.filter(
                Room.status.in_([RoomStatus.WAITING, RoomStatus.ACTIVE])
            ).order_by(Room.created_at.desc()).limit(limit).all()
        elif room_type == 'my' and current_user.is_authenticated:
            # غرف المستخدم فقط
            rooms = Room.query.join(Player).filter(
                Player.user_id == current_user.id,
                Room.status.in_([RoomStatus.WAITING, RoomStatus.ACTIVE])
            ).order_by(Room.created_at.desc()).limit(limit).all()
        else:
            # افتراضي: الغرف العامة
            rooms = room_manager.get_public_rooms(limit)
        
        return jsonify({
            'success': True,
            'rooms': [room.to_dict() for room in rooms],
            'count': len(rooms)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في الحصول على الغرف: {str(e)}'
        }), 500

@room_bp.route('/public', methods=['GET'])
def get_public_rooms():
    """الحصول على الغرف العامة"""
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
        
        room_manager = current_app.room_manager
        rooms = room_manager.get_public_rooms(limit)
        
        return jsonify({
            'success': True,
            'rooms': [room.to_dict() for room in rooms],
            'count': len(rooms)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@room_bp.route('/<room_code>', methods=['GET'])
@login_required
def get_room_info(room_code):
    """الحصول على معلومات غرفة"""
    try:
        room_manager = current_app.room_manager
        room = room_manager.get_room(room_code.upper())
        
        if not room:
            return jsonify({
                'success': False,
                'message': 'الغرفة غير موجودة'
            }), 404
        
        return jsonify({
            'success': True,
            'room': room.to_dict(include_players=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@room_bp.route('/<room_code>/ready', methods=['POST'])
@login_required
def set_ready_status(room_code):
    """تعيين حالة الاستعداد"""
    try:
        data = request.get_json() or {}
        ready = data.get('ready', True)
        
        room_manager = current_app.room_manager
        success, message = room_manager.set_player_ready(current_user.id, ready)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@room_bp.route('/<room_code>/settings', methods=['PUT'])
@login_required
def update_room_settings(room_code):
    """تحديث إعدادات الغرفة"""
    try:
        data = request.get_json()
        
        room_manager = current_app.room_manager
        success, message = room_manager.update_room_settings(
            room_code.upper(),
            current_user.id,
            **data
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500