#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محلل الإحصائيات بالذكاء الاصطناعي
AI Statistics Analyzer
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from models import Game, Player, Message, User
from models.statistics import UserStatistics
from models.player import PlayerRole

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class StatsAnalyzer:
    """محلل الإحصائيات للحصول على تقارير ذكية"""
    
    def __init__(self, openai_api_key: str = None):
        """إنشاء محلل الإحصائيات"""
        self.openai_available = OPENAI_AVAILABLE and openai_api_key
        
        if self.openai_available:
            try:
                if hasattr(openai, 'OpenAI'):
                    self.client = openai.OpenAI(api_key=openai_api_key)
                else:
                    openai.api_key = openai_api_key
                    self.client = openai
            except Exception as e:
                print(f"⚠️ فشل في تهيئة OpenAI للإحصائيات: {e}")
                self.openai_available = False
    
    def generate_player_report(self, user_id: int) -> Dict:
        """إنشاء تقرير شامل للاعب"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'المستخدم غير موجود'}
            
            stats = UserStatistics.query.filter_by(user_id=user_id).first()
            if not stats:
                return {'error': 'لا توجد إحصائيات للمستخدم'}
            
            # جمع البيانات
            recent_games = self._get_recent_games(user_id, limit=10)
            performance_trends = self._analyze_performance_trends(user_id)
            role_analysis = self._analyze_role_performance(stats)
            behavioral_analysis = self._analyze_player_behavior(user_id)
            
            # إنشاء التقرير بالذكاء الاصطناعي
            ai_insights = self._generate_ai_insights(user, stats, recent_games, performance_trends)
            
            return {
                'user_id': user_id,
                'username': user.username,
                'display_name': user.display_name,
                'report_date': datetime.utcnow().isoformat(),
                'basic_stats': stats.to_dict(detailed=True),
                'recent_games': recent_games,
                'performance_trends': performance_trends,
                'role_analysis': role_analysis,
                'behavioral_analysis': behavioral_analysis,
                'ai_insights': ai_insights,
                'recommendations': self._generate_recommendations(stats, performance_trends, behavioral_analysis)
            }
            
        except Exception as e:
            return {'error': f'خطأ في إنشاء التقرير: {str(e)}'}
    
    def _get_recent_games(self, user_id: int, limit: int = 10) -> List[Dict]:
        """الحصول على الألعاب الأخيرة"""
        
        # البحث عن الألعاب التي شارك فيها المستخدم
        from sqlalchemy import desc
        from models import db
        
        games = db.session.query(Game).join(
            Player, Game.room_id == Player.room_id
        ).filter(
            Player.user_id == user_id
        ).order_by(desc(Game.started_at)).limit(limit).all()
        
        recent_games = []
        for game in games:
            player = Player.query.filter_by(
                user_id=user_id,
                room_id=game.room_id
            ).first()
            
            if player:
                game_data = {
                    'game_id': game.id,
                    'started_at': game.started_at.isoformat(),
                    'ended_at': game.ended_at.isoformat() if game.ended_at else None,
                    'duration': game.get_duration() if hasattr(game, 'get_duration') else 0,
                    'total_players': game.total_players,
                    'winner': game.winner.value if game.winner else None,
                    'player_role': player.role.value if player.role else None,
                    'player_survived': player.is_alive,
                    'player_won': self._did_player_win(player, game.winner)
                }
                recent_games.append(game_data)
        
        return recent_games
    
    def _did_player_win(self, player: Player, game_winner) -> Optional[bool]:
        """تحديد ما إذا كان اللاعب فاز"""
        if not game_winner:
            return None
        
        from models.game import WinCondition
        
        if game_winner == WinCondition.MAFIA_WIN:
            return player.role == PlayerRole.MAFIA
        elif game_winner == WinCondition.CITIZENS_WIN:
            return player.role != PlayerRole.MAFIA
        elif game_winner == WinCondition.DRAW:
            return None
        
        return False
    
    def _analyze_performance_trends(self, user_id: int) -> Dict:
        """تحليل اتجاهات الأداء"""
        
        # الحصول على الألعاب الأخيرة مع تواريخها
        recent_games = self._get_recent_games(user_id, limit=20)
        
        if len(recent_games) < 5:
            return {
                'trend': 'insufficient_data',
                'win_rate_trend': 'stable',
                'recent_performance': 'unknown'
            }
        
        # تقسيم الألعاب إلى فترات
        first_half = recent_games[len(recent_games)//2:]
        second_half = recent_games[:len(recent_games)//2]
        
        # حساب معدل الفوز لكل فترة
        first_wins = sum(1 for game in first_half if game['player_won'])
        second_wins = sum(1 for game in second_half if game['player_won'])
        
        first_rate = first_wins / len(first_half) if first_half else 0
        second_rate = second_wins / len(second_half) if second_half else 0
        
        # تحديد الاتجاه
        if second_rate > first_rate + 0.1:
            trend = 'improving'
        elif second_rate < first_rate - 0.1:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # تحليل الأداء الأخير (آخر 5 ألعاب)
        last_5 = recent_games[:5]
        recent_wins = sum(1 for game in last_5 if game['player_won'])
        recent_performance = recent_wins / len(last_5) if last_5 else 0
        
        return {
            'trend': trend,
            'win_rate_trend': trend,
            'first_period_win_rate': round(first_rate, 2),
            'second_period_win_rate': round(second_rate, 2),
            'recent_performance': round(recent_performance, 2),
            'games_analyzed': len(recent_games)
        }
    
    def _analyze_role_performance(self, stats: UserStatistics) -> Dict:
        """تحليل أداء الأدوار"""
        
        roles = ['citizen', 'mafia', 'doctor', 'detective', 'vigilante', 'mayor', 'jester']
        role_performance = {}
        
        for role in roles:
            games_attr = f"games_as_{role}"
            wins_attr = f"wins_as_{role}"
            
            games = getattr(stats, games_attr, 0)
            wins = getattr(stats, wins_attr, 0)
            
            if games > 0:
                win_rate = wins / games
                
                # تقييم الأداء
                if win_rate >= 0.7:
                    performance = 'excellent'
                elif win_rate >= 0.5:
                    performance = 'good'
                elif win_rate >= 0.3:
                    performance = 'average'
                else:
                    performance = 'needs_improvement'
                
                role_performance[role] = {
                    'games': games,
                    'wins': wins,
                    'win_rate': round(win_rate, 2),
                    'performance': performance
                }
        
        # تحديد أفضل وأسوأ الأدوار
        if role_performance:
            best_role = max(role_performance.items(), key=lambda x: x[1]['win_rate'])
            worst_role = min(role_performance.items(), key=lambda x: x[1]['win_rate'])
            
            return {
                'role_stats': role_performance,
                'best_role': {
                    'role': best_role[0],
                    'win_rate': best_role[1]['win_rate']
                },
                'worst_role': {
                    'role': worst_role[0],
                    'win_rate': worst_role[1]['win_rate']
                },
                'most_played': stats.get_favorite_role()
            }
        
        return {'role_stats': {}, 'insufficient_data': True}
    
    def _analyze_player_behavior(self, user_id: int) -> Dict:
        """تحليل سلوك اللاعب"""
        
        # الحصول على الرسائل الأخيرة
        recent_messages = Message.query.filter_by(
            user_id=user_id
        ).order_by(Message.sent_at.desc()).limit(100).all()
        
        if not recent_messages:
            return {
                'communication_style': 'unknown',
                'activity_level': 'unknown',
                'behavior_score': 0.0
            }
        
        # تحليل نمط التواصل
        total_length = sum(len(msg.content) for msg in recent_messages)
        avg_length = total_length / len(recent_messages)
        
        # تحليل مستوى النشاط
        last_week = datetime.utcnow() - timedelta(days=7)
        recent_count = sum(1 for msg in recent_messages if msg.sent_at >= last_week)
        
        # تحليل السلوك المشبوه
        flagged_count = sum(1 for msg in recent_messages if msg.is_flagged)
        suspicious_ratio = flagged_count / len(recent_messages)
        
        # تحديد نمط التواصل
        if avg_length > 100:
            communication_style = 'verbose'
        elif avg_length > 50:
            communication_style = 'detailed'
        elif avg_length > 20:
            communication_style = 'normal'
        else:
            communication_style = 'brief'
        
        # تحديد مستوى النشاط
        if recent_count > 50:
            activity_level = 'very_active'
        elif recent_count > 20:
            activity_level = 'active'
        elif recent_count > 5:
            activity_level = 'moderate'
        else:
            activity_level = 'inactive'
        
        # حساب نقاط السلوك
        behavior_score = 1.0 - (suspicious_ratio * 2)  # خصم نقاط للسلوك المشبوه
        behavior_score = max(0.0, min(1.0, behavior_score))
        
        return {
            'communication_style': communication_style,
            'activity_level': activity_level,
            'average_message_length': round(avg_length, 1),
            'recent_messages_count': recent_count,
            'flagged_messages_ratio': round(suspicious_ratio, 3),
            'behavior_score': round(behavior_score, 2)
        }
    
    def _generate_ai_insights(self, user: User, stats: UserStatistics, 
                            recent_games: List[Dict], performance_trends: Dict) -> Dict:
        """إنشاء تحليلات ذكية بالذكاء الاصطناعي"""
        
        try:
            # إعداد البيانات للذكاء الاصطناعي
            data_summary = {
                'total_games': stats.total_games_played,
                'win_rate': stats.get_win_rate(),
                'favorite_role': stats.get_favorite_role(),
                'recent_trend': performance_trends.get('trend', 'stable'),
                'survival_rate': stats.get_survival_rate()
            }
            
            prompt = f"""
            أنت محلل خبير في لعبة المافيا. قم بتحليل أداء اللاعب التالي وإعطاء نصائح:

            اسم اللاعب: {user.display_name}
            إجمالي الألعاب: {data_summary['total_games']}
            معدل الفوز: {data_summary['win_rate']:.1f}%
            الدور المفضل: {data_summary['favorite_role']}
            الاتجاه الأخير: {data_summary['recent_trend']}
            معدل البقاء: {data_summary['survival_rate']:.1f}%

            قم بتحليل نقاط القوة والضعف، وقدم نصائح للتحسين باللغة العربية.
            اجعل التحليل مفيداً وإيجابياً ومحفزاً.

            أجب بـ JSON:
            {{
                "strengths": ["نقطة قوة 1", "نقطة قوة 2"],
                "weaknesses": ["نقطة ضعف 1", "نقطة ضعف 2"],
                "improvement_tips": ["نصيحة 1", "نصيحة 2"],
                "overall_assessment": "تقييم عام",
                "next_focus": "ما يجب التركيز عليه"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "أنت مدرب محترف للعبة المافيا باللغة العربية."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {
                    'strengths': ['يشارك في الألعاب بانتظام'],
                    'weaknesses': ['يحتاج لمزيد من التحسن'],
                    'improvement_tips': ['مارس أكثر', 'تفاعل مع اللاعبين'],
                    'overall_assessment': 'لاعب في طور التطوير',
                    'next_focus': 'تحسين استراتيجيات اللعب'
                }
                
        except Exception as e:
            print(f"خطأ في تحليل الذكاء الاصطناعي: {e}")
            return {
                'error': 'فشل في التحليل الذكي',
                'fallback_assessment': 'يحتاج لمزيد من البيانات للتحليل'
            }
    
    def _generate_recommendations(self, stats: UserStatistics, 
                                performance_trends: Dict, behavioral_analysis: Dict) -> List[str]:
        """إنشاء توصيات للتحسين"""
        
        recommendations = []
        
        # توصيات حسب معدل الفوز
        win_rate = stats.get_win_rate()
        if win_rate < 30:
            recommendations.append("🎯 ركز على تعلم استراتيجيات أساسية جديدة")
            recommendations.append("📚 اقرأ أدلة اللعبة وتعلم من اللاعبين المتقدمين")
        elif win_rate < 50:
            recommendations.append("⚡ جرب تحسين مهارات التحليل والاستنتاج")
            recommendations.append("🗣️ شارك أكثر في النقاشات لفهم اللاعبين")
        
        # توصيات حسب الاتجاه
        trend = performance_trends.get('trend', 'stable')
        if trend == 'declining':
            recommendations.append("📈 راجع ألعابك الأخيرة وتعلم من الأخطاء")
            recommendations.append("🔄 جرب استراتيجيات جديدة")
        elif trend == 'improving':
            recommendations.append("🚀 استمر على نفس النهج، أداؤك يتحسن!")
            recommendations.append("🎖️ تحدى نفسك في أدوار أكثر صعوبة")
        
        # توصيات حسب السلوك
        activity = behavioral_analysis.get('activity_level', 'unknown')
        if activity == 'inactive':
            recommendations.append("💬 شارك أكثر في المحادثات أثناء اللعب")
        elif activity == 'very_active':
            recommendations.append("⚖️ حافظ على توازن بين الكلام والاستماع")
        
        # توصيات حسب الأدوار
        favorite_role = stats.get_favorite_role()
        if favorite_role == 'citizen':
            recommendations.append("🕵️ جرب الأدوار الخاصة لتطوير مهارات جديدة")
        elif favorite_role == 'mafia':
            recommendations.append("😇 العب كمواطن أكثر لفهم منظورهم")
        
        # إضافة توصيات عامة إذا لم تكن هناك توصيات كافية
        if len(recommendations) < 3:
            recommendations.extend([
                "🤝 تفاعل مع اللاعبين الآخرين وكون علاقات",
                "🧠 طور مهارات القراءة النفسية للاعبين",
                "⏰ اختر التوقيت المناسب لأعمالك"
            ])
        
        return recommendations[:5]  # أقصى 5 توصيات
    
    def analyze_game(self, game_id: int) -> Dict:
        """تحليل لعبة محددة"""
        try:
            game = Game.query.get(game_id)
            if not game:
                return {'error': 'اللعبة غير موجودة'}
            
            # استخدام GameAnalyzer للتحليل المفصل
            from .game_analyzer import GameAnalyzer
            game_analyzer = GameAnalyzer(self.client.api_key)
            
            return game_analyzer.analyze_game_flow(game_id)
            
        except Exception as e:
            return {'error': f'خطأ في تحليل اللعبة: {str(e)}'}
    
    def get_platform_insights(self) -> Dict:
        """الحصول على إحصائيات عامة للمنصة"""
        try:
            # إحصائيات المستخدمين
            total_users = User.query.filter_by(is_active=True).count()
            active_users = User.query.filter_by(is_active=True, is_online=True).count()
            
            # إحصائيات الألعاب
            total_games = Game.query.count()
            completed_games = Game.query.filter(Game.ended_at.isnot(None)).count()
            
            # تحليل الأدوار الشائعة
            from sqlalchemy import func
            role_stats = db.session.query(
                func.sum(UserStatistics.games_as_citizen).label('citizen'),
                func.sum(UserStatistics.games_as_mafia).label('mafia'),
                func.sum(UserStatistics.games_as_doctor).label('doctor'),
                func.sum(UserStatistics.games_as_detective).label('detective'),
                func.sum(UserStatistics.games_as_vigilante).label('vigilante'),
                func.sum(UserStatistics.games_as_mayor).label('mayor'),
                func.sum(UserStatistics.games_as_jester).label('jester')
            ).first()
            
            # حساب معدلات الفوز العامة
            avg_stats = db.session.query(
                func.avg(UserStatistics.games_won * 100.0 / UserStatistics.total_games_played).label('avg_win_rate'),
                func.avg(UserStatistics.times_survived * 100.0 / UserStatistics.total_games_played).label('avg_survival_rate')
            ).filter(UserStatistics.total_games_played > 0).first()
            
            return {
                'platform': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'total_games': total_games,
                    'completed_games': completed_games
                },
                'role_distribution': {
                    'citizen': int(role_stats.citizen or 0),
                    'mafia': int(role_stats.mafia or 0),
                    'doctor': int(role_stats.doctor or 0),
                    'detective': int(role_stats.detective or 0),
                    'vigilante': int(role_stats.vigilante or 0),
                    'mayor': int(role_stats.mayor or 0),
                    'jester': int(role_stats.jester or 0)
                },
                'averages': {
                    'win_rate': round(float(avg_stats.avg_win_rate or 0), 2),
                    'survival_rate': round(float(avg_stats.avg_survival_rate or 0), 2)
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': f'خطأ في تحليل المنصة: {str(e)}'}

# إضافة في النهاية
from models import db