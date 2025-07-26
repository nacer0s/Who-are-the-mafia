#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تشغيل سريع للمشروع
Quick Run Script
"""

import os
import sys
from app import create_app

def main():
    """تشغيل التطبيق"""
    
    print("🎮 بدء تشغيل لعبة المافيا...")
    
    # التحقق من وجود ملف البيئة
    if not os.path.exists('.env'):
        print("⚠️ ملف .env غير موجود!")
        print("📝 يرجى إنشاء ملف .env وإضافة الإعدادات المطلوبة")
        return
    
    # إنشاء التطبيق
    try:
        app, socketio = create_app('development')
        
        # طباعة معلومات التشغيل
        print(f"🌐 الخادم: http://{app.config['HOST']}:{app.config['PORT']}")
        print(f"🔧 وضع التطوير: {'مفعل' if app.config['DEBUG'] else 'معطل'}")
        print(f"🤖 الذكاء الاصطناعي: {'مفعل' if app.config.get('OPENAI_API_KEY') else 'معطل'}")
        print("=" * 50)
        
        # تشغيل الخادم
        socketio.run(
            app,
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'],
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {e}")
        return

if __name__ == '__main__':
    main()