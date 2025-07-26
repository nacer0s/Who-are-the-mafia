#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج اللاعب
Player Model
"""

from datetime import datetime
from enum import Enum
import json
from . import db

class PlayerRole(Enum):
    """أدوار اللاعبين"""
    CITIZEN = "citizen"       # مواطن عادي
    MAFIA = "mafia"          # مافيا
    DOCTOR = "doctor"        # طبيب
    DETECTIVE = "detective"   # محقق/شرطي
    VIGILANTE = "vigilante"   # العدالة الشعبية
    MAYOR = "mayor"          # عمدة
    JESTER = "jester"        # مهرج

class PlayerStatus(Enum):
    """حالات اللاعب"""
    ALIVE = "alive"         # حي
    DEAD = "dead"           # ميت
    ELIMINATED = "eliminated" # مطرود
    LEFT = "left"           # غادر اللعبة

class DeathCause(Enum):
    """أسباب الوفاة"""
    MAFIA_KILL = "mafia_kill"     # قتل المافيا
    LYNCH = "lynch"               # إعدام بالتصويت
    VIGILANTE_KILL = "vigilante_kill"  # قتل العدالة الشعبية
    LEFT_GAME = "left_game"       # غادر اللعبة
    OTHER = "other"               # سبب آخر

class Player(db.Model):
    """نموذج اللاعب في اللعبة"""
    
    __tablename__ = 'players'
    
    # المعرف الأساسي
    id = db.Column(db.Integer, primary_key=True)
    
    # ربط مع المستخدم والغرفة
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    
    # معلومات اللاعب في اللعبة
    role = db.Column(db.Enum(PlayerRole), nullable=True)  # يتم تعيينه عند بدء اللعبة
    status = db.Column(db.Enum(PlayerStatus), default=PlayerStatus.ALIVE, nullable=False)
    
    # معلومات الحالة
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_alive = db.Column(db.Boolean, default=True, nullable=False)
    is_ready = db.Column(db.Boolean, default=False, nullable=False)
    
    # معلومات الوفاة
    death_cause = db.Column(db.Enum(DeathCause), nullable=True)
    death_round = db.Column(db.Integer, nullable=True)
    death_time = db.Column(db.DateTime, nullable=True)
    killed_by_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    
    # معلومات التصويت والأعمال
    votes_cast = db.Column(db.Integer, default=0, nullable=False)
    votes_received = db.Column(db.Integer, default=0, nullable=False)
    actions_taken = db.Column(db.Integer, default=0, nullable=False)
    
    # معلومات إضافية (JSON)
    extra_data = db.Column(db.Text, nullable=True)  # بيانات إضافية كـ JSON
    
    # معلومات التوقيت
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    left_at = db.Column(db.DateTime, nullable=True)
    
    # العلاقات
    killed_by = db.relationship('Player', remote_side=[id], backref='victims')
    
    def __init__(self, user_id, room_id, **kwargs):
        """إنشاء لاعب جديد"""
        self.user_id = user_id
        self.room_id = room_id
        
        # تطبيق الإعدادات الاختيارية
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def assign_role(self, role):
        """تعيين دور للاعب"""
        self.role = role
        db.session.commit()
        
        # تسجيل في سجل اللعبة
        game = self.get_current_game()
        if game:
            game.log_action(
                f"تم تعيين دور {self.get_role_name()} للاعب {self.user.display_name}",
                player_id=self.id
            )
    
    def kill(self, cause=DeathCause.OTHER, killed_by=None, round_number=None):
        """قتل اللاعب"""
        if not self.is_alive:
            return False, "اللاعب ميت بالفعل"
        
        self.is_alive = False
        self.status = PlayerStatus.DEAD
        self.death_cause = cause
        self.death_time = datetime.utcnow()
        self.death_round = round_number
        
        if killed_by:
            self.killed_by_id = killed_by
        
        db.session.commit()
        
        # تسجيل في سجل اللعبة
        game = self.get_current_game()
        if game:
            cause_text = self.get_death_cause_text()
            game.log_action(
                f"مات {self.user.display_name} - {cause_text}",
                player_id=self.id,
                details={'cause': cause.value, 'killed_by': killed_by}
            )
        
        return True, "تم قتل اللاعب"
    
    def eliminate(self, round_number=None):
        """طرد اللاعب من اللعبة"""
        return self.kill(DeathCause.LYNCH, round_number=round_number)
    
    def leave_game(self):
        """مغادرة اللعبة"""
        self.is_active = False
        self.left_at = datetime.utcnow()
        
        if self.is_alive:
            self.kill(DeathCause.LEFT_GAME)
        
        db.session.commit()
        
        # تسجيل في سجل اللعبة
        game = self.get_current_game()
        if game:
            game.log_action(
                f"غادر {self.user.display_name} اللعبة",
                player_id=self.id
            )
    
    def vote(self, target_player_id=None):
        """تسجيل صوت"""
        self.votes_cast += 1
        
        if target_player_id:
            target = Player.query.get(target_player_id)
            if target:
                target.votes_received += 1
                db.session.commit()
                
                # تسجيل في سجل اللعبة
                game = self.get_current_game()
                if game:
                    game.log_action(
                        f"صوت {self.user.display_name} ضد {target.user.display_name}",
                        player_id=self.id,
                        details={'target': target_player_id}
                    )
        
        db.session.commit()
    
    def take_action(self, action_type, target_id=None, details=None):
        """تنفيذ عمل (للأدوار الخاصة)"""
        self.actions_taken += 1
        
        # حفظ تفاصيل العمل
        extra_data = self.get_extra_data()
        if 'actions' not in extra_data:
            extra_data['actions'] = []
        
        action_data = {
            'type': action_type,
            'target_id': target_id,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        extra_data['actions'].append(action_data)
        self.set_extra_data(extra_data)
        
        db.session.commit()
        
        # تسجيل في سجل اللعبة
        game = self.get_current_game()
        if game:
            target_name = ""
            if target_id:
                target = Player.query.get(target_id)
                target_name = f" على {target.user.display_name}" if target else ""
            
            game.log_action(
                f"نفذ {self.user.display_name} عمل {action_type}{target_name}",
                player_id=self.id,
                details=action_data
            )
    
    def set_extra_data(self, data):
        """تعيين البيانات الإضافية"""
        self.extra_data = json.dumps(data, ensure_ascii=False)
    
    def get_extra_data(self):
        """الحصول على البيانات الإضافية"""
        if self.extra_data:
            return json.loads(self.extra_data)
        return {}
    
    def get_current_game(self):
        """الحصول على اللعبة الحالية"""
        from .game import Game, GameStatus
        return Game.query.filter_by(
            room_id=self.room_id,
            status=GameStatus.ACTIVE
        ).first()
    
    def get_role_name(self):
        """الحصول على اسم الدور بالعربية"""
        role_names = {
            PlayerRole.CITIZEN: "مواطن",
            PlayerRole.MAFIA: "مافيا",
            PlayerRole.DOCTOR: "طبيب",
            PlayerRole.DETECTIVE: "محقق",
            PlayerRole.VIGILANTE: "عدالة شعبية",
            PlayerRole.MAYOR: "عمدة",
            PlayerRole.JESTER: "مهرج"
        }
        return role_names.get(self.role, "غير معروف")
    
    def get_role_description(self):
        """الحصول على وصف الدور"""
        descriptions = {
            PlayerRole.CITIZEN: "مواطن عادي، هدفك العثور على المافيا والقضاء عليهم",
            PlayerRole.MAFIA: "أنت من المافيا، هدفك القضاء على جميع المواطنين",
            PlayerRole.DOCTOR: "يمكنك حماية لاعب واحد كل ليلة من الموت",
            PlayerRole.DETECTIVE: "يمكنك التحقق من هوية لاعب واحد كل ليلة",
            PlayerRole.VIGILANTE: "يمكنك قتل لاعب واحد كل ليلة",
            PlayerRole.MAYOR: "صوتك يحسب بصوتين في التصويت",
            PlayerRole.JESTER: "هدفك أن يتم إعدامك بالتصويت"
        }
        return descriptions.get(self.role, "دور غير معروف")
    
    def get_death_cause_text(self):
        """الحصول على نص سبب الوفاة"""
        cause_texts = {
            DeathCause.MAFIA_KILL: "قتلته المافيا",
            DeathCause.LYNCH: "أعدم بالتصويت",
            DeathCause.VIGILANTE_KILL: "قتلته العدالة الشعبية",
            DeathCause.LEFT_GAME: "غادر اللعبة",
            DeathCause.OTHER: "سبب آخر"
        }
        return cause_texts.get(self.death_cause, "سبب غير معروف")
    
    def can_vote(self):
        """التحقق من إمكانية التصويت"""
        return self.is_alive and self.is_active
    
    def can_take_action(self):
        """التحقق من إمكانية تنفيذ عمل"""
        return self.is_alive and self.is_active and self.role in [
            PlayerRole.DOCTOR, PlayerRole.DETECTIVE, 
            PlayerRole.VIGILANTE, PlayerRole.MAFIA
        ]
    
    def is_mafia(self):
        """التحقق من كون اللاعب من المافيا"""
        return self.role == PlayerRole.MAFIA
    
    def is_citizen(self):
        """التحقق من كون اللاعب مواطن"""
        return self.role != PlayerRole.MAFIA
    
    def to_dict(self, include_role=False, include_private=False):
        """تحويل اللاعب إلى قاموس"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'display_name': self.user.display_name if self.user else None,
            'avatar_url': self.user.avatar_url if self.user else None,
            'room_id': self.room_id,
            'status': self.status.value,
            'is_active': self.is_active,
            'is_alive': self.is_alive,
            'is_ready': self.is_ready,
            'votes_cast': self.votes_cast,
            'votes_received': self.votes_received,
            'actions_taken': self.actions_taken,
            'joined_at': self.joined_at.isoformat(),
            'left_at': self.left_at.isoformat() if self.left_at else None
        }
        
        # معلومات الدور (للاعب نفسه أو المشرف)
        if include_role and self.role:
            data.update({
                'role': self.role.value,
                'role_name': self.get_role_name(),
                'role_description': self.get_role_description(),
                'can_vote': self.can_vote(),
                'can_take_action': self.can_take_action()
            })
        
        # معلومات الوفاة
        if not self.is_alive:
            data.update({
                'death_cause': self.death_cause.value if self.death_cause else None,
                'death_cause_text': self.get_death_cause_text(),
                'death_round': self.death_round,
                'death_time': self.death_time.isoformat() if self.death_time else None,
                'killed_by_id': self.killed_by_id
            })
        
        # معلومات خاصة (للاعب نفسه فقط)
        if include_private:
            data['extra_data'] = self.get_extra_data()
        
        return data
    
    def __repr__(self):
        return f'<Player {self.user.username if self.user else self.user_id} in Room {self.room_id}>'
    
    def __str__(self):
        return f"{self.user.display_name if self.user else 'لاعب'} ({self.get_role_name() if self.role else 'بدون دور'})"