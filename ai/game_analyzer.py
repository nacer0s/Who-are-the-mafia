#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محلل اللعب بالذكاء الاصطناعي
AI Game Analyzer
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from models import Game, Player, Message, GameLog
from models.player import PlayerRole

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class GameAnalyzer:
    """محلل اللعب للكشف عن الأنماط المشبوهة وتحليل الاستراتيجيات"""
    
    def __init__(self, openai_api_key: str = None):
        """إنشاء محلل اللعب"""
        self.openai_available = OPENAI_AVAILABLE and openai_api_key
        
        if self.openai_available:
            try:
                if hasattr(openai, 'OpenAI'):
                    self.client = openai.OpenAI(api_key=openai_api_key)
                else:
                    openai.api_key = openai_api_key
                    self.client = openai
            except Exception as e:
                print(f"⚠️ فشل في تهيئة OpenAI لتحليل الألعاب: {e}")
                self.openai_available = False
    
    def analyze_player_behavior(self, player_id: int, game_id: int) -> Dict:
        """تحليل سلوك لاعب معين في لعبة"""
        try:
            player = Player.query.get(player_id)
            game = Game.query.get(game_id)
            
            if not player or not game:
                return {'error': 'اللاعب أو اللعبة غير موجودة'}
            
            # جمع البيانات
            messages = Message.query.filter_by(
                user_id=player.user_id,
                room_id=game.room_id
            ).order_by(Message.sent_at).all()
            
            game_logs = GameLog.query.filter_by(
                game_id=game_id,
                player_id=player_id
            ).order_by(GameLog.created_at).all()
            
            # تحليل الرسائل
            message_analysis = self._analyze_player_messages(messages, player.role)
            
            # تحليل الأعمال
            action_analysis = self._analyze_player_actions(game_logs, player.role)
            
            # تحليل التصويت
            voting_analysis = self._analyze_player_voting(player_id, game_id)
            
            # تحليل عام
            overall_analysis = self._get_overall_player_analysis(
                player, message_analysis, action_analysis, voting_analysis
            )
            
            return {
                'player_id': player_id,
                'game_id': game_id,
                'role': player.role.value if player.role else None,
                'is_alive': player.is_alive,
                'message_analysis': message_analysis,
                'action_analysis': action_analysis,
                'voting_analysis': voting_analysis,
                'overall_analysis': overall_analysis,
                'suspicion_level': overall_analysis.get('suspicion_level', 'low'),
                'recommendations': overall_analysis.get('recommendations', [])
            }
            
        except Exception as e:
            return {'error': f'خطأ في تحليل اللاعب: {str(e)}'}
    
    def _analyze_player_messages(self, messages: List[Message], role: PlayerRole) -> Dict:
        """تحليل رسائل اللاعب"""
        
        if not messages:
            return {
                'total_messages': 0,
                'average_length': 0,
                'sentiment_distribution': {},
                'suspicious_patterns': [],
                'communication_style': 'silent'
            }
        
        # إحصائيات أساسية
        total_messages = len(messages)
        total_length = sum(len(msg.content) for msg in messages)
        average_length = total_length / total_messages if total_messages > 0 else 0
        
        # تحليل التوزيع الزمني
        day_messages = sum(1 for msg in messages if msg.game_phase == 'day')
        night_messages = sum(1 for msg in messages if msg.game_phase == 'night')
        voting_messages = sum(1 for msg in messages if msg.game_phase == 'voting')
        
        # تحليل الأنماط المشبوهة
        suspicious_patterns = []
        flagged_messages = sum(1 for msg in messages if msg.is_flagged)
        
        if flagged_messages > 0:
            suspicious_patterns.append({
                'type': 'flagged_messages',
                'count': flagged_messages,
                'description': f'{flagged_messages} رسالة مبلغ عنها'
            })
        
        # تحليل النشاط حسب المرحلة
        if role == PlayerRole.MAFIA and night_messages > day_messages * 2:
            suspicious_patterns.append({
                'type': 'unusual_night_activity',
                'description': 'نشاط ليلي غير عادي للمافيا'
            })
        
        # تحليل نمط التواصل
        communication_style = 'normal'
        if total_messages == 0:
            communication_style = 'silent'
        elif total_messages < 5:
            communication_style = 'quiet'
        elif total_messages > 50:
            communication_style = 'talkative'
        elif average_length > 100:
            communication_style = 'verbose'
        elif average_length < 20:
            communication_style = 'brief'
        
        return {
            'total_messages': total_messages,
            'average_length': round(average_length, 2),
            'phase_distribution': {
                'day': day_messages,
                'night': night_messages,
                'voting': voting_messages
            },
            'suspicious_patterns': suspicious_patterns,
            'communication_style': communication_style,
            'flagged_messages': flagged_messages
        }
    
    def _analyze_player_actions(self, game_logs: List[GameLog], role: PlayerRole) -> Dict:
        """تحليل أعمال اللاعب"""
        
        if not game_logs:
            return {
                'total_actions': 0,
                'action_types': {},
                'timing_analysis': {},
                'effectiveness': 'unknown'
            }
        
        # تصنيف الأعمال
        action_types = {}
        for log in game_logs:
            action = log.action
            action_types[action] = action_types.get(action, 0) + 1
        
        # تحليل التوقيت
        timing_analysis = {
            'early_actions': 0,
            'late_actions': 0,
            'consistent_timing': True
        }
        
        # تحليل الفعالية حسب الدور
        effectiveness = self._analyze_role_effectiveness(game_logs, role)
        
        return {
            'total_actions': len(game_logs),
            'action_types': action_types,
            'timing_analysis': timing_analysis,
            'effectiveness': effectiveness
        }
    
    def _analyze_player_voting(self, player_id: int, game_id: int) -> Dict:
        """تحليل أنماط التصويت"""
        
        # هنا نحتاج للبحث في سجلات التصويت
        # نفترض وجود سجلات التصويت في GameLog
        
        voting_logs = GameLog.query.filter_by(
            game_id=game_id,
            player_id=player_id,
            action='تصويت'
        ).all()
        
        if not voting_logs:
            return {
                'total_votes': 0,
                'voting_pattern': 'no_votes',
                'accuracy': 0.0
            }
        
        total_votes = len(voting_logs)
        
        # تحليل دقة التصويت (يحتاج لمنطق أكثر تعقيداً)
        # هنا نحتاج لمعرفة من كانوا مافيا ومن صوت ضدهم
        
        return {
            'total_votes': total_votes,
            'voting_pattern': 'active' if total_votes > 3 else 'passive',
            'accuracy': 0.0  # يحتاج تحسين
        }
    
    def _analyze_role_effectiveness(self, game_logs: List[GameLog], role: PlayerRole) -> str:
        """تحليل فعالية اللاعب في دوره"""
        
        if not game_logs:
            return 'inactive'
        
        # تحليل حسب الدور
        if role == PlayerRole.DOCTOR:
            heal_actions = [log for log in game_logs if 'علاج' in log.action]
            if len(heal_actions) >= 2:
                return 'active'
            elif len(heal_actions) == 1:
                return 'moderate'
            else:
                return 'inactive'
        
        elif role == PlayerRole.DETECTIVE:
            investigate_actions = [log for log in game_logs if 'تحقيق' in log.action]
            if len(investigate_actions) >= 2:
                return 'active'
            elif len(investigate_actions) == 1:
                return 'moderate'
            else:
                return 'inactive'
        
        elif role == PlayerRole.MAFIA:
            kill_actions = [log for log in game_logs if 'قتل' in log.action]
            if len(kill_actions) >= 1:
                return 'active'
            else:
                return 'inactive'
        
        else:
            # للمواطنين العاديين
            if len(game_logs) > 0:
                return 'active'
            else:
                return 'inactive'
    
    def _get_overall_player_analysis(self, player: Player, message_analysis: Dict, 
                                   action_analysis: Dict, voting_analysis: Dict) -> Dict:
        """التحليل العام للاعب"""
        
        suspicion_factors = []
        suspicion_score = 0.0
        
        # تحليل النشاط
        if message_analysis['communication_style'] == 'silent':
            suspicion_factors.append('صامت جداً')
            suspicion_score += 0.2
        elif message_analysis['communication_style'] == 'talkative':
            suspicion_factors.append('كثير الكلام')
            suspicion_score += 0.1
        
        # تحليل الرسائل المشبوهة
        if message_analysis['flagged_messages'] > 0:
            suspicion_factors.append('رسائل مبلغ عنها')
            suspicion_score += 0.3 * (message_analysis['flagged_messages'] / message_analysis['total_messages'])
        
        # تحليل فعالية الدور
        if action_analysis['effectiveness'] == 'inactive':
            suspicion_factors.append('غير نشط في دوره')
            suspicion_score += 0.15
        
        # تحديد مستوى الشك
        if suspicion_score > 0.6:
            suspicion_level = 'high'
        elif suspicion_score > 0.3:
            suspicion_level = 'medium'
        else:
            suspicion_level = 'low'
        
        # التوصيات
        recommendations = []
        
        if suspicion_level == 'high':
            recommendations.append('مراقبة مشددة')
            recommendations.append('فحص رسائله بعناية')
        elif suspicion_level == 'medium':
            recommendations.append('مراقبة عادية')
        
        if message_analysis['communication_style'] == 'silent':
            recommendations.append('تشجيعه على المشاركة أكثر')
        
        return {
            'suspicion_score': round(suspicion_score, 2),
            'suspicion_level': suspicion_level,
            'suspicion_factors': suspicion_factors,
            'recommendations': recommendations,
            'overall_rating': self._calculate_player_rating(message_analysis, action_analysis, voting_analysis)
        }
    
    def _calculate_player_rating(self, message_analysis: Dict, action_analysis: Dict, voting_analysis: Dict) -> str:
        """حساب تقييم عام للاعب"""
        
        score = 0
        
        # نقاط المشاركة
        if message_analysis['total_messages'] > 10:
            score += 2
        elif message_analysis['total_messages'] > 5:
            score += 1
        
        # نقاط الفعالية
        if action_analysis['effectiveness'] == 'active':
            score += 2
        elif action_analysis['effectiveness'] == 'moderate':
            score += 1
        
        # نقاط التصويت
        if voting_analysis['voting_pattern'] == 'active':
            score += 1
        
        # خصم نقاط للسلوك المشبوه
        if message_analysis['flagged_messages'] > 0:
            score -= 1
        
        # تحديد التقييم
        if score >= 4:
            return 'excellent'
        elif score >= 2:
            return 'good'
        elif score >= 0:
            return 'fair'
        else:
            return 'poor'
    
    def analyze_game_flow(self, game_id: int) -> Dict:
        """تحليل تدفق اللعبة"""
        try:
            game = Game.query.get(game_id)
            if not game:
                return {'error': 'اللعبة غير موجودة'}
            
            # جمع بيانات اللعبة
            players = Player.query.filter_by(room_id=game.room_id).all()
            messages = Message.query.filter_by(room_id=game.room_id).order_by(Message.sent_at).all()
            game_logs = GameLog.query.filter_by(game_id=game_id).order_by(GameLog.created_at).all()
            
            # تحليل المراحل
            phase_analysis = self._analyze_game_phases(messages, game_logs)
            
            # تحليل التفاعل
            interaction_analysis = self._analyze_player_interactions(messages, players)
            
            # تحليل النتيجة
            outcome_analysis = self._analyze_game_outcome(game, players)
            
            return {
                'game_id': game_id,
                'total_players': len(players),
                'game_duration': game.get_duration() if hasattr(game, 'get_duration') else 0,
                'phase_analysis': phase_analysis,
                'interaction_analysis': interaction_analysis,
                'outcome_analysis': outcome_analysis,
                'overall_quality': self._rate_game_quality(phase_analysis, interaction_analysis)
            }
            
        except Exception as e:
            return {'error': f'خطأ في تحليل اللعبة: {str(e)}'}
    
    def _analyze_game_phases(self, messages: List[Message], game_logs: List[GameLog]) -> Dict:
        """تحليل مراحل اللعبة"""
        
        phase_stats = {
            'day': {'messages': 0, 'duration': 0},
            'night': {'messages': 0, 'duration': 0},
            'voting': {'messages': 0, 'duration': 0}
        }
        
        for message in messages:
            if message.game_phase in phase_stats:
                phase_stats[message.game_phase]['messages'] += 1
        
        return {
            'phase_distribution': phase_stats,
            'total_rounds': max((log.round_number for log in game_logs), default=0),
            'phase_balance': self._calculate_phase_balance(phase_stats)
        }
    
    def _analyze_player_interactions(self, messages: List[Message], players: List[Player]) -> Dict:
        """تحليل تفاعل اللاعبين"""
        
        active_players = len([p for p in players if p.user_id in [m.user_id for m in messages]])
        total_players = len(players)
        
        participation_rate = active_players / total_players if total_players > 0 else 0
        
        return {
            'active_players': active_players,
            'total_players': total_players,
            'participation_rate': round(participation_rate, 2),
            'average_messages_per_player': len(messages) / active_players if active_players > 0 else 0
        }
    
    def _analyze_game_outcome(self, game: Game, players: List[Player]) -> Dict:
        """تحليل نتيجة اللعبة"""
        
        mafia_players = [p for p in players if p.role == PlayerRole.MAFIA]
        citizen_players = [p for p in players if p.role != PlayerRole.MAFIA]
        
        return {
            'winner': game.winner.value if game.winner else 'unknown',
            'mafia_count': len(mafia_players),
            'citizen_count': len(citizen_players),
            'survivors': len([p for p in players if p.is_alive]),
            'game_balance': self._evaluate_game_balance(mafia_players, citizen_players)
        }
    
    def _calculate_phase_balance(self, phase_stats: Dict) -> str:
        """حساب توازن المراحل"""
        
        day_msgs = phase_stats['day']['messages']
        night_msgs = phase_stats['night']['messages']
        voting_msgs = phase_stats['voting']['messages']
        
        total = day_msgs + night_msgs + voting_msgs
        
        if total == 0:
            return 'no_activity'
        
        day_ratio = day_msgs / total
        
        if day_ratio > 0.7:
            return 'day_heavy'
        elif day_ratio < 0.3:
            return 'night_heavy'
        else:
            return 'balanced'
    
    def _evaluate_game_balance(self, mafia_players: List[Player], citizen_players: List[Player]) -> str:
        """تقييم توازن اللعبة"""
        
        mafia_count = len(mafia_players)
        citizen_count = len(citizen_players)
        total = mafia_count + citizen_count
        
        if total == 0:
            return 'unknown'
        
        mafia_ratio = mafia_count / total
        
        if 0.2 <= mafia_ratio <= 0.35:
            return 'balanced'
        elif mafia_ratio < 0.2:
            return 'citizen_favored'
        else:
            return 'mafia_favored'
    
    def _rate_game_quality(self, phase_analysis: Dict, interaction_analysis: Dict) -> str:
        """تقييم جودة اللعبة"""
        
        score = 0
        
        # نقاط المشاركة
        if interaction_analysis['participation_rate'] > 0.8:
            score += 2
        elif interaction_analysis['participation_rate'] > 0.6:
            score += 1
        
        # نقاط التوازن
        if phase_analysis['phase_balance'] == 'balanced':
            score += 2
        elif phase_analysis['phase_balance'] in ['day_heavy', 'night_heavy']:
            score += 1
        
        # نقاط الجولات
        if phase_analysis['total_rounds'] >= 3:
            score += 1
        
        # تحديد الجودة
        if score >= 4:
            return 'excellent'
        elif score >= 2:
            return 'good'
        elif score >= 1:
            return 'fair'
        else:
            return 'poor'