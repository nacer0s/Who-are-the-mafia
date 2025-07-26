#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أحداث الصوت عبر WebSocket
Voice WebSocket Events
"""

import os
import base64
from datetime import datetime
from flask import current_app
from flask_socketio import emit
from flask_login import current_user
from models import db
from models.message import Message, MessageType

def register_voice_events(socketio):
    """تسجيل أحداث الصوت"""
    
    @socketio.on('voice_message')
    def handle_voice_message(data):
        """إرسال رسالة صوتية"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            # بيانات الصوت
            audio_data = data.get('audio_data')  # base64 encoded
            duration = data.get('duration', 0)
            
            if not audio_data:
                emit('error', {'message': 'بيانات الصوت مطلوبة'})
                return
            
            # الحصول على الغرفة
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            # التحقق من إمكانية الإرسال
            if not room.allow_voice_chat:
                emit('error', {'message': 'الدردشة الصوتية معطلة في هذه الغرفة'})
                return
            
            # حفظ الملف الصوتي
            voice_file_path = save_voice_file(audio_data, current_user.id)
            
            if not voice_file_path:
                emit('error', {'message': 'فشل في حفظ الملف الصوتي'})
                return
            
            # تحويل الصوت إلى نص
            transcription = ""
            if hasattr(current_app, 'speech_to_text'):
                try:
                    transcription = current_app.speech_to_text.transcribe(voice_file_path)
                except Exception as e:
                    print(f"خطأ في تحويل الصوت إلى نص: {e}")
            
            # إنشاء الرسالة الصوتية
            game_manager = current_app.game_manager
            session = game_manager.get_game_session(room.id)
            
            message = Message(
                room_id=room.id,
                user_id=current_user.id,
                content=transcription or "[رسالة صوتية]",
                message_type=MessageType.VOICE,
                voice_file_path=voice_file_path,
                voice_duration=duration,
                transcription=transcription
            )
            
            # إضافة معلومات اللعبة
            if session:
                message.game_round = session.current_round
                message.game_phase = session.phase_manager.current_phase.value
            
            db.session.add(message)
            db.session.commit()
            
            # تحليل الرسالة الصوتية بالذكاء الاصطناعي
            if hasattr(current_app, 'ai_analyzer') and transcription:
                try:
                    analysis = current_app.ai_analyzer.analyze_voice_message(
                        message.id,
                        transcription,
                        voice_file_path,
                        current_user.id,
                        room.id,
                        session.current_round if session else None,
                        session.phase_manager.current_phase.value if session else None
                    )
                    
                    if analysis.get('is_suspicious', False):
                        message.flag_as_suspicious(
                            analysis.get('reason', 'محتوى صوتي مشبوه'),
                            analysis.get('suspicion_score', 0.5)
                        )
                        
                        # إخفاء الرسالة إذا كانت مخالفة شديدة
                        if analysis.get('suspicion_score', 0) > 0.8:
                            message.hide_message(analysis.get('reason', 'مخالفة صوتية شديدة'))
                            
                            emit('voice_message_hidden', {
                                'message_id': message.id,
                                'reason': analysis.get('reason', 'مخالفة صوتية شديدة')
                            })
                            
                except Exception as e:
                    print(f"خطأ في تحليل الرسالة الصوتية: {e}")
            
            # تحديث إحصائيات الدردشة
            if current_user.statistics:
                current_user.statistics.update_chat_stats(
                    len(transcription) if transcription else 10,  # تقدير طول الرسالة الصوتية
                    message.suspicion_score,
                    message.is_flagged
                )
            
            # إرسال الرسالة الصوتية
            message_data = message.to_dict(current_user.id)
            emit('new_voice_message', {'message': message_data}, room=room.room_code)
            
            # إشعار بنجاح الإرسال
            emit('voice_message_sent', {
                'message_id': message.id,
                'transcription': transcription,
                'duration': duration
            })
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': f'خطأ في إرسال الرسالة الصوتية: {str(e)}'})
    
    @socketio.on('voice_chat_join')
    def handle_voice_chat_join():
        """الانضمام للدردشة الصوتية المباشرة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            if not room.allow_voice_chat:
                emit('error', {'message': 'الدردشة الصوتية معطلة في هذه الغرفة'})
                return
            
            # الانضمام لقناة الصوت
            voice_channel = f"{room.room_code}_voice"
            
            emit('voice_chat_joined', {
                'channel': voice_channel,
                'user_id': current_user.id,
                'display_name': current_user.display_name
            })
            
            # إشعار باقي اللاعبين
            emit('user_joined_voice', {
                'user_id': current_user.id,
                'display_name': current_user.display_name
            }, room=room.room_code, include_self=False)
            
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('voice_chat_leave')
    def handle_voice_chat_leave():
        """مغادرة الدردشة الصوتية المباشرة"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            # مغادرة قناة الصوت
            emit('voice_chat_left', {
                'user_id': current_user.id,
                'display_name': current_user.display_name
            })
            
            # إشعار باقي اللاعبين
            emit('user_left_voice', {
                'user_id': current_user.id,
                'display_name': current_user.display_name
            }, room=room.room_code, include_self=False)
            
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('voice_mute_toggle')
    def handle_voice_mute_toggle(data):
        """تفعيل/إلغاء كتم الصوت"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return
        
        try:
            is_muted = data.get('muted', False)
            
            room_manager = current_app.room_manager
            room = room_manager.get_user_room(current_user.id)
            
            if not room:
                emit('error', {'message': 'لست في أي غرفة'})
                return
            
            # إشعار باقي اللاعبين بحالة الكتم
            emit('user_voice_mute_changed', {
                'user_id': current_user.id,
                'display_name': current_user.display_name,
                'muted': is_muted
            }, room=room.room_code, include_self=False)
            
            emit('voice_mute_updated', {
                'muted': is_muted
            })
            
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})
    
    @socketio.on('request_transcription')
    def handle_request_transcription(data):
        """طلب تحويل ملف صوتي إلى نص"""
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
            
            if not message or message.message_type != MessageType.VOICE:
                emit('error', {'message': 'رسالة صوتية غير موجودة'})
                return
            
            # التحقق من الصلاحية
            if not message.can_be_seen_by(current_user.id):
                emit('error', {'message': 'ليس لديك صلاحية لرؤية هذه الرسالة'})
                return
            
            # إرسال النص المحول إن وجد
            if message.transcription:
                emit('transcription_result', {
                    'message_id': message_id,
                    'transcription': message.transcription
                })
            else:
                # محاولة تحويل الصوت إلى نص
                if hasattr(current_app, 'speech_to_text') and message.voice_file_path:
                    try:
                        transcription = current_app.speech_to_text.transcribe(message.voice_file_path)
                        
                        # حفظ النص المحول
                        message.transcription = transcription
                        db.session.commit()
                        
                        emit('transcription_result', {
                            'message_id': message_id,
                            'transcription': transcription
                        })
                        
                    except Exception as e:
                        emit('error', {'message': f'فشل في تحويل الصوت إلى نص: {str(e)}'})
                else:
                    emit('error', {'message': 'خدمة تحويل الصوت إلى نص غير متاحة'})
            
        except Exception as e:
            emit('error', {'message': f'خطأ: {str(e)}'})

def save_voice_file(audio_data_base64, user_id):
    """حفظ الملف الصوتي"""
    try:
        # إنشاء مجلد الملفات الصوتية إن لم يكن موجوداً
        voice_dir = os.path.join(current_app.root_path, 'static', 'voice_messages')
        os.makedirs(voice_dir, exist_ok=True)
        
        # فك تشفير البيانات
        audio_data = base64.b64decode(audio_data_base64)
        
        # إنشاء اسم ملف فريد
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"voice_{user_id}_{timestamp}.wav"
        file_path = os.path.join(voice_dir, filename)
        
        # حفظ الملف
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        
        # إرجاع المسار النسبي
        return f"static/voice_messages/{filename}"
        
    except Exception as e:
        print(f"خطأ في حفظ الملف الصوتي: {e}")
        return None

def cleanup_old_voice_files():
    """تنظيف الملفات الصوتية القديمة"""
    try:
        voice_dir = os.path.join(current_app.root_path, 'static', 'voice_messages')
        
        if not os.path.exists(voice_dir):
            return
        
        # حذف الملفات الأقدم من أسبوع
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for filename in os.listdir(voice_dir):
            file_path = os.path.join(voice_dir, filename)
            
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        print(f"تم حذف الملف الصوتي القديم: {filename}")
                    except Exception as e:
                        print(f"خطأ في حذف الملف {filename}: {e}")
        
    except Exception as e:
        print(f"خطأ في تنظيف الملفات الصوتية: {e}")

# إضافة مهمة التنظيف الدورية
def setup_voice_cleanup():
    """إعداد تنظيف الملفات الصوتية الدوري"""
    import threading
    import time
    
    def cleanup_worker():
        while True:
            time.sleep(86400)  # كل 24 ساعة
            cleanup_old_voice_files()
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

# تصدير الوظائف
__all__ = ['register_voice_events', 'save_voice_file', 'cleanup_old_voice_files', 'setup_voice_cleanup']