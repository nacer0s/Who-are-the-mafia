#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الرسائل
Message Model
"""

from datetime import datetime
from enum import Enum
import json
from . import db

class MessageType(Enum):
    """أنواع الرسائل"""
    TEXT = "text"             # رسالة نصية عادية
    VOICE = "voice"           # رسالة صوتية
    SYSTEM = "system"         # رسالة النظام
    GAME_ACTION = "game_action"  # رسالة عمل في اللعبة
    PRIVATE = "private"       # رسالة خاصة
    ANNOUNCEMENT = "announcement"  # إعلان

class MessageStatus(Enum):
    """حالات الرسالة"""
    SENT = "sent"             # تم الإرسال
    DELIVERED = "delivered"   # تم التسليم
    READ = "read"             # تم القراءة
    HIDDEN = "hidden"         # مخفية (للرسائل المخالفة)
    DELETED = "deleted"       # محذوفة

class Message(db.Model):
    """نموذج الرسائل في الدردشة"""
    
    __tablename__ = 'messages'
    
    # المعرف الأساسي
    id = db.Column(db.Integer, primary_key=True)
    
    # ربط مع المستخدم والغرفة
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null للرسائل النظام
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    
    # معلومات الرسالة
    message_type = db.Column(db.Enum(MessageType), default=MessageType.TEXT, nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # للرسائل الصوتية
    voice_file_path = db.Column(db.String(255), nullable=True)
    voice_duration = db.Column(db.Float, nullable=True)  # بالثواني
    transcription = db.Column(db.Text, nullable=True)    # تحويل الصوت إلى نص
    
    # حالة الرسالة
    status = db.Column(db.Enum(MessageStatus), default=MessageStatus.SENT, nullable=False)
    
    # معلومات الإرسال
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    edited_at = db.Column(db.DateTime, nullable=True)
    
    # معلومات اللعبة
    game_round = db.Column(db.Integer, nullable=True)
    game_phase = db.Column(db.String(20), nullable=True)
    
    # تحليل الذكاء الاصطناعي
    ai_analysis = db.Column(db.Text, nullable=True)  # تحليل المحتوى كـ JSON
    suspicion_score = db.Column(db.Float, default=0.0, nullable=False)  # مؤشر الشك (0-1)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)  # مبلغ عنها
    
    # معلومات إضافية
    message_metadata = db.Column(db.Text, nullable=True)  # بيانات إضافية كـ JSON
    
    def __init__(self, room_id, content, user_id=None, message_type=MessageType.TEXT, **kwargs):
        """إنشاء رسالة جديدة"""
        self.room_id = room_id
        self.content = content
        self.user_id = user_id
        self.message_type = message_type
        
        # تطبيق الإعدادات الاختيارية
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_ai_analysis(self, analysis):
        """تعيين تحليل الذكاء الاصطناعي"""
        self.ai_analysis = json.dumps(analysis, ensure_ascii=False)
        db.session.commit()
    
    def get_ai_analysis(self):
        """الحصول على تحليل الذكاء الاصطناعي"""
        if self.ai_analysis:
            return json.loads(self.ai_analysis)
        return {}
    
    def set_metadata(self, metadata):
        """تعيين البيانات الإضافية"""
        self.message_metadata = json.dumps(metadata, ensure_ascii=False)
    
    def get_metadata(self):
        """الحصول على البيانات الإضافية"""
        if self.message_metadata:
            return json.loads(self.message_metadata)
        return {}
    
    def flag_as_suspicious(self, reason, score=0.8):
        """تمييز الرسالة كمشبوهة"""
        self.is_flagged = True
        self.suspicion_score = max(self.suspicion_score, score)
        
        # إضافة السبب للتحليل
        analysis = self.get_ai_analysis()
        if 'flags' not in analysis:
            analysis['flags'] = []
        
        analysis['flags'].append({
            'reason': reason,
            'score': score,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        self.set_ai_analysis(analysis)
        db.session.commit()
    
    def hide_message(self, reason="مخالفة للقوانين"):
        """إخفاء الرسالة"""
        self.status = MessageStatus.HIDDEN
        
        # إضافة السبب للبيانات الإضافية
        metadata = self.get_metadata()
        metadata['hidden_reason'] = reason
        metadata['hidden_at'] = datetime.utcnow().isoformat()
        self.set_metadata(metadata)
        
        db.session.commit()
    
    def edit_content(self, new_content):
        """تعديل محتوى الرسالة"""
        self.content = new_content
        self.edited_at = datetime.utcnow()
        db.session.commit()
    
    def delete_message(self):
        """حذف الرسالة"""
        self.status = MessageStatus.DELETED
        self.content = "[تم حذف هذه الرسالة]"
        db.session.commit()
    
    def is_from_mafia(self):
        """التحقق من كون المرسل من المافيا"""
        if not self.user_id:
            return False
        
        from .player import Player, PlayerRole
        player = Player.query.filter_by(
            user_id=self.user_id,
            room_id=self.room_id
        ).first()
        
        return player and player.role == PlayerRole.MAFIA
    
    def can_be_seen_by(self, user_id):
        """التحقق من إمكانية رؤية الرسالة"""
        # الرسائل المحذوفة لا يمكن رؤيتها
        if self.status == MessageStatus.DELETED:
            return False
        
        # رسائل النظام يمكن رؤيتها من الجميع
        if self.message_type == MessageType.SYSTEM:
            return True
        
        # الرسائل المخفية يمكن رؤيتها من المرسل فقط
        if self.status == MessageStatus.HIDDEN:
            return self.user_id == user_id
        
        # الرسائل الخاصة
        if self.message_type == MessageType.PRIVATE:
            metadata = self.get_metadata()
            target_user_id = metadata.get('target_user_id')
            return user_id in [self.user_id, target_user_id]
        
        # رسائل المافيا في الليل
        if self.message_type == MessageType.GAME_ACTION:
            from .player import Player, PlayerRole
            player = Player.query.filter_by(
                user_id=user_id,
                room_id=self.room_id
            ).first()
            
            # إذا كانت رسالة مافيا، فقط المافيا يمكنهم رؤيتها
            if self.is_from_mafia():
                return player and player.role == PlayerRole.MAFIA
        
        return True
    
    def get_display_content(self, viewer_user_id=None):
        """الحصول على المحتوى المعروض"""
        if not self.can_be_seen_by(viewer_user_id):
            return "[رسالة مخفية]"
        
        if self.status == MessageStatus.HIDDEN:
            return "[تم إخفاء هذه الرسالة]"
        
        if self.status == MessageStatus.DELETED:
            return "[تم حذف هذه الرسالة]"
        
        return self.content
    
    def to_dict(self, viewer_user_id=None, include_analysis=False):
        """تحويل الرسالة إلى قاموس"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'sender_name': self.user.display_name if self.user else "النظام",
            'sender_avatar': self.user.avatar_url if self.user else None,
            'room_id': self.room_id,
            'message_type': self.message_type.value,
            'content': self.get_display_content(viewer_user_id),
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat(),
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'game_round': self.game_round,
            'game_phase': self.game_phase,
            'is_flagged': self.is_flagged,
            'can_see': self.can_be_seen_by(viewer_user_id)
        }
        
        # معلومات الرسائل الصوتية
        if self.message_type == MessageType.VOICE:
            data.update({
                'voice_file_path': self.voice_file_path,
                'voice_duration': self.voice_duration,
                'transcription': self.transcription
            })
        
        # تحليل الذكاء الاصطناعي (للمشرفين فقط)
        if include_analysis:
            data.update({
                'ai_analysis': self.get_ai_analysis(),
                'suspicion_score': self.suspicion_score,
                'metadata': self.get_metadata()
            })
        
        return data
    
    @staticmethod
    def create_system_message(room_id, content, **kwargs):
        """إنشاء رسالة نظام"""
        message = Message(
            room_id=room_id,
            content=content,
            user_id=None,
            message_type=MessageType.SYSTEM,
            **kwargs
        )
        db.session.add(message)
        db.session.commit()
        return message
    
    @staticmethod
    def create_game_action_message(room_id, content, user_id=None, **kwargs):
        """إنشاء رسالة عمل في اللعبة"""
        message = Message(
            room_id=room_id,
            content=content,
            user_id=user_id,
            message_type=MessageType.GAME_ACTION,
            **kwargs
        )
        db.session.add(message)
        db.session.commit()
        return message
    
    def __repr__(self):
        sender = self.user.username if self.user else "System"
        return f'<Message {self.id}: {sender} in Room {self.room_id}>'
    
    def __str__(self):
        return f"{self.content[:50]}..." if len(self.content) > 50 else self.content