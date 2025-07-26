#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات الإحصائيات
Statistics Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, User, Game, Player
from models.statistics import UserStatistics
from sqlalchemy import func, desc

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/my-stats', methods=['GET'])
@login_required
def get_my_statistics():
    """الحصول على إحصائياتي"""
    try:
        # الحصول على الإحصائيات المفصلة
        stats = UserStatistics.query.filter_by(user_id=current_user.id).first()
        
        if not stats:
            # إنشاء إحصائيات جديدة إذا لم تكن موجودة
            stats = UserStatistics(user_id=current_user.id)
            db.session.add(stats)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'statistics': stats.to_dict(detailed=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في الحصول على الإحصائيات: {str(e)}'
        }), 500

@stats_bp.route('/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_statistics(user_id):
    """الحصول على إحصائيات مستخدم معين"""
    try:
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            }), 404
        
        stats = UserStatistics.query.filter_by(user_id=user_id).first()
        
        if not stats:
            return jsonify({
                'success': True,
                'statistics': {
                    'user_id': user_id,
                    'total_games_played': 0,
                    'message': 'لم يلعب هذا المستخدم أي لعبة بعد'
                }
            })
        
        # إحصائيات عامة فقط (ليس التفاصيل الخاصة)
        return jsonify({
            'success': True,
            'statistics': stats.to_dict(detailed=False)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@stats_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """الحصول على لوحة المتصدرين"""
    try:
        # نوع الترتيب
        sort_by = request.args.get('sort', 'win_rate')  # win_rate, total_games, games_won
        limit = min(int(request.args.get('limit', 50)), 100)
        
        # بناء الاستعلام
        query = db.session.query(
            UserStatistics,
            User.username,
            User.display_name,
            User.avatar_url
        ).join(User, UserStatistics.user_id == User.id).filter(
            User.is_active == True,
            UserStatistics.total_games_played > 0
        )
        
        # ترتيب حسب النوع المطلوب
        if sort_by == 'win_rate':
            # ترتيب حسب معدل الفوز (مع الحد الأدنى من الألعاب)
            query = query.filter(UserStatistics.total_games_played >= 5).order_by(
                desc(UserStatistics.games_won * 100.0 / UserStatistics.total_games_played),
                desc(UserStatistics.total_games_played)
            )
        elif sort_by == 'total_games':
            query = query.order_by(desc(UserStatistics.total_games_played))
        elif sort_by == 'games_won':
            query = query.order_by(desc(UserStatistics.games_won))
        else:
            query = query.order_by(desc(UserStatistics.total_games_played))
        
        results = query.limit(limit).all()
        
        # تنسيق النتائج
        leaderboard = []
        for rank, (stats, username, display_name, avatar_url) in enumerate(results, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': stats.user_id,
                'username': username,
                'display_name': display_name,
                'avatar_url': avatar_url,
                'total_games': stats.total_games_played,
                'games_won': stats.games_won,
                'win_rate': stats.get_win_rate(),
                'survival_rate': stats.get_survival_rate(),
                'favorite_role': stats.get_favorite_role()
            })
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard,
            'sort_by': sort_by,
            'count': len(leaderboard)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@stats_bp.route('/global', methods=['GET'])
def get_global_statistics():
    """الحصول على الإحصائيات العامة للموقع"""
    try:
        # إحصائيات المستخدمين
        total_users = User.query.filter_by(is_active=True).count()
        online_users = User.query.filter_by(is_active=True, is_online=True).count()
        
        # إحصائيات الألعاب
        total_games = Game.query.count()
        active_games = current_app.game_manager.get_active_games_count()
        
        # إحصائيات الغرف
        active_rooms = current_app.room_manager.get_active_rooms_count()
        total_players_in_rooms = current_app.room_manager.get_total_players_count()
        
        # إحصائيات متقدمة
        stats_query = db.session.query(
            func.sum(UserStatistics.total_games_played).label('total_games_played'),
            func.avg(UserStatistics.total_games_played).label('avg_games_per_user'),
            func.sum(UserStatistics.total_messages_sent).label('total_messages'),
            func.avg(UserStatistics.average_suspicion_score).label('avg_suspicion_score')
        ).first()
        
        # الأدوار الأكثر لعباً
        popular_roles = db.session.query(
            func.sum(UserStatistics.games_as_citizen).label('citizen'),
            func.sum(UserStatistics.games_as_mafia).label('mafia'),
            func.sum(UserStatistics.games_as_doctor).label('doctor'),
            func.sum(UserStatistics.games_as_detective).label('detective'),
            func.sum(UserStatistics.games_as_vigilante).label('vigilante'),
            func.sum(UserStatistics.games_as_mayor).label('mayor'),
            func.sum(UserStatistics.games_as_jester).label('jester')
        ).first()
        
        return jsonify({
            'success': True,
            'statistics': {
                'users': {
                    'total': total_users,
                    'online': online_users,
                    'offline': total_users - online_users
                },
                'games': {
                    'total_completed': total_games,
                    'currently_active': active_games,
                    'total_games_played': int(stats_query.total_games_played or 0),
                    'average_per_user': round(float(stats_query.avg_games_per_user or 0), 2)
                },
                'rooms': {
                    'active_rooms': active_rooms,
                    'players_in_rooms': total_players_in_rooms
                },
                'chat': {
                    'total_messages': int(stats_query.total_messages or 0),
                    'average_suspicion': round(float(stats_query.avg_suspicion_score or 0), 3)
                },
                'roles': {
                    'citizen': int(popular_roles.citizen or 0),
                    'mafia': int(popular_roles.mafia or 0),
                    'doctor': int(popular_roles.doctor or 0),
                    'detective': int(popular_roles.detective or 0),
                    'vigilante': int(popular_roles.vigilante or 0),
                    'mayor': int(popular_roles.mayor or 0),
                    'jester': int(popular_roles.jester or 0)
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@stats_bp.route('/analyze-game/<int:game_id>', methods=['GET'])
@login_required
def analyze_game(game_id):
    """تحليل لعبة معينة"""
    try:
        # التأكد من وجود اللعبة
        game = Game.query.get(game_id)
        if not game:
            return jsonify({
                'success': False,
                'message': 'اللعبة غير موجودة'
            }), 404
        
        # التأكد من مشاركة المستخدم في اللعبة
        player = Player.query.filter_by(
            user_id=current_user.id,
            room_id=game.room_id
        ).first()
        
        if not player:
            return jsonify({
                'success': False,
                'message': 'لم تشارك في هذه اللعبة'
            }), 403
        
        # تحليل اللعبة باستخدام الذكاء الاصطناعي
        analyzer = current_app.stats_analyzer
        analysis = analyzer.analyze_game(game_id)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في التحليل: {str(e)}'
        }), 500

@stats_bp.route('/my-games', methods=['GET'])
@login_required
def get_my_games():
    """الحصول على ألعابي"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        
        # الحصول على الألعاب التي شارك فيها المستخدم
        games_query = db.session.query(Game).join(
            Player, Game.room_id == Player.room_id
        ).filter(
            Player.user_id == current_user.id
        ).order_by(desc(Game.started_at))
        
        # تطبيق التصفح
        total = games_query.count()
        games = games_query.offset((page - 1) * per_page).limit(per_page).all()
        
        # تنسيق النتائج
        games_data = []
        for game in games:
            # الحصول على معلومات اللاعب في هذه اللعبة
            player = Player.query.filter_by(
                user_id=current_user.id,
                room_id=game.room_id
            ).first()
            
            games_data.append({
                'game': game.to_dict(),
                'player': player.to_dict(include_role=True) if player else None
            })
        
        return jsonify({
            'success': True,
            'games': games_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500