#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج سجل اللعبة
Game Log Model
"""

from datetime import datetime
from enum import Enum
import json
from . import db

class LogLevel(Enum):
    """مستويات السجل"""
    INFO = "info"         # معلومات عامة
    WARNING = "warning"   # تحذير
    ERROR = "error"       # خطأ
    DEBUG = "debug"       # تصحيح أخطاء
    GAME = "game"         # أحداث اللعبة
    ADMIN = "admin"       # أحداث إدارية

class GameLog(db.Model):
    """نموذج سجل أحداث اللعبة"""
    
    __tablename__ = 'game_logs'
    
    # المعرف الأساسي
    id = db.Column(db.Integer, primary_key=True)
    
    # ربط مع اللعبة واللاعب
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    
    # معلومات السجل
    action = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    level = db.Column(db.Enum(LogLevel), default=LogLevel.INFO, nullable=False)
    
    # معلومات اللعبة
    round_number = db.Column(db.Integer, nullable=True)
    phase = db.Column(db.String(20), nullable=True)
    
    # معلومات إضافية
    details = db.Column(db.Text, nullable=True)  # تفاصيل إضافية كـ JSON
    
    # معلومات التوقيت
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # العلاقات
    player = db.relationship('Player', backref='logs')
    
    def __init__(self, game_id, action, **kwargs):
        """إنشاء سجل جديد"""
        self.game_id = game_id
        self.action = action
        
        # تطبيق الإعدادات الاختيارية
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_details(self, details):
        """تعيين التفاصيل الإضافية"""
        if details:
            self.details = json.dumps(details, ensure_ascii=False)
    
    def get_details(self):
        """الحصول على التفاصيل الإضافية"""
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self, include_details=False):
        """تحويل السجل إلى قاموس"""
        data = {
            'id': self.id,
            'game_id': self.game_id,
            'player_id': self.player_id,
            'player_name': self.player.user.display_name if self.player and self.player.user else None,
            'action': self.action,
            'description': self.description,
            'level': self.level.value,
            'round_number': self.round_number,
            'phase': self.phase,
            'created_at': self.created_at.isoformat()
        }
        
        if include_details:
            data['details'] = self.get_details()
        
        return data
    
    @staticmethod
    def log_game_start(game_id, total_players):
        """تسجيل بدء اللعبة"""
        log = GameLog(
            game_id=game_id,
            action="بدء اللعبة",
            description=f"بدأت اللعبة بـ {total_players} لاعبين",
            level=LogLevel.GAME,
            round_number=1
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_game_end(game_id, winner, winner_team=None):
        """تسجيل انتهاء اللعبة"""
        winner_text = {
            'mafia_win': 'فوز المافيا',
            'citizens_win': 'فوز المواطنين',
            'draw': 'تعادل',
            'cancelled': 'ألغيت اللعبة'
        }.get(winner, 'نتيجة غير معروفة')
        
        log = GameLog(
            game_id=game_id,
            action="انتهاء اللعبة",
            description=f"انتهت اللعبة - {winner_text}",
            level=LogLevel.GAME,
            details={'winner': winner, 'winner_team': winner_team}
        )
        log.set_details({'winner': winner, 'winner_team': winner_team})
        
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_player_death(game_id, player_id, cause, round_number, phase):
        """تسجيل وفاة لاعب"""
        from .player import Player
        player = Player.query.get(player_id)
        player_name = player.user.display_name if player and player.user else "لاعب"
        
        cause_text = {
            'mafia_kill': 'قتلته المافيا',
            'lynch': 'أعدم بالتصويت',
            'vigilante_kill': 'قتلته العدالة الشعبية',
            'left_game': 'غادر اللعبة'
        }.get(cause, 'مات لسبب غير معروف')
        
        log = GameLog(
            game_id=game_id,
            player_id=player_id,
            action="وفاة لاعب",
            description=f"مات {player_name} - {cause_text}",
            level=LogLevel.GAME,
            round_number=round_number,
            phase=phase
        )
        log.set_details({'cause': cause})
        
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_vote(game_id, voter_id, target_id, round_number, phase):
        """تسجيل تصويت"""
        from .player import Player
        voter = Player.query.get(voter_id)
        target = Player.query.get(target_id)
        
        voter_name = voter.user.display_name if voter and voter.user else "لاعب"
        target_name = target.user.display_name if target and target.user else "لاعب"
        
        log = GameLog(
            game_id=game_id,
            player_id=voter_id,
            action="تصويت",
            description=f"صوت {voter_name} ضد {target_name}",
            level=LogLevel.GAME,
            round_number=round_number,
            phase=phase
        )
        log.set_details({'voter_id': voter_id, 'target_id': target_id})
        
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_phase_change(game_id, new_phase, round_number):
        """تسجيل تغيير المرحلة"""
        phase_names = {
            'day': 'النهار',
            'night': 'الليل',
            'voting': 'التصويت',
            'trial': 'المحاكمة'
        }
        
        phase_name = phase_names.get(new_phase, new_phase)
        
        log = GameLog(
            game_id=game_id,
            action="تغيير المرحلة",
            description=f"بدأت مرحلة {phase_name}",
            level=LogLevel.GAME,
            round_number=round_number,
            phase=new_phase
        )
        
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_role_action(game_id, player_id, action_type, target_id, round_number, phase):
        """تسجيل عمل دور خاص"""
        from .player import Player
        player = Player.query.get(player_id)
        target = Player.query.get(target_id) if target_id else None
        
        player_name = player.user.display_name if player and player.user else "لاعب"
        target_name = target.user.display_name if target and target.user else "لاعب"
        
        action_names = {
            'heal': 'علاج',
            'investigate': 'تحقيق',
            'kill': 'قتل',
            'protect': 'حماية'
        }
        
        action_name = action_names.get(action_type, action_type)
        target_text = f" على {target_name}" if target_id else ""
        
        log = GameLog(
            game_id=game_id,
            player_id=player_id,
            action="عمل دور",
            description=f"نفذ {player_name} عمل {action_name}{target_text}",
            level=LogLevel.GAME,
            round_number=round_number,
            phase=phase
        )
        log.set_details({
            'action_type': action_type,
            'target_id': target_id
        })
        
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_suspicious_activity(game_id, player_id, activity_type, details, round_number=None, phase=None):
        """تسجيل نشاط مشبوه"""
        from .player import Player
        player = Player.query.get(player_id)
        player_name = player.user.display_name if player and player.user else "لاعب"
        
        log = GameLog(
            game_id=game_id,
            player_id=player_id,
            action="نشاط مشبوه",
            description=f"نشاط مشبوه من {player_name}: {activity_type}",
            level=LogLevel.WARNING,
            round_number=round_number,
            phase=phase
        )
        log.set_details({
            'activity_type': activity_type,
            'details': details
        })
        
        db.session.add(log)
        db.session.commit()
        return log
    
    def __repr__(self):
        return f'<GameLog {self.id}: {self.action} in Game {self.game_id}>'
    
    def __str__(self):
        return f"[{self.level.value.upper()}] {self.action}: {self.description}"