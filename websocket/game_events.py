#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أحداث اللعبة عبر WebSocket
Game WebSocket Events
"""

from flask import current_app
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from models.message import Message
from models.player import Player

def register_game_events(socketio):
    """تسجيل أحداث اللعبة"""
    
    @socketio.on('start_game')
    def handle_start_game():
        """بدء اللعبة"""
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
                emit('error', {'message': 'فقط منشئ الغرفة يمكنه بدء اللعبة'})
                return
            
            # بدء اللعبة
            game_manager = current_app.game_manager
            success, message, game = game_manager.start_game(room.id)
            
            if success:
                # إشعار جميع اللاعبين ببدء اللعبة
                emit('game_started', {
                    'game': game.to_dict() if game else None,
                    'message': message
                }, room=room.room_code)
                
                # إرسال الأدوار للاعبين (رسائل خاصة)
                session = game_manager.get_game_session(room.id)
                if session:
                    for player in session.players:
                        role_info = session.role_manager.get_role_info(player.role)
                        
                        # إرسال الدور للاعب بشكل خاص
                        emit('role_assigned', {
                            'role': {
                                'name': role_info['name'],
                                'description': role_info['description'],
                                'abilities': role_info['abilities'],
                                'win_condition': role_info['win_condition'],
                                'team': role_info['team']
                            }
                        }, room=f"user_{player.user_id}")
                
            else:
                emit('error', {'message': message})
                
        except Exception as e:
            emit('error', {'message': f'خطأ في بدء اللعبة: {str(e)}'})
    
    @socketio.on('submit_action')
    def handle_submit_action(data):
        """تقديم إجراء في اللعبة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            action_type = data.get('action_type')
            target_id = data.get('target_id')
            details = data.get('details', {})
            
            if not action_type:
                emit('error', {'message': 'نوع الإجراء مطلوب'})
                return
            
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            game_manager = current_app.game_manager
            success, message = game_manager.submit_action(
                room.id,
                current_user.id,
                action_type,
                target_id,
                **details
            )
            
            if success:
                emit('action_submitted', {
                    'action_type': action_type,
                    'message': message
                })
                
                # إشعار المدير بالإجراء (للمراقبة)
                emit('player_action', {
                    'player_id': current_user.id,
                    'player_name': current_user.display_name,
                    'action_type': action_type,
                    'target_id': target_id
                }, room=f"admin_{room.room_code}")
                
            else:
                emit('error', {'message': message})
                
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('cast_vote')
    def handle_cast_vote(data):
        """تسجيل صوت"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            target_id = data.get('target_id')
            
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            game_manager = current_app.game_manager
            success, message = game_manager.cast_vote(
                room.id,
                current_user.id,
                target_id
            )
            
            if success:
                emit('vote_cast', {
                    'target_id': target_id,
                    'message': message
                })
                
                # إشعار جميع اللاعبين بالتصويت (بدون كشف الهوية)
                target_name = "لا أحد"
                if target_id:
                    target_player = Player.query.get(target_id)
                    if target_player and target_player.user:
                        target_name = target_player.user.display_name
                
                emit('vote_update', {
                    'voter_name': current_user.display_name,
                    'target_name': target_name,
                    'message': f"صوت {current_user.display_name} {'ضد ' + target_name if target_id else 'بالامتناع'}"
                }, room=room.room_code)
                
                # تحديث إحصائيات التصويت
                session = game_manager.get_game_session(room.id)
                if session:
                    voting_summary = session.voting_manager.get_vote_summary(room.id)
                    emit('voting_summary', voting_summary, room=room.room_code)
                
            else:
                emit('error', {'message': message})
                
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('get_game_status')
    def handle_get_game_status():
        """الحصول على حالة اللعبة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            game_manager = current_app.game_manager
            status = game_manager.get_game_status(room.id)
            
            emit('game_status', status)
            
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('get_player_info')
    def handle_get_player_info():
        """الحصول على معلومات اللاعب"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            # البحث عن اللاعب
            player = Player.query.filter_by(
                user_id=current_user.id,
                room_id=room.id
            ).first()
            
            if not player:
                emit('error', {'message': 'لست لاعباً في هذه الغرفة'})
                return
            
            game_manager = current_app.game_manager
            info = game_manager.get_player_info(room.id, player.id)
            
            emit('player_info', info)
            
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('join_private_channel')
    def handle_join_private_channel(data):
        """الانضمام للقناة الخاصة (مثل قناة المافيا)"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            channel_type = data.get('channel_type')  # 'mafia', 'dead', etc.
            
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            # البحث عن اللاعب
            player = Player.query.filter_by(
                user_id=current_user.id,
                room_id=room.id
            ).first()
            
            if not player:
                emit('error', {'message': 'لست لاعباً في هذه الغرفة'})
                return
            
            # التحقق من صلاحية الانضمام للقناة
            can_join = False
            
            if channel_type == 'mafia' and player.role.value == 'mafia':
                can_join = True
            elif channel_type == 'dead' and not player.is_alive:
                can_join = True
            
            if can_join:
                channel_name = f"{room.room_code}_{channel_type}"
                join_room(channel_name)
                
                emit('channel_joined', {
                    'channel': channel_type,
                    'message': f'انضممت إلى قناة {channel_type}'
                })
                
                # إشعار باقي أعضاء القناة
                emit('member_joined_channel', {
                    'user_id': current_user.id,
                    'display_name': current_user.display_name,
                    'channel': channel_type
                }, room=channel_name, include_self=False)
                
            else:
                emit('error', {'message': 'ليس لديك صلاحية للانضمام لهذه القناة'})
                
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('phase_change')
    def handle_phase_change(data):
        """تغيير مرحلة اللعبة (للمشرفين فقط)"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            # التحقق من الصلاحية (المنشئ أو مشرف)
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room or room.creator_id != current_user.id:
                emit('error', {'message': 'ليس لديك صلاحية تغيير مرحلة اللعبة'})
                return
            
            new_phase = data.get('phase')
            duration = data.get('duration')
            
            game_manager = current_app.game_manager
            session = game_manager.get_game_session(room.id)
            
            if not session:
                emit('error', {'message': 'لا توجد لعبة نشطة'})
                return
            
            # تغيير المرحلة
            from models.game import GamePhase
            try:
                phase_enum = GamePhase(new_phase)
                success = session.phase_manager.start_phase(phase_enum, duration)
                
                if success:
                    emit('phase_changed', {
                        'phase': new_phase,
                        'duration': duration,
                        'message': f'تم تغيير المرحلة إلى {new_phase}'
                    }, room=room.room_code)
                else:
                    emit('error', {'message': 'فشل في تغيير المرحلة'})
                    
            except ValueError:
                emit('error', {'message': 'مرحلة غير صحيحة'})
                
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    # أحداث النظام للعبة
    def broadcast_game_event(room_code, event_type, data):
        """بث حدث لعبة لجميع اللاعبين"""
        socketio.emit(event_type, data, room=room_code)
    
    def send_private_message(user_id, event_type, data):
        """إرسال رسالة خاصة للاعب"""
        socketio.emit(event_type, data, room=f"user_{user_id}")
    
    # الأحداث الإضافية ستكون متاحة داخل دوال الحدث فقط
    
    return socketio