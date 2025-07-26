#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الإحصائيات
Statistics Model
"""

from datetime import datetime
import json
from . import db

class UserStatistics(db.Model):
    """نموذج إحصائيات المستخدم المفصلة"""
    
    __tablename__ = 'user_statistics'
    
    # المعرف الأساسي
    id = db.Column(db.Integer, primary_key=True)
    
    # ربط مع المستخدم
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # إحصائيات الألعاب العامة
    total_games_played = db.Column(db.Integer, default=0, nullable=False)
    games_won = db.Column(db.Integer, default=0, nullable=False)
    games_lost = db.Column(db.Integer, default=0, nullable=False)
    games_drawn = db.Column(db.Integer, default=0, nullable=False)
    
    # إحصائيات الأدوار
    games_as_citizen = db.Column(db.Integer, default=0, nullable=False)
    games_as_mafia = db.Column(db.Integer, default=0, nullable=False)
    games_as_doctor = db.Column(db.Integer, default=0, nullable=False)
    games_as_detective = db.Column(db.Integer, default=0, nullable=False)
    games_as_vigilante = db.Column(db.Integer, default=0, nullable=False)
    games_as_mayor = db.Column(db.Integer, default=0, nullable=False)
    games_as_jester = db.Column(db.Integer, default=0, nullable=False)
    
    # إحصائيات الفوز بكل دور
    wins_as_citizen = db.Column(db.Integer, default=0, nullable=False)
    wins_as_mafia = db.Column(db.Integer, default=0, nullable=False)
    wins_as_doctor = db.Column(db.Integer, default=0, nullable=False)
    wins_as_detective = db.Column(db.Integer, default=0, nullable=False)
    wins_as_vigilante = db.Column(db.Integer, default=0, nullable=False)
    wins_as_mayor = db.Column(db.Integer, default=0, nullable=False)
    wins_as_jester = db.Column(db.Integer, default=0, nullable=False)
    
    # إحصائيات البقاء
    times_survived = db.Column(db.Integer, default=0, nullable=False)
    times_killed_by_mafia = db.Column(db.Integer, default=0, nullable=False)
    times_lynched = db.Column(db.Integer, default=0, nullable=False)
    times_killed_by_vigilante = db.Column(db.Integer, default=0, nullable=False)
    
    # إحصائيات التصويت
    total_votes_cast = db.Column(db.Integer, default=0, nullable=False)
    correct_votes = db.Column(db.Integer, default=0, nullable=False)  # تصويت ضد مافيا
    incorrect_votes = db.Column(db.Integer, default=0, nullable=False)  # تصويت ضد مواطنين
    times_voted_out = db.Column(db.Integer, default=0, nullable=False)
    
    # إحصائيات الأعمال الخاصة
    successful_heals = db.Column(db.Integer, default=0, nullable=False)      # للطبيب
    failed_heals = db.Column(db.Integer, default=0, nullable=False)
    successful_investigations = db.Column(db.Integer, default=0, nullable=False)  # للمحقق
    mafia_kills_made = db.Column(db.Integer, default=0, nullable=False)     # للمافيا
    vigilante_kills_made = db.Column(db.Integer, default=0, nullable=False) # للعدالة الشعبية
    
    # إحصائيات الدردشة
    total_messages_sent = db.Column(db.Integer, default=0, nullable=False)
    average_message_length = db.Column(db.Float, default=0.0, nullable=False)
    messages_flagged_suspicious = db.Column(db.Integer, default=0, nullable=False)
    
    # إحصائيات السلوك
    average_suspicion_score = db.Column(db.Float, default=0.0, nullable=False)
    times_accused = db.Column(db.Integer, default=0, nullable=False)
    times_defended = db.Column(db.Integer, default=0, nullable=False)
    
    # معلومات الوقت
    total_playtime_seconds = db.Column(db.Integer, default=0, nullable=False)
    average_game_duration = db.Column(db.Float, default=0.0, nullable=False)
    
    # إحصائيات متقدمة (JSON)
    detailed_stats = db.Column(db.Text, nullable=True)
    
    # معلومات التحديث
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, user_id):
        """إنشاء إحصائيات جديدة للمستخدم"""
        self.user_id = user_id
    
    def update_game_stats(self, role, won, game_duration, survived=False):
        """تحديث إحصائيات اللعبة"""
        # إحصائيات عامة
        self.total_games_played += 1
        if won:
            self.games_won += 1
        else:
            self.games_lost += 1
        
        if survived:
            self.times_survived += 1
        
        # إحصائيات الأدوار
        role_games_attr = f"games_as_{role.lower()}"
        if hasattr(self, role_games_attr):
            setattr(self, role_games_attr, getattr(self, role_games_attr) + 1)
        
        # إحصائيات الفوز بالأدوار
        if won:
            role_wins_attr = f"wins_as_{role.lower()}"
            if hasattr(self, role_wins_attr):
                setattr(self, role_wins_attr, getattr(self, role_wins_attr) + 1)
        
        # إحصائيات الوقت
        self.total_playtime_seconds += int(game_duration)
        self._update_average_game_duration()
        
        db.session.commit()
    
    def update_death_stats(self, cause):
        """تحديث إحصائيات الوفاة"""
        if cause == "mafia_kill":
            self.times_killed_by_mafia += 1
        elif cause == "lynch":
            self.times_lynched += 1
        elif cause == "vigilante_kill":
            self.times_killed_by_vigilante += 1
        
        db.session.commit()
    
    def update_vote_stats(self, was_correct):
        """تحديث إحصائيات التصويت"""
        self.total_votes_cast += 1
        if was_correct:
            self.correct_votes += 1
        else:
            self.incorrect_votes += 1
        
        db.session.commit()
    
    def update_action_stats(self, action_type, was_successful=False):
        """تحديث إحصائيات الأعمال الخاصة"""
        if action_type == "heal":
            if was_successful:
                self.successful_heals += 1
            else:
                self.failed_heals += 1
        elif action_type == "investigate":
            if was_successful:
                self.successful_investigations += 1
        elif action_type == "mafia_kill":
            self.mafia_kills_made += 1
        elif action_type == "vigilante_kill":
            self.vigilante_kills_made += 1
        
        db.session.commit()
    
    def update_chat_stats(self, message_length, suspicion_score=0.0, is_flagged=False):
        """تحديث إحصائيات الدردشة"""
        self.total_messages_sent += 1
        
        # تحديث متوسط طول الرسالة
        total_length = self.average_message_length * (self.total_messages_sent - 1) + message_length
        self.average_message_length = total_length / self.total_messages_sent
        
        # تحديث مؤشر الشك
        if suspicion_score > 0:
            total_suspicion = self.average_suspicion_score * (self.total_messages_sent - 1) + suspicion_score
            self.average_suspicion_score = total_suspicion / self.total_messages_sent
        
        if is_flagged:
            self.messages_flagged_suspicious += 1
        
        db.session.commit()
    
    def _update_average_game_duration(self):
        """تحديث متوسط مدة اللعبة"""
        if self.total_games_played > 0:
            self.average_game_duration = self.total_playtime_seconds / self.total_games_played
    
    def get_win_rate(self):
        """حساب معدل الفوز العام"""
        if self.total_games_played == 0:
            return 0.0
        return (self.games_won / self.total_games_played) * 100
    
    def get_survival_rate(self):
        """حساب معدل البقاء"""
        if self.total_games_played == 0:
            return 0.0
        return (self.times_survived / self.total_games_played) * 100
    
    def get_vote_accuracy(self):
        """حساب دقة التصويت"""
        if self.total_votes_cast == 0:
            return 0.0
        return (self.correct_votes / self.total_votes_cast) * 100
    
    def get_role_win_rate(self, role):
        """حساب معدل الفوز بدور معين"""
        games_attr = f"games_as_{role.lower()}"
        wins_attr = f"wins_as_{role.lower()}"
        
        if not hasattr(self, games_attr) or not hasattr(self, wins_attr):
            return 0.0
        
        games = getattr(self, games_attr)
        wins = getattr(self, wins_attr)
        
        if games == 0:
            return 0.0
        
        return (wins / games) * 100
    
    def get_favorite_role(self):
        """الحصول على الدور المفضل (الأكثر لعباً)"""
        roles = [
            ('citizen', self.games_as_citizen),
            ('mafia', self.games_as_mafia),
            ('doctor', self.games_as_doctor),
            ('detective', self.games_as_detective),
            ('vigilante', self.games_as_vigilante),
            ('mayor', self.games_as_mayor),
            ('jester', self.games_as_jester)
        ]
        
        favorite = max(roles, key=lambda x: x[1])
        return favorite[0] if favorite[1] > 0 else None
    
    def get_best_role(self):
        """الحصول على أفضل دور (أعلى معدل فوز)"""
        roles = ['citizen', 'mafia', 'doctor', 'detective', 'vigilante', 'mayor', 'jester']
        best_role = None
        best_rate = 0
        
        for role in roles:
            rate = self.get_role_win_rate(role)
            if rate > best_rate:
                best_rate = rate
                best_role = role
        
        return best_role, best_rate
    
    def set_detailed_stats(self, stats):
        """تعيين الإحصائيات المفصلة"""
        self.detailed_stats = json.dumps(stats, ensure_ascii=False)
    
    def get_detailed_stats(self):
        """الحصول على الإحصائيات المفصلة"""
        if self.detailed_stats:
            return json.loads(self.detailed_stats)
        return {}
    
    def to_dict(self, detailed=False):
        """تحويل الإحصائيات إلى قاموس"""
        data = {
            'user_id': self.user_id,
            'total_games_played': self.total_games_played,
            'games_won': self.games_won,
            'games_lost': self.games_lost,
            'games_drawn': self.games_drawn,
            'win_rate': self.get_win_rate(),
            'survival_rate': self.get_survival_rate(),
            'vote_accuracy': self.get_vote_accuracy(),
            'favorite_role': self.get_favorite_role(),
            'total_playtime_hours': round(self.total_playtime_seconds / 3600, 2),
            'average_game_duration_minutes': round(self.average_game_duration / 60, 2),
            'total_messages_sent': self.total_messages_sent,
            'average_message_length': round(self.average_message_length, 1),
            'average_suspicion_score': round(self.average_suspicion_score, 3),
            'last_updated': self.last_updated.isoformat()
        }
        
        if detailed:
            best_role, best_rate = self.get_best_role()
            
            data.update({
                # إحصائيات الأدوار
                'role_stats': {
                    'citizen': {
                        'games': self.games_as_citizen,
                        'wins': self.wins_as_citizen,
                        'win_rate': self.get_role_win_rate('citizen')
                    },
                    'mafia': {
                        'games': self.games_as_mafia,
                        'wins': self.wins_as_mafia,
                        'win_rate': self.get_role_win_rate('mafia')
                    },
                    'doctor': {
                        'games': self.games_as_doctor,
                        'wins': self.wins_as_doctor,
                        'win_rate': self.get_role_win_rate('doctor')
                    },
                    'detective': {
                        'games': self.games_as_detective,
                        'wins': self.wins_as_detective,
                        'win_rate': self.get_role_win_rate('detective')
                    },
                    'vigilante': {
                        'games': self.games_as_vigilante,
                        'wins': self.wins_as_vigilante,
                        'win_rate': self.get_role_win_rate('vigilante')
                    },
                    'mayor': {
                        'games': self.games_as_mayor,
                        'wins': self.wins_as_mayor,
                        'win_rate': self.get_role_win_rate('mayor')
                    },
                    'jester': {
                        'games': self.games_as_jester,
                        'wins': self.wins_as_jester,
                        'win_rate': self.get_role_win_rate('jester')
                    }
                },
                
                # إحصائيات البقاء والوفاة
                'survival_stats': {
                    'times_survived': self.times_survived,
                    'times_killed_by_mafia': self.times_killed_by_mafia,
                    'times_lynched': self.times_lynched,
                    'times_killed_by_vigilante': self.times_killed_by_vigilante
                },
                
                # إحصائيات التصويت
                'voting_stats': {
                    'total_votes_cast': self.total_votes_cast,
                    'correct_votes': self.correct_votes,
                    'incorrect_votes': self.incorrect_votes,
                    'times_voted_out': self.times_voted_out
                },
                
                # إحصائيات الأعمال الخاصة
                'action_stats': {
                    'successful_heals': self.successful_heals,
                    'failed_heals': self.failed_heals,
                    'successful_investigations': self.successful_investigations,
                    'mafia_kills_made': self.mafia_kills_made,
                    'vigilante_kills_made': self.vigilante_kills_made
                },
                
                # إحصائيات السلوك
                'behavior_stats': {
                    'messages_flagged_suspicious': self.messages_flagged_suspicious,
                    'times_accused': self.times_accused,
                    'times_defended': self.times_defended
                },
                
                'best_role': best_role,
                'best_role_win_rate': best_rate,
                'detailed_stats': self.get_detailed_stats()
            })
        
        return data
    
    def __repr__(self):
        return f'<UserStatistics for User {self.user_id}>'
    
    def __str__(self):
        return f"إحصائيات {self.user.display_name if self.user else f'المستخدم {self.user_id}'}"