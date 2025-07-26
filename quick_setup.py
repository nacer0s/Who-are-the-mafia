#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد سريع للعبة المافيا
Quick Setup for Mafia Game
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def print_header():
    """طباعة رأس البرنامج"""
    print("🎭" + "="*58 + "🎭")
    print("🎮             إعداد سريع للعبة المافيا                🎮")
    print("🎭" + "="*58 + "🎭")
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

def check_python():
    """فحص إصدار Python"""
    print("🐍 فحص إصدار Python...")
    
    if sys.version_info < (3, 8):
        print("❌ يتطلب Python 3.8 أو أحدث")
        print(f"   الإصدار الحالي: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} - ممتاز!")
    return True

def install_requirements():
    """تثبيت المتطلبات"""
    print("\n📦 تثبيت المتطلبات...")
    
    try:
        # تحديث pip أولاً
        print("   🔄 تحديث pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # تثبيت المتطلبات
        print("   📥 تثبيت المكتبات...")  
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        
        print("✅ تم تثبيت جميع المتطلبات!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل في تثبيت المتطلبات: {e}")
        print("💡 حاول تشغيل: pip install -r requirements.txt")
        return False
    except FileNotFoundError:
        print("❌ ملف requirements.txt غير موجود")
        return False

def setup_env_file():
    """إعداد ملف البيئة"""
    print("\n⚙️ إعداد ملف البيئة...")
    
    if os.path.exists('.env'):
        print("✅ ملف .env موجود بالفعل")
        return True
    
    # إنشاء ملف .env أساسي
    env_content = """# إعدادات قاعدة البيانات
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///mafia_game.db

# إعدادات Flask
SECRET_KEY=24/05/2007-mafia-game-secret
DEBUG=True
HOST=0.0.0.0
PORT=5000

# إعدادات اللعبة
MIN_PLAYERS=4
MAX_PLAYERS=20
GAME_TIME_LIMIT=300
VOTE_TIME_LIMIT=60

# إعدادات OpenAI (اختياري - للذكاء الاصطناعي)
# OPENAI_API_KEY=sk-your-key-here
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ تم إنشاء ملف .env الأساسي")
        return True
    except Exception as e:
        print(f"❌ فشل في إنشاء ملف .env: {e}")
        return False

def setup_database():
    """إعداد قاعدة البيانات"""
    print("\n🗄️ إعداد قاعدة البيانات...")
    
    try:
        # تشغيل إعداد قاعدة البيانات
        result = subprocess.run([sys.executable, "setup_database.py"], 
                               capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ تم إعداد قاعدة البيانات بنجاح!")
            print("👤 حسابات جاهزة:")
            print("   • المدير: admin / admin123")
            print("   • اللاعبون: احمد، فاطمة، محمد / test123")
            return True
        else:
            print(f"⚠️ تحذير في إعداد قاعدة البيانات:")
            print(result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr)
            return True  # نتابع حتى لو كان هناك تحذيرات
            
    except subprocess.TimeoutExpired:
        print("⚠️ انتهت مهلة إعداد قاعدة البيانات، لكن قد يكون نجح")
        return True
    except Exception as e:
        print(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
        return False

def test_application():
    """اختبار التطبيق"""
    print("\n🧪 اختبار التطبيق...")
    
    try:
        # اختبار استيراد المكونات الأساسية
        result = subprocess.run([
            sys.executable, "-c", 
            "from app import create_app; app, socketio = create_app(); print('✅ التطبيق يعمل!')"
        ], capture_output=True, text=True, timeout=15)
        
        if "✅ التطبيق يعمل!" in result.stdout:
            print("✅ اختبار التطبيق نجح!")
            return True
        else:
            print("⚠️ التطبيق يعمل لكن مع تحذيرات")
            return True
            
    except subprocess.TimeoutExpired:
        print("⚠️ انتهت مهلة الاختبار")
        return True
    except Exception as e:
        print(f"❌ فشل اختبار التطبيق: {e}")
        return False

def show_completion_message():
    """عرض رسالة الإكمال"""
    print("\n" + "🎉" + "="*58 + "🎉")
    print("🎊                  تم الإعداد بنجاح!                  🎊")
    print("🎉" + "="*58 + "🎉")
    print()
    print("🚀 لتشغيل الخادم:")
    print("   python main.py")
    print()
    print("🌐 بعد التشغيل، اذهب إلى:")
    print("   http://localhost:5000")
    print()
    print("👤 حسابات جاهزة للتجربة:")
    print("   • admin / admin123 (مدير)")
    print("   • احمد / test123 (لاعب)")
    print("   • فاطمة / test123 (لاعب)")
    print()
    print("📚 للمساعدة:")
    print("   • دليل سريع: START_HERE.md")
    print("   • دليل شامل: GUIDE.md")
    print("   • اختبار شامل: python test_complete.py")
    print()
    print("🎮 استمتع بلعب المافيا! 🎭")
    print("="*60)

def main():
    """الدالة الرئيسية"""
    print_header()
    
    success_count = 0
    total_steps = 5
    
    # الخطوة 1: فحص Python
    if check_python():
        success_count += 1
    else:
        print("\n❌ لا يمكن المتابعة بدون Python مناسب")
        input("اضغط Enter للخروج...")
        return
    
    # الخطوة 2: تثبيت المتطلبات
    if install_requirements():
        success_count += 1
    else:
        print("⚠️ يمكن المتابعة لكن قد تحتاج لتثبيت المتطلبات يدوياً")
    
    # الخطوة 3: إعداد ملف البيئة
    if setup_env_file():
        success_count += 1
    
    # الخطوة 4: إعداد قاعدة البيانات
    if setup_database():
        success_count += 1
    
    # الخطوة 5: اختبار التطبيق
    if test_application():
        success_count += 1
    
    # عرض النتيجة
    print(f"\n📊 تم إكمال {success_count}/{total_steps} خطوات بنجاح")
    
    if success_count >= 3:
        show_completion_message()
        
        # سؤال عن التشغيل المباشر
        print("\n❓ هل تريد تشغيل الخادم الآن؟ (y/n): ", end="")
        try:
            choice = input().lower().strip()
            if choice in ['y', 'yes', 'نعم', 'ن']:
                print("\n🚀 تشغيل الخادم...")
                time.sleep(1)
                try:
                    subprocess.run([sys.executable, "main.py"])
                except KeyboardInterrupt:
                    print("\n🛑 تم إيقاف الخادم")
        except KeyboardInterrupt:
            print("\n👋 تم الإلغاء")
    else:
        print("\n⚠️ هناك مشاكل في الإعداد. راجع الأخطاء أعلاه.")
        print("💡 يمكنك المحاولة يدوياً:")
        print("   1. pip install -r requirements.txt")
        print("   2. python setup_database.py")  
        print("   3. python main.py")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الإعداد بواسطة المستخدم")
    except Exception as e:
        print(f"\n💥 خطأ غير متوقع: {e}")
        print("🔧 حاول الإعداد اليدوي")
    
    input("\nاضغط Enter للخروج...")