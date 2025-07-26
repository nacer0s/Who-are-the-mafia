#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أحداث الدردشة عبر WebSocket
Chat WebSocket Events
"""

from flask import current_app
from flask_socketio import emit
from flask_login import current_user
from models import db
from models.message import Message, MessageType
from models.player import Player

def register_chat_events(socketio):
    """تسجيل أحداث الدردشة"""
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """إرسال رسالة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            content = data.get('content', '').strip()
            message_type = data.get('message_type', 'text')
            
            if not content:
                emit('error', {'message': 'محتوى الرسالة مطلوب'})
                return
            
            # الحصول على الغرفة
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            # التحقق من إمكانية الإرسال
            if not room.allow_text_chat:
                emit('error', {'message': 'الدردشة النصية معطلة في هذه الغرفة'})
                return
            
            # التحقق من قيود اللعبة
            game_manager = current_app.game_manager
            session = game_manager.get_game_session(room.id)
            
            # البحث عن اللاعب
            player = Player.query.filter_by(
                user_id=current_user.id,
                room_id=room.id
            ).first()
            
            # إنشاء الرسالة
            msg_type = MessageType.TEXT
            if message_type == 'voice':
                msg_type = MessageType.VOICE
            elif message_type == 'private':
                msg_type = MessageType.PRIVATE
            
            message = Message(
                room_id=room.id,
                user_id=current_user.id,
                content=content,
                message_type=msg_type
            )
            
            # إضافة معلومات اللعبة إن وجدت
            if session:
                message.game_round = session.current_round
                message.game_phase = session.phase_manager.current_phase.value
            
            db.session.add(message)
            db.session.commit()
            
            # تحليل الرسالة بالذكاء الاصطناعي
            if hasattr(current_app, 'ai_analyzer'):
                try:
                    analysis = current_app.ai_analyzer.analyze_message(
                        message.id,
                        content,
                        current_user.id,
                        room.id,
                        session.current_round if session else None,
                        session.phase_manager.current_phase.value if session else None
                    )
                    
                    if analysis.get('is_suspicious', False):
                        message.flag_as_suspicious(
                            analysis.get('reason', 'محتوى مشبوه'),
                            analysis.get('suspicion_score', 0.5)
                        )
                        
                        # إخفاء الرسالة إذا كانت مخالفة شديدة
                        if analysis.get('suspicion_score', 0) > 0.8:
                            message.hide_message(analysis.get('reason', 'مخالفة شديدة'))
                            
                            # إشعار المرسل
                            emit('message_hidden', {
                                'message_id': message.id,
                                'reason': analysis.get('reason', 'مخالفة شديدة')
                            })
                            
                except Exception as e:
                    print(f"خطأ في تحليل الرسالة: {e}")
            
            # تحديث إحصائيات الدردشة
            if current_user.statistics:
                current_user.statistics.update_chat_stats(
                    len(content),
                    message.suspicion_score,
                    message.is_flagged
                )
            
            # إرسال الرسالة للمستقبلين المناسبين
            message_data = message.to_dict(current_user.id)
            
            if msg_type == MessageType.PRIVATE:
                # رسالة خاصة
                target_user_id = data.get('target_user_id')
                if target_user_id:
                    emit('new_message', {'message': message_data}, room=f"user_{target_user_id}")
                    emit('new_message', {'message': message_data})  # للمرسل أيضاً
            else:
                # رسالة عامة
                target_room = room.room_code
                
                # التحقق من القناة الخاصة
                if session and player:
                    current_phase = session.phase_manager.current_phase.value
                    
                    # في الليل، المافيا يمكنهم التحدث فيما بينهم فقط
                    if current_phase == 'night' and player.role.value == 'mafia':
                        target_room = f"{room.room_code}_mafia"
                    # الأموات يتحدثون في قناة خاصة
                    elif not player.is_alive:
                        target_room = f"{room.room_code}_dead"
                
                emit('new_message', {'message': message_data}, room=target_room)
            
            # إشعار بنجاح الإرسال
            emit('message_sent', {
                'message_id': message.id,
                'status': message.status.value
            })
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': f'خطأ في إرسال الرسالة: {str(e)}'})
    
    @socketio.on('get_messages')
    def handle_get_messages(data):
        """الحصول على الرسائل"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            # معايير الاستعلام
            limit = min(int(data.get('limit', 50)), 100)
            offset = int(data.get('offset', 0))
            
            # استعلام الرسائل
            messages_query = Message.query.filter_by(
                room_id=room.id
            ).order_by(Message.sent_at.desc())
            
            total_count = messages_query.count()
            messages = messages_query.offset(offset).limit(limit).all()
            
            # تنسيق الرسائل
            messages_data = []
            for message in reversed(messages):  # عكس الترتيب للعرض الصحيح
                if message.can_be_seen_by(current_user.id):
                    messages_data.append(message.to_dict(current_user.id))
            
            emit('messages_loaded', {
                'messages': messages_data,
                'total_count': total_count,
                'loaded_count': len(messages_data),
                'offset': offset
            })
            
        except Exception as e:
            emit('error', {'message': f'خطأ في تحميل الرسائل: {str(e)}'})
    
    @socketio.on('edit_message')
    def handle_edit_message(data):
        """تعديل رسالة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            message_id = data.get('message_id')
            new_content = data.get('content', '').strip()
            
            if not message_id or not new_content:
                emit('error', {'message': 'معرف الرسالة والمحتوى الجديد مطلوبان'})
                return
            
            # البحث عن الرسالة
            message = Message.query.get(message_id)
            
            if not message:
                emit('error', {'message': 'الرسالة غير موجودة'})
                return
            
            # التحقق من الصلاحية
            if message.user_id != current_user.id:
                emit('error', {'message': 'لا يمكنك تعديل رسالة شخص آخر'})
                return
            
            # التحقق من الوقت (يمكن التعديل خلال 5 دقائق فقط)
            from datetime import datetime, timedelta
            if datetime.utcnow() - message.sent_at > timedelta(minutes=5):
                emit('error', {'message': 'لا يمكن تعديل الرسالة بعد 5 دقائق من الإرسال'})
                return
            
            # تعديل الرسالة
            old_content = message.content
            message.edit_content(new_content)
            
            # تحليل المحتوى الجديد
            if hasattr(current_app, 'ai_analyzer'):
                try:
                    room_manager = current_app.room_manager
                    room = room_manager.get_room_by_id(message.room_id)
                    
                    analysis = current_app.ai_analyzer.analyze_message(
                        message.id,
                        new_content,
                        current_user.id,
                        message.room_id,
                        message.game_round,
                        message.game_phase
                    )
                    
                    if analysis.get('is_suspicious', False):
                        message.flag_as_suspicious(
                            analysis.get('reason', 'محتوى مشبوه بعد التعديل'),
                            analysis.get('suspicion_score', 0.5)
                        )
                        
                except Exception as e:
                    print(f"خطأ في تحليل الرسالة المعدلة: {e}")
            
            # إشعار جميع المستخدمين بالتعديل
            from models.room import Room
            room = Room.query.get(message.room_id)
            
            if room:
                emit('message_edited', {
                    'message': message.to_dict(current_user.id),
                    'old_content': old_content
                }, room=room.room_code)
            
            emit('message_edit_success', {
                'message_id': message_id,
                'new_content': new_content
            })
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': f'خطأ في تعديل الرسالة: {str(e)}'})
    
    @socketio.on('delete_message')
    def handle_delete_message(data):
        """حذف رسالة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            message_id = data.get('message_id')
            
            if not message_id:
                emit('error', {'message': 'معرف الرسالة مطلوب'})
                return
            
            # البحث عن الرسالة
            message = Message.query.get(message_id)
            
            if not message:
                emit('error', {'message': 'الرسالة غير موجودة'})
                return
            
            # التحقق من الصلاحية
            from models.room import Room
            room = Room.query.get(message.room_id)
            
            can_delete = (
                message.user_id == current_user.id or  # المرسل
                (room and room.creator_id == current_user.id)  # منشئ الغرفة
            )
            
            if not can_delete:
                emit('error', {'message': 'ليس لديك صلاحية حذف هذه الرسالة'})
                return
            
            # حذف الرسالة
            message.delete_message()
            
            # إشعار جميع المستخدمين بالحذف
            if room:
                emit('message_deleted', {
                    'message_id': message_id,
                    'deleted_by': current_user.display_name
                }, room=room.room_code)
            
            emit('message_delete_success', {
                'message_id': message_id
            })
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': f'خطأ في حذف الرسالة: {str(e)}'})
    
    @socketio.on('report_message')
    def handle_report_message(data):
        """الإبلاغ عن رسالة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            message_id = data.get('message_id')
            reason = data.get('reason', 'محتوى مخالف')
            
            if not message_id:
                emit('error', {'message': 'معرف الرسالة مطلوب'})
                return
            
            # البحث عن الرسالة
            message = Message.query.get(message_id)
            
            if not message:
                emit('error', {'message': 'الرسالة غير موجودة'})
                return
            
            # تسجيل الإبلاغ
            message.flag_as_suspicious(f"تم الإبلاغ من {current_user.display_name}: {reason}", 0.7)
            
            # إشعار المشرفين
            from models.room import Room
            room = Room.query.get(message.room_id)
            
            if room:
                emit('message_reported', {
                    'message_id': message_id,
                    'reported_by': current_user.display_name,
                    'reason': reason,
                    'message_content': message.content[:100] + "..." if len(message.content) > 100 else message.content
                }, room=f"admin_{room.room_code}")
            
            emit('report_sent', {
                'message_id': message_id,
                'message': 'تم إرسال التقرير للمشرفين'
            })
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': f'خطأ في الإبلاغ: {str(e)}'})
    
    @socketio.on('typing_start')
    def handle_typing_start():
        """بداية الكتابة"""
        if not current_user.is_authenticated:
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if room:
                emit('user_typing', {
                    'user_id': current_user.id,
                    'display_name': current_user.display_name,
                    'typing': True
                }, room=room.room_code, include_self=False)
                
        except Exception as e:
            print(f"خطأ في typing_start: {e}")
    
    @socketio.on('typing_stop')
    def handle_typing_stop():
        """إيقاف الكتابة"""
        if not current_user.is_authenticated:
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if room:
                emit('user_typing', {
                    'user_id': current_user.id,
                    'display_name': current_user.display_name,
                    'typing': False
                }, room=room.room_code, include_self=False)
                
        except Exception as e:
            print(f"خطأ في typing_stop: {e}")
    
    return socketio