#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج اللعبة
Game Model
"""

from datetime import datetime
from enum import Enum
import json
from . import db

class GamePhase(Enum):
    """مراحل اللعبة"""
    DAY = "day"           # النهار - مناقشة وتصويت
    NIGHT = "night"       # الليل - أعمال المافيا والأدوار الخاصة
    VOTING = "voting"     # مرحلة التصويت
    TRIAL = "trial"       # مرحلة المحاكمة
    FINISHED = "finished" # انتهت اللعبة

class GameStatus(Enum):
    """حالات اللعبة"""
    STARTING = "starting"   # بدء اللعبة وتوزيع الأدوار
    ACTIVE = "active"       # اللعبة نشطة
    PAUSED = "paused"       # اللعبة متوقفة مؤقتاً
    FINISHED = "finished"   # انتهت اللعبة
    CANCELLED = "cancelled" # ألغيت اللعبة

class WinCondition(Enum):
    """شروط الفوز"""
    MAFIA_WIN = "mafia_win"           # فوز المافيا
    CITIZENS_WIN = "citizens_win"     # فوز المواطنين
    DRAW = "draw"                     # تعادل
    CANCELLED = "cancelled"           # ألغيت اللعبة

class Game(db.Model):
    """نموذج اللعبة"""
    
    __tablename__ = 'games'
    
    # المعرف الأساسي
    id = db.Column(db.Integer, primary_key=True)
    
    # ربط مع الغرفة
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    
    # معلومات اللعبة
    game_number = db.Column(db.Integer, nullable=False)  # رقم اللعبة في الغرفة
    total_players = db.Column(db.Integer, nullable=False)
    
    # حالة اللعبة
    status = db.Column(db.Enum(GameStatus), default=GameStatus.STARTING, nullable=False)
    phase = db.Column(db.Enum(GamePhase), default=GamePhase.DAY, nullable=False)
    
    # معلومات الجولة الحالية
    current_round = db.Column(db.Integer, default=1, nullable=False)
    phase_start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    phase_end_time = db.Column(db.DateTime, nullable=True)
    
    # معلومات التوقيت
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    
    # نتيجة اللعبة
    winner = db.Column(db.Enum(WinCondition), nullable=True)
    winner_team = db.Column(db.String(50), nullable=True)  # "mafia" أو "citizens"
    
    # إعدادات اللعبة (JSON)
    settings = db.Column(db.Text, nullable=True)  # إعدادات إضافية كـ JSON
    
    # العلاقات
    logs = db.relationship('GameLog', backref='game', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, room_id, total_players, **kwargs):
        """إنشاء لعبة جديدة"""
        self.room_id = room_id
        self.total_players = total_players
        
        # حساب رقم اللعبة في الغرفة
        last_game = Game.query.filter_by(room_id=room_id).order_by(Game.game_number.desc()).first()
        self.game_number = (last_game.game_number + 1) if last_game else 1
        
        # تطبيق الإعدادات الاختيارية
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_settings(self, settings_dict):
        """تعيين إعدادات اللعبة"""
        self.settings = json.dumps(settings_dict, ensure_ascii=False)
    
    def get_settings(self):
        """الحصول على إعدادات اللعبة"""
        if self.settings:
            return json.loads(self.settings)
        return {}
    
    def start_phase(self, phase, duration=None):
        """بدء مرحلة جديدة"""
        self.phase = phase
        self.phase_start_time = datetime.utcnow()
        
        if duration:
            from datetime import timedelta
            self.phase_end_time = self.phase_start_time + timedelta(seconds=duration)
        else:
            self.phase_end_time = None
        
        db.session.commit()
        
        # تسجيل في السجل
        self.log_action(f"بدء مرحلة {phase.value}")
    
    def next_round(self):
        """الانتقال للجولة التالية"""
        self.current_round += 1
        db.session.commit()
        
        self.log_action(f"بدء الجولة {self.current_round}")
    
    def finish_game(self, winner, winner_team=None):
        """إنهاء اللعبة"""
        self.status = GameStatus.FINISHED
        self.phase = GamePhase.FINISHED
        self.winner = winner
        self.winner_team = winner_team
        self.finished_at = datetime.utcnow()
        
        db.session.commit()
        
        # تسجيل في السجل
        winner_text = {
            WinCondition.MAFIA_WIN: "فوز المافيا",
            WinCondition.CITIZENS_WIN: "فوز المواطنين",
            WinCondition.DRAW: "تعادل",
            WinCondition.CANCELLED: "ألغيت اللعبة"
        }.get(winner, "نتيجة غير معروفة")
        
        self.log_action(f"انتهت اللعبة - {winner_text}")
    
    def cancel_game(self, reason="ألغيت اللعبة"):
        """إلغاء اللعبة"""
        self.status = GameStatus.CANCELLED
        self.phase = GamePhase.FINISHED
        self.winner = WinCondition.CANCELLED
        self.finished_at = datetime.utcnow()
        
        db.session.commit()
        
        self.log_action(f"ألغيت اللعبة - {reason}")
    
    def pause_game(self):
        """إيقاف اللعبة مؤقتاً"""
        self.status = GameStatus.PAUSED
        db.session.commit()
        
        self.log_action("تم إيقاف اللعبة مؤقتاً")
    
    def resume_game(self):
        """استئناف اللعبة"""
        self.status = GameStatus.ACTIVE
        db.session.commit()
        
        self.log_action("تم استئناف اللعبة")
    
    def log_action(self, action, player_id=None, details=None):
        """تسجيل حدث في سجل اللعبة"""
        from .game_log import GameLog
        
        log_entry = GameLog(
            game_id=self.id,
            player_id=player_id,
            action=action,
            details=details,
            round_number=self.current_round,
            phase=self.phase.value
        )
        
        db.session.add(log_entry)
        db.session.commit()
    
    def get_duration(self):
        """حساب مدة اللعبة"""
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        else:
            return (datetime.utcnow() - self.started_at).total_seconds()
    
    def get_phase_remaining_time(self):
        """حساب الوقت المتبقي في المرحلة الحالية"""
        if not self.phase_end_time:
            return None
        
        remaining = (self.phase_end_time - datetime.utcnow()).total_seconds()
        return max(0, remaining)
    
    def is_phase_expired(self):
        """التحقق من انتهاء وقت المرحلة"""
        if not self.phase_end_time:
            return False
        
        return datetime.utcnow() >= self.phase_end_time
    
    def get_alive_players(self):
        """الحصول على اللاعبين الأحياء"""
        from .player import Player
        return Player.query.filter_by(
            room_id=self.room_id,
            is_alive=True
        ).all()
    
    def get_mafia_players(self):
        """الحصول على لاعبي المافيا الأحياء"""
        from .player import Player, PlayerRole
        return Player.query.filter_by(
            room_id=self.room_id,
            is_alive=True,
            role=PlayerRole.MAFIA
        ).all()
    
    def get_citizen_players(self):
        """الحصول على المواطنين الأحياء"""
        from .player import Player, PlayerRole
        return Player.query.filter(
            Player.room_id == self.room_id,
            Player.is_alive == True,
            Player.role != PlayerRole.MAFIA
        ).all()
    
    def check_win_condition(self):
        """فحص شروط الفوز"""
        alive_players = self.get_alive_players()
        mafia_count = len([p for p in alive_players if p.role.name == 'MAFIA'])
        citizen_count = len(alive_players) - mafia_count
        
        if mafia_count == 0:
            return WinCondition.CITIZENS_WIN, "citizens"
        elif mafia_count >= citizen_count:
            return WinCondition.MAFIA_WIN, "mafia"
        else:
            return None, None
    
    def to_dict(self):
        """تحويل اللعبة إلى قاموس"""
        return {
            'id': self.id,
            'room_id': self.room_id,
            'game_number': self.game_number,
            'total_players': self.total_players,
            'status': self.status.value,
            'phase': self.phase.value,
            'current_round': self.current_round,
            'phase_start_time': self.phase_start_time.isoformat(),
            'phase_end_time': self.phase_end_time.isoformat() if self.phase_end_time else None,
            'phase_remaining_time': self.get_phase_remaining_time(),
            'started_at': self.started_at.isoformat(),
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration': self.get_duration(),
            'winner': self.winner.value if self.winner else None,
            'winner_team': self.winner_team,
            'settings': self.get_settings()
        }
    
    def __repr__(self):
        return f'<Game {self.id}: Room {self.room_id}, Game #{self.game_number}>'
    
    def __str__(self):
        return f"لعبة #{self.game_number} - الجولة {self.current_round}"