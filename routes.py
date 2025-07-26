#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات الواجهات الأمامية
Frontend Routes
"""

from flask import render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, current_user, logout_user
from models import db, User, Room, Game, Player, Message
from models.room import RoomStatus
from models.game import GameStatus
from models.statistics import UserStatistics
from game import RoomManager, GameManager
from ai import StatsAnalyzer
import datetime

def register_routes(app):
    """تسجيل جميع المسارات"""
    
    @app.route('/')
    def index():
        """الصفحة الرئيسية"""
        # إحصائيات عامة للعرض
        stats = {
            'total_users': User.query.count(),
            'total_games': Game.query.filter(Game.status == GameStatus.FINISHED).count(),
            'active_rooms': Room.query.filter(Room.status == RoomStatus.WAITING).count(),
            'online_users': User.query.filter(
                User.last_seen > datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
            ).count()
        }
        
        return render_template('index.html', stats=stats)
    
    @app.route('/login', methods=['GET'])
    def login():
        """صفحة تسجيل الدخول"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('auth/login.html')
    
    @app.route('/register', methods=['GET'])
    def register():
        """صفحة التسجيل"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('auth/register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """تسجيل الخروج"""
        logout_user()
        flash('تم تسجيل الخروج بنجاح', 'success')
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """لوحة تحكم اللاعب"""
        # إحصائيات المستخدم
        user_stats = UserStatistics.query.filter_by(user_id=current_user.id).first()
        if not user_stats:
            user_stats = UserStatistics(user_id=current_user.id)
            db.session.add(user_stats)
            db.session.commit()
        
        # الأنشطة الحديثة (يمكن تطويرها لاحقاً)
        recent_activities = []
        
        # الغرف المتاحة (الغرف العامة هي التي لا تحتوي على كلمة مرور)
        available_rooms = Room.query.filter(
            Room.status == RoomStatus.WAITING,
            Room.password.is_(None)
        ).limit(5).all()
        
        # الألعاب الحديثة - البحث عن الألعاب في الغرف التي شارك فيها اللاعب
        user_rooms = db.session.query(Player.room_id).filter(
            Player.user_id == current_user.id
        ).distinct().subquery()
        
        recent_games = Game.query.filter(
            Game.room_id.in_(user_rooms),
            Game.status == GameStatus.FINISHED
        ).order_by(Game.finished_at.desc()).limit(5).all()
        
        # الإشعارات غير المقروءة (يمكن تطويرها لاحقاً)
        unread_notifications = 0
        
        # نصيحة اليوم
        daily_tip = {
            'title': 'استخدم الذكاء الاصطناعي',
            'content': 'يمكن للذكاء الاصطناعي في اللعبة كشف محاولات الغش وتحليل أنماط اللعب. راقب مؤشر الشك للاعبين الآخرين!'
        }
        
        return render_template('dashboard.html',
                             user_stats=user_stats,
                             recent_activities=recent_activities,
                             available_rooms=available_rooms,
                             recent_games=recent_games,
                             unread_notifications=unread_notifications,
                             daily_tip=daily_tip)
    
    @app.route('/rooms')
    @login_required
    def rooms():
        """صفحة الغرف"""
        return render_template('rooms.html')
    
    @app.route('/create-room')
    @login_required
    def create_room():
        """إنشاء غرفة جديدة"""
        return render_template('create_room.html')
    
    @app.route('/join-room/<room_code>')
    @login_required
    def join_room(room_code):
        """الانضمام إلى غرفة"""
        room = Room.query.filter_by(room_code=room_code).first_or_404()
        
        # محاولة إضافة اللاعب للغرفة
        success, message = room.add_player(current_user.id)
        
        if success:
            flash(f'تم الانضمام إلى غرفة {room.name} بنجاح', 'success')
            return redirect(url_for('game', room_code=room_code))
        else:
            flash(message, 'error')
            return redirect(url_for('rooms'))
    
    @app.route('/game/<room_code>')
    @login_required
    def game(room_code):
        """صفحة اللعبة"""
        room = Room.query.filter_by(room_code=room_code).first_or_404()
        
        # التحقق من أن المستخدم في الغرفة
        player = Player.query.filter_by(
            room_id=room.id,
            user_id=current_user.id
        ).first()
        
        if not player:
            flash('لست عضواً في هذه الغرفة', 'error')
            return redirect(url_for('rooms'))
        
        return render_template('game.html', room=room, player=player)
    
    @app.route('/profile')
    @login_required
    def profile():
        """الملف الشخصي"""
        return render_template('profile.html')
    
    @app.route('/stats')
    @login_required
    def stats():
        """صفحة الإحصائيات العامة"""
        return render_template('stats.html')
    
    @app.route('/my-stats')
    @login_required
    def my_stats():
        """إحصائياتي المفصلة"""
        user_stats = UserStatistics.query.filter_by(user_id=current_user.id).first()
        if not user_stats:
            user_stats = UserStatistics(user_id=current_user.id)
            db.session.add(user_stats)
            db.session.commit()
        
        # تحليل ذكي للإحصائيات
        ai_analysis = None
        if app.config.get('OPENAI_API_KEY'):
            try:
                analyzer = StatsAnalyzer(app.config['OPENAI_API_KEY'])
                ai_analysis = analyzer.generate_player_report(current_user.id)
            except Exception as e:
                print(f"خطأ في تحليل الإحصائيات: {e}")
        
        return render_template('my_stats.html', 
                             user_stats=user_stats,
                             ai_analysis=ai_analysis)
    
    @app.route('/admin')
    @login_required
    def admin():
        """لوحة الإدارة"""
        if not current_user.is_admin:
            flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
            return redirect(url_for('dashboard'))
        
        return render_template('admin/dashboard.html')
    
    @app.route('/rules')
    def rules():
        """قوانين اللعبة"""
        return render_template('rules.html')
    
    @app.route('/help')
    def help():
        """صفحة المساعدة"""
        return render_template('help.html')
    
    @app.route('/friends')
    @login_required
    def friends():
        """صفحة الأصدقاء"""
        return render_template('friends.html')
    
    @app.route('/notifications')
    @login_required
    def notifications():
        """صفحة الإشعارات"""
        return render_template('notifications.html')
    
    @app.route('/terms')
    def terms():
        """شروط الاستخدام"""
        return render_template('legal/terms.html')
    
    @app.route('/privacy')
    def privacy():
        """سياسة الخصوصية"""
        return render_template('legal/privacy.html')
    
    @app.route('/api/info')
    def api_info():
        """معلومات API"""
        return jsonify({
            'api_version': '1.0.0',
            'game_name': 'لعبة المافيا',
            'status': 'active',
            'features': [
                'إدارة متعددة اللاعبين',
                'دردشة نصية وصوتية',
                'ذكاء اصطناعي للكشف عن الغش',
                'إحصائيات تفصيلية',
                'أدوار متنوعة'
            ],
            'ai_features': {
                'message_analysis': bool(app.config.get('OPENAI_API_KEY')),
                'speech_to_text': bool(app.config.get('OPENAI_API_KEY')),
                'game_analysis': bool(app.config.get('OPENAI_API_KEY')),
                'statistics_analysis': bool(app.config.get('OPENAI_API_KEY'))
            },
            'server_time': datetime.datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'message': 'مرحباً بك في لعبة المافيا!'
        })
    
    @app.route('/health')
    def health():
        """فحص صحة الطبيق"""
        try:
            # فحص قاعدة البيانات
            db.session.execute(db.text('SELECT 1'))
            db_status = 'healthy'
        except Exception:
            db_status = 'error'
        
        # إحصائيات سريعة
        active_games = Game.query.filter(Game.status == GameStatus.ACTIVE).count()
        active_rooms = Room.query.filter(Room.status == RoomStatus.WAITING).count()
        online_users = User.query.filter(
            User.last_seen > datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        ).count()
        
        health_data = {
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'database': db_status,
            'active_games': active_games,
            'active_rooms': active_rooms,
            'online_users': online_users,
            'ai_enabled': bool(app.config.get('OPENAI_API_KEY')),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code
    
    @app.route('/api/tips/random')
    @login_required
    def random_tip():
        """نصيحة عشوائية"""
        tips = [
            {
                'title': 'راقب مؤشر الشك',
                'content': 'مؤشر الشك يساعدك في تحديد اللاعبين المشبوهين بناءً على تحليل رسائلهم.'
            },
            {
                'title': 'استخدم الدردشة الصوتية',
                'content': 'الدردشة الصوتية تضيف بُعداً جديداً للعبة وتساعد في كشف الكذب من نبرة الصوت.'
            },
            {
                'title': 'انتبه للأنماط',
                'content': 'لاحظ أنماط سلوك اللاعبين - المافيا عادة ما تتجنب لفت الانتباه.'
            },
            {
                'title': 'تعاون مع فريقك',
                'content': 'إذا كنت مواطناً، تعاون مع الأدوار الخاصة مثل المحقق والطبيب.'
            },
            {
                'title': 'لا تكشف دورك مبكراً',
                'content': 'كشف دورك مبكراً قد يجعلك هدفاً سهلاً للمافيا.'
            }
        ]
        
        import random
        tip = random.choice(tips)
        
        return jsonify({
            'success': True,
            'tip': tip
        })
    
    @app.route('/api/dashboard/quick-stats')
    @login_required
    def dashboard_quick_stats():
        """إحصائيات سريعة للوحة التحكم"""
        user_stats = UserStatistics.query.filter_by(user_id=current_user.id).first()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_games': user_stats.total_games_played if user_stats else 0,
                'win_rate': user_stats.win_rate if user_stats else 0,
                'messages_sent': user_stats.total_messages_sent if user_stats else 0,
                'playtime_hours': user_stats.total_playtime_hours if user_stats else 0
            }
        })
    
    # معالجة الأخطاء
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    print("✅ تم تسجيل جميع المسارات بنجاح")