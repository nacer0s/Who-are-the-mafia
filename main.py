#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التطبيق الرئيسي للعبة المافيا
Main Application Runner
"""

import os
import sys
from datetime import datetime

def check_requirements():
    """التحقق من متطلبات التشغيل"""
    print("🔍 فحص متطلبات التشغيل...")
    
    # فحص إصدار Python
    if sys.version_info < (3, 8):
        print("❌ يتطلب Python 3.8 أو أحدث")
        return False
    
    # فحص ملف .env
    if not os.path.exists('.env'):
        print("⚠️ ملف .env غير موجود - سيتم استخدام الإعدادات الافتراضية")
    
    # فحص المتطلبات
    required_packages = [
        'flask', 'flask_socketio', 'flask_login', 
        'flask_cors', 'flask_sqlalchemy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ حزم مفقودة: {', '.join(missing_packages)}")
        print("💡 قم بتشغيل: pip install -r requirements.txt")
        return False
    
    print("✅ جميع المتطلبات متوفرة")
    return True

def setup_database():
    """إعداد قاعدة البيانات"""
    print("🗄️ إعداد قاعدة البيانات...")
    
    try:
        from setup_database import create_database, create_admin_user, create_test_users, verify_database
        
        # إنشاء قاعدة البيانات
        if create_database():
            print("✅ تم إنشاء قاعدة البيانات")
        
        # إنشاء المدير
        if create_admin_user():
            print("✅ تم إنشاء حساب المدير")
        
        # إنشاء مستخدمين تجريبيين
        if create_test_users():
            print("✅ تم إنشاء المستخدمين التجريبيين")
        
        # التحقق من النتيجة
        if verify_database():
            print("✅ قاعدة البيانات جاهزة")
            return True
        
    except Exception as e:
        print(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
        return False
    
    return True

def run_server():
    """تشغيل الخادم"""
    print("🚀 تشغيل خادم لعبة المافيا...")
    
    try:
        from app import create_app
        
        # إنشاء التطبيق
        app, socketio = create_app('development')
        
        # طباعة معلومات التشغيل
        print("\n" + "="*60)
        print("🎮 خادم لعبة المافيا جاهز!")
        print("="*60)
        print(f"🌐 الرابط المحلي: http://{app.config['HOST']}:{app.config['PORT']}")
        print(f"🔧 وضع التطوير: {'مفعل' if app.config['DEBUG'] else 'معطل'}")
        print(f"🤖 الذكاء الاصطناعي: {'مفعل' if app.config.get('OPENAI_API_KEY') else 'معطل'}")
        print(f"💾 قاعدة البيانات: {app.config.get('DATABASE_TYPE', 'sqlite').upper()}")
        print("\n📚 روابط مفيدة:")
        print(f"   • معلومات API: http://{app.config['HOST']}:{app.config['PORT']}/api/info")
        print(f"   • فحص الصحة: http://{app.config['HOST']}:{app.config['PORT']}/health")
        print("\n👤 حسابات تجريبية:")
        print("   • المدير: admin / admin123")
        print("   • اللاعبون: احمد، فاطمة، محمد، عائشة / test123")
        print("\n🎯 لإيقاف الخادم: اضغط Ctrl+C")
        print("="*60)
        
        # تشغيل الخادم
        socketio.run(
            app,
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'],
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل الخادم: {e}")
        return False
    
    return True

def main():
    """الدالة الرئيسية"""
    print("🎭 مرحباً بك في لعبة المافيا!")
    print(f"📅 تاريخ التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # التحقق من المتطلبات
    if not check_requirements():
        print("\n❌ فشل في التحقق من المتطلبات")
        input("اضغط Enter للخروج...")
        return
    
    # إعداد قاعدة البيانات
    try:
        if not setup_database():
            print("\n⚠️ تحذير: مشاكل في قاعدة البيانات، لكن سيتم المتابعة")
    except Exception as e:
        print(f"\n⚠️ تحذير في قاعدة البيانات: {e}")
    
    # تشغيل الخادم
    run_server()
    
    print("\n👋 شكراً لاستخدام لعبة المافيا!")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n💥 خطأ فادح: {e}")
        print("🔧 تحقق من الإعدادات وحاول مرة أخرى")
        input("اضغط Enter للخروج...")
    except KeyboardInterrupt:
        print("\n🛑 تم إنهاء البرنامج")