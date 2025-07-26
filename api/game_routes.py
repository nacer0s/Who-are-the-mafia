#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات اللعبة
Game Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

game_bp = Blueprint('game', __name__)

@game_bp.route('/start', methods=['POST'])
@login_required
def start_game():
    """بدء لعبة جديدة"""
    try:
        data = request.get_json() or {}
        
        # الحصول على الغرفة الحالية
        room_manager = current_app.room_manager
        room = room_manager.get_user_room(current_user.id)
        
        if not room:
            return jsonify({
                'success': False,
                'message': 'لست في أي غرفة'
            }), 400
        
        # التحقق من الصلاحية
        if room.creator_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'فقط منشئ الغرفة يمكنه بدء اللعبة'
            }), 403
        
        # بدء اللعبة
        game_manager = current_app.game_manager
        success, message, game = game_manager.start_game(room.id)
        
        return jsonify({
            'success': success,
            'message': message,
            'game': game.to_dict() if game else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في بدء اللعبة: {str(e)}'
        }), 500

@game_bp.route('/status', methods=['GET'])
@login_required
def get_game_status():
    """الحصول على حالة اللعبة"""
    try:
        room_manager = current_app.room_manager
        room = room_manager.get_user_room(current_user.id)
        
        if not room:
            return jsonify({
                'success': False,
                'message': 'لست في أي غرفة'
            }), 400
        
        game_manager = current_app.game_manager
        status = game_manager.get_game_status(room.id)
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@game_bp.route('/action', methods=['POST'])
@login_required
def submit_action():
    """تقديم إجراء في اللعبة"""
    try:
        data = request.get_json()
        
        if not data.get('action_type'):
            return jsonify({
                'success': False,
                'message': 'نوع الإجراء مطلوب'
            }), 400
        
        room_manager = current_app.room_manager
        room = room_manager.get_user_room(current_user.id)
        
        if not room:
            return jsonify({
                'success': False,
                'message': 'لست في أي غرفة'
            }), 400
        
        game_manager = current_app.game_manager
        success, message = game_manager.submit_action(
            room.id,
            current_user.id,
            data['action_type'],
            data.get('target_id'),
            **data.get('details', {})
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

@game_bp.route('/vote', methods=['POST'])
@login_required
def cast_vote():
    """تسجيل صوت"""
    try:
        data = request.get_json() or {}
        
        room_manager = current_app.room_manager
        room = room_manager.get_user_room(current_user.id)
        
        if not room:
            return jsonify({
                'success': False,
                'message': 'لست في أي غرفة'
            }), 400
        
        game_manager = current_app.game_manager
        success, message = game_manager.cast_vote(
            room.id,
            current_user.id,
            data.get('target_id')
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

@game_bp.route('/player-info', methods=['GET'])
@login_required
def get_player_info():
    """الحصول على معلومات اللاعب"""
    try:
        room_manager = current_app.room_manager
        room = room_manager.get_user_room(current_user.id)
        
        if not room:
            return jsonify({
                'success': False,
                'message': 'لست في أي غرفة'
            }), 400
        
        # العثور على اللاعب
        from models.player import Player
        player = Player.query.filter_by(
            user_id=current_user.id,
            room_id=room.id
        ).first()
        
        if not player:
            return jsonify({
                'success': False,
                'message': 'لست لاعباً في هذه الغرفة'
            }), 400
        
        game_manager = current_app.game_manager
        info = game_manager.get_player_info(room.id, player.id)
        
        return jsonify({
            'success': True,
            'player': info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500