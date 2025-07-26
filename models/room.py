#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الغرفة
Room Model
"""

from datetime import datetime
from enum import Enum
import uuid
from . import db

class RoomStatus(Enum):
    """حالات الغرفة"""
    WAITING = "waiting"      # في انتظار اللاعبين
    STARTING = "starting"    # بدء اللعبة
    PLAYING = "playing"      # اللعبة جارية
    FINISHED = "finished"    # انتهت اللعبة
    CANCELLED = "cancelled"  # ألغيت اللعبة

class Room(db.Model):
    """نموذج الغرفة في اللعبة"""
    
    __tablename__ = 'rooms'
    
    # المعرف الأساسي
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    
    # معلومات الغرفة
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    password = db.Column(db.String(255), nullable=True)  # للغرف الخاصة
    
    # إعدادات اللعبة
    max_players = db.Column(db.Integer, default=12, nullable=False)
    min_players = db.Column(db.Integer, default=4, nullable=False)
    
    # حالة الغرفة
    status = db.Column(db.Enum(RoomStatus), default=RoomStatus.WAITING, nullable=False)
    current_players = db.Column(db.Integer, default=0, nullable=False)
    
    # معلومات المنشئ
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    creator = db.relationship('User', backref='created_rooms')
    
    # معلومات التوقيت
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    
    # إعدادات اللعبة المتقدمة
    allow_voice_chat = db.Column(db.Boolean, default=True, nullable=False)
    allow_text_chat = db.Column(db.Boolean, default=True, nullable=False)
    auto_start = db.Column(db.Boolean, default=False, nullable=False)
    
    # العلاقات
    games = db.relationship('Game', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    players = db.relationship('Player', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, creator_id, **kwargs):
        """إنشاء غرفة جديدة"""
        self.name = name
        self.creator_id = creator_id
        self.room_code = self.generate_room_code()
        
        # تطبيق الإعدادات الاختيارية
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @staticmethod
    def generate_room_code():
        """توليد رمز غرفة فريد"""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Room.query.filter_by(room_code=code).first():
                return code
    
    def add_player(self, user_id):
        """إضافة لاعب إلى الغرفة"""
        from .player import Player
        
        # التحقق من وجود اللاعب مسبقاً
        existing_player = Player.query.filter_by(
            user_id=user_id, 
            room_id=self.id
        ).first()
        
        if existing_player:
            return False, "اللاعب موجود بالفعل في الغرفة"
        
        # التحقق من عدد اللاعبين
        if self.current_players >= self.max_players:
            return False, "الغرفة ممتلئة"
        
        # التحقق من حالة الغرفة
        if self.status != RoomStatus.WAITING:
            return False, "لا يمكن الانضمام إلى الغرفة الآن"
        
        # إنشاء لاعب جديد
        player = Player(user_id=user_id, room_id=self.id)
        db.session.add(player)
        
        # تحديث عدد اللاعبين
        self.current_players += 1
        
        # التحقق من البدء التلقائي
        if self.auto_start and self.current_players >= self.min_players:
            self.start_game()
        
        db.session.commit()
        return True, "تم الانضمام بنجاح"
    
    def remove_player(self, user_id):
        """إزالة لاعب من الغرفة"""
        from .player import Player
        
        player = Player.query.filter_by(
            user_id=user_id, 
            room_id=self.id
        ).first()
        
        if not player:
            return False, "اللاعب غير موجود في الغرفة"
        
        # حذف اللاعب
        db.session.delete(player)
        self.current_players -= 1
        
        # إذا غادر المنشئ، نقل الملكية أو حذف الغرفة
        if user_id == self.creator_id:
            remaining_players = Player.query.filter_by(room_id=self.id).all()
            if remaining_players:
                # نقل الملكية لأول لاعب
                self.creator_id = remaining_players[0].user_id
            else:
                # حذف الغرفة إذا لم يبق أحد
                self.status = RoomStatus.CANCELLED
        
        db.session.commit()
        return True, "تم المغادرة بنجاح"
    
    def start_game(self):
        """بدء اللعبة"""
        if self.current_players < self.min_players:
            return False, f"يجب وجود {self.min_players} لاعبين على الأقل"
        
        if self.status != RoomStatus.WAITING:
            return False, "لا يمكن بدء اللعبة الآن"
        
        self.status = RoomStatus.STARTING
        self.started_at = datetime.utcnow()
        db.session.commit()
        
        return True, "تم بدء اللعبة"
    
    def finish_game(self):
        """إنهاء اللعبة"""
        self.status = RoomStatus.FINISHED
        self.finished_at = datetime.utcnow()
        db.session.commit()
    
    def cancel_game(self):
        """إلغاء اللعبة"""
        self.status = RoomStatus.CANCELLED
        self.finished_at = datetime.utcnow()
        db.session.commit()
    
    def get_active_players(self):
        """الحصول على اللاعبين النشطين"""
        from .player import Player
        return Player.query.filter_by(room_id=self.id, is_active=True).all()
    
    def is_full(self):
        """التحقق من امتلاء الغرفة"""
        return self.current_players >= self.max_players
    
    def can_join(self):
        """التحقق من إمكانية الانضمام"""
        return (self.status == RoomStatus.WAITING and 
                not self.is_full())
    
    def to_dict(self, include_players=False):
        """تحويل الغرفة إلى قاموس"""
        data = {
            'id': self.id,
            'room_code': self.room_code,
            'name': self.name,
            'description': self.description,
            'max_players': self.max_players,
            'min_players': self.min_players,
            'current_players': self.current_players,
            'status': self.status.value,
            'creator_id': self.creator_id,
            'creator_name': self.creator.display_name if self.creator else None,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'allow_voice_chat': self.allow_voice_chat,
            'allow_text_chat': self.allow_text_chat,
            'auto_start': self.auto_start,
            'is_full': self.is_full(),
            'can_join': self.can_join()
        }
        
        if include_players:
            data['players'] = [player.to_dict() for player in self.get_active_players()]
        
        return data
    
    def __repr__(self):
        return f'<Room {self.room_code}: {self.name}>'
    
    def __str__(self):
        return f"{self.name} ({self.room_code})"