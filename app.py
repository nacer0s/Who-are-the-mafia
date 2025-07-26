#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تطبيق لعبة المافيا الرئيسي
Main Mafia Game Application
"""

from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_cors import CORS
import os
from datetime import timedelta

# استيراد الإعدادات
from config import config

# استيراد النماذج
from models import db, User

# استيراد المدراء
from game import GameManager, RoomManager

# استيراد مسارات API
from api import auth_bp, game_bp, room_bp, stats_bp

# استيراد أحداث WebSocket
from websocket import register_game_events, register_room_events, register_chat_events, register_voice_events

# استيراد الذكاء الاصطناعي
from ai import MessageAnalyzer, SpeechToText, GameAnalyzer, StatsAnalyzer

# استيراد مسارات الواجهات
from routes import register_routes

def create_app(config_name='development'):
    """إنشاء تطبيق Flask"""
    
    app = Flask(__name__)
    
    # تحميل الإعدادات  
    app.config.from_object(config[config_name])
    
    # تهيئة الإضافات
    db.init_app(app)
    
    # إعداد CORS
    CORS(app, 
         origins=["http://localhost:3000"],  # للواجهة الأمامية المستقبلية
         supports_credentials=True)
    
    # إعداد SocketIO
    socketio = SocketIO(app, 
                       cors_allowed_origins="*",
                       async_mode='threading',
                       logger=True,
                       engineio_logger=True)
    
    # إعداد إدارة تسجيل الدخول
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # إعداد مدة الجلسة
    app.permanent_session_lifetime = timedelta(days=7)
    
    # إنشاء قاعدة البيانات
    with app.app_context():
        db.create_all()
        print("✅ تم إنشاء قاعدة البيانات بنجاح")
    
    # تسجيل مسارات API
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(game_bp, url_prefix='/api/game')
    app.register_blueprint(room_bp, url_prefix='/api/room')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    
    # تسجيل مسارات الواجهات
    register_routes(app)
    
    # إنشاء مدراء اللعبة
    app.game_manager = GameManager()
    app.room_manager = RoomManager()
    
    # إعداد الذكاء الاصطناعي
    openai_api_key = app.config.get('OPENAI_API_KEY')
    if openai_api_key:
        app.ai_analyzer = MessageAnalyzer(openai_api_key)
        app.speech_to_text = SpeechToText(openai_api_key)
        app.game_analyzer = GameAnalyzer(openai_api_key)
        app.stats_analyzer = StatsAnalyzer(openai_api_key)
        print("✅ تم تهيئة محركات الذكاء الاصطناعي")
    else:
        print("⚠️ لم يتم تعيين مفتاح OpenAI - الذكاء الاصطناعي معطل")
    
    # تسجيل أحداث WebSocket
    register_game_events(socketio)
    register_room_events(socketio)
    register_chat_events(socketio)
    register_voice_events(socketio)
    
    # إعداد أحداث الاتصال
    @socketio.on('connect')
    def handle_connect(auth):
        print(f"🔗 اتصال جديد من العميل")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f"❌ انقطع الاتصال مع العميل")
    
    # المسارات يتم تسجيلها من routes.py
    


    
    # معالج الأخطاء
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'المورد غير موجود'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'خطأ داخلي في الخادم'}, 500
    
    # إرجاع التطبيق و SocketIO
    return app, socketio

def setup_development_data(app):
    """إعداد بيانات التطوير"""
    with app.app_context():
        # إنشاء مستخدم تجريبي
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                display_name='المدير',
                email='admin@mafia.game'
            )
            admin_user.set_password('admin123')
            admin_user.is_admin = True
            db.session.add(admin_user)
        
        # إنشاء مستخدمين تجريبيين
        test_users = [
            ('player1', 'اللاعب الأول', 'player1@test.com'),
            ('player2', 'اللاعب الثاني', 'player2@test.com'),
            ('player3', 'اللاعب الثالث', 'player3@test.com'),
            ('player4', 'اللاعب الرابع', 'player4@test.com'),
        ]
        
        for username, display_name, email in test_users:
            existing_user = User.query.filter_by(username=username).first()
            if not existing_user:
                test_user = User(
                    username=username,
                    display_name=display_name,
                    email=email
                )
                test_user.set_password('test123')
                db.session.add(test_user)
        
        db.session.commit()
        print("✅ تم إنشاء بيانات التطوير")

def run_cleanup_tasks(app):
    """تشغيل مهام التنظيف الدورية"""
    import threading
    import time
    
    def cleanup_worker():
        while True:
            try:
                with app.app_context():
                    # تنظيف الألعاب المنتهية
                    cleaned_games = app.game_manager.cleanup_finished_games()
                    if cleaned_games > 0:
                        print(f"🧹 تم تنظيف {cleaned_games} لعبة منتهية")
                    
                    # تنظيف الملفات الصوتية القديمة
                    from websocket.voice_events import cleanup_old_voice_files
                    cleanup_old_voice_files()
                    
            except Exception as e:
                print(f"❌ خطأ في مهمة التنظيف: {e}")
            
            # انتظار ساعة
            time.sleep(3600)
    
    # تشغيل مهمة التنظيف في خيط منفصل
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    print("🧹 تم بدء مهام التنظيف الدورية")

if __name__ == '__main__':
    # إنشاء التطبيق
    app, socketio = create_app('development')
    
    # إعداد بيانات التطوير
    if app.config['DEBUG']:
        setup_development_data(app)
    
    # تشغيل مهام التنظيف
    run_cleanup_tasks(app)
    
    print("🎮 بدء تشغيل خادم لعبة المافيا...")
    print(f"🌐 الخادم يعمل على: http://{app.config['HOST']}:{app.config['PORT']}")
    print(f"🔧 وضع التطوير: {'مفعل' if app.config['DEBUG'] else 'معطل'}")
    print(f"🤖 الذكاء الاصطناعي: {'مفعل' if app.config.get('OPENAI_API_KEY') else 'معطل'}")
    print("📝 لمشاهدة API: /api/info")
    print("💚 للتحقق من الصحة: /health")
    print("-" * 50)
    
    # تشغيل الخادم
    socketio.run(
        app,
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        allow_unsafe_werkzeug=True  # للتطوير فقط
    )