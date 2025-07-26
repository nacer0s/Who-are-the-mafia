#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار شامل للعبة المافيا
Complete Testing Suite
"""

import requests
import json
import time
import sys
from datetime import datetime

class MafiaGameTester:
    """فئة اختبار شاملة للعبة المافيا"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """تسجيل نتيجة اختبار"""
        status = "✅ نجح" if success else "❌ فشل"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now()
        })
        print(f"{status}: {test_name} {message}")
        
    def test_server_health(self):
        """اختبار صحة الخادم"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            data = response.json()
            
            if response.status_code == 200 and data.get('status') == 'healthy':
                self.log_test("صحة الخادم", True, f"قاعدة البيانات: {data.get('database')}")
                return True
            else:
                self.log_test("صحة الخادم", False, f"استجابة غير متوقعة: {data}")
                return False
                
        except Exception as e:
            self.log_test("صحة الخادم", False, f"خطأ: {e}")
            return False
    
    def test_api_info(self):
        """اختبار معلومات API"""
        try:
            response = self.session.get(f"{self.base_url}/api/info")
            data = response.json()
            
            if response.status_code == 200 and 'api_version' in data:
                ai_features = data.get('ai_features', {})
                ai_count = sum(1 for v in ai_features.values() if v)
                self.log_test("معلومات API", True, f"ميزات AI: {ai_count}/4")
                return True
            else:
                self.log_test("معلومات API", False, "معلومات ناقصة")
                return False
                
        except Exception as e:
            self.log_test("معلومات API", False, f"خطأ: {e}")
            return False
    
    def test_user_registration(self):
        """اختبار تسجيل المستخدمين"""
        test_user = {
            "username": f"test_user_{int(time.time())}",
            "display_name": "مستخدم تجريبي",
            "password": "test123",
            "email": "test@example.com"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=test_user
            )
            data = response.json()
            
            if response.status_code == 201 and data.get('success'):
                self.log_test("تسجيل المستخدم", True, f"المستخدم: {test_user['username']}")
                return test_user
            else:
                self.log_test("تسجيل المستخدم", False, data.get('message', 'خطأ غير معروف'))
                return None
                
        except Exception as e:
            self.log_test("تسجيل المستخدم", False, f"خطأ: {e}")
            return None
    
    def test_user_login(self, username, password):
        """اختبار تسجيل الدخول"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password}
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test("تسجيل الدخول", True, f"المستخدم: {username}")
                return data.get('user')
            else:
                self.log_test("تسجيل الدخول", False, data.get('message', 'فشل تسجيل الدخول'))
                return None
                
        except Exception as e:
            self.log_test("تسجيل الدخول", False, f"خطأ: {e}")
            return None
    
    def test_room_creation(self):
        """اختبار إنشاء الغرف"""
        room_data = {
            "name": f"غرفة تجريبية {int(time.time())}",
            "max_players": 8,
            "min_players": 4,
            "allow_voice_chat": True,
            "allow_text_chat": True
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/room/create",
                json=room_data
            )
            data = response.json()
            
            if response.status_code == 201 and data.get('success'):
                room = data.get('room', {})
                self.log_test("إنشاء الغرفة", True, f"الرمز: {room.get('room_code', 'غير معروف')}")
                return room
            else:
                self.log_test("إنشاء الغرفة", False, data.get('message', 'فشل إنشاء الغرفة'))
                return None
                
        except Exception as e:
            self.log_test("إنشاء الغرفة", False, f"خطأ: {e}")
            return None
    
    def test_room_joining(self, room_code):
        """اختبار الانضمام للغرف"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/room/join",
                json={"room_code": room_code}
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test("الانضمام للغرفة", True, f"الرمز: {room_code}")
                return True
            else:
                self.log_test("الانضمام للغرفة", False, data.get('message', 'فشل الانضمام'))
                return False
                
        except Exception as e:
            self.log_test("الانضمام للغرفة", False, f"خطأ: {e}")
            return False
    
    def test_statistics(self):
        """اختبار الإحصائيات"""
        try:
            # إحصائيات المستخدم
            response = self.session.get(f"{self.base_url}/api/stats/my-stats")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                stats = data.get('statistics', {})
                self.log_test("إحصائيات المستخدم", True, f"الألعاب: {stats.get('total_games_played', 0)}")
            else:
                self.log_test("إحصائيات المستخدم", False, "فشل في الحصول على الإحصائيات")
            
            # إحصائيات عامة
            response = self.session.get(f"{self.base_url}/api/stats/global")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                platform = data.get('platform', {})
                self.log_test("إحصائيات عامة", True, f"المستخدمون: {platform.get('total_users', 0)}")
                return True
            else:
                self.log_test("إحصائيات عامة", False, "فشل في الإحصائيات العامة")
                return False
                
        except Exception as e:
            self.log_test("الإحصائيات", False, f"خطأ: {e}")
            return False
    
    def test_ai_features(self):
        """اختبار ميزات الذكاء الاصطناعي"""
        try:
            # اختبار تحليل الرسائل الأساسي
            from ai import MessageAnalyzer
            analyzer = MessageAnalyzer()
            
            test_message = "مرحبا، أنا مواطن عادي في هذه اللعبة"
            analysis = analyzer.analyze_basic_patterns(test_message)
            
            if analysis:
                self.log_test("تحليل الرسائل", True, f"تم تحليل {len(test_message)} حرف")
            else:
                self.log_test("تحليل الرسائل", False, "فشل في التحليل الأساسي")
            
            # اختبار محول الصوت (إذا كان متاحاً)
            from ai import SpeechToText
            stt = SpeechToText()
            
            if hasattr(stt, 'openai_available') and stt.openai_available:
                self.log_test("تحويل الصوت", True, "OpenAI متاح")
            else:
                self.log_test("تحويل الصوت", False, "OpenAI غير متاح")
            
            return True
            
        except Exception as e:
            self.log_test("ميزات الذكاء الاصطناعي", False, f"خطأ: {e}")
            return False
    
    def test_models(self):
        """اختبار النماذج"""
        try:
            # اختبار استيراد النماذج
            from models import User, Room, Game, Player, Message
            self.log_test("استيراد النماذج", True, "جميع النماذج متاحة")
            
            # اختبار إنشاء مستخدم
            from models import db
            from app import create_app
            
            app, _ = create_app()
            with app.app_context():
                user_count = User.query.count()
                self.log_test("قاعدة البيانات", True, f"المستخدمون: {user_count}")
            
            return True
            
        except Exception as e:
            self.log_test("النماذج", False, f"خطأ: {e}")
            return False
    
    def run_complete_test(self):
        """تشغيل اختبار شامل"""
        print("🧪 بدء الاختبار الشامل للعبة المافيا")
        print("=" * 60)
        
        # اختبار البنية الأساسية
        print("\n📋 اختبار البنية الأساسية:")
        self.test_models()
        self.test_ai_features()
        
        # اختبار الخادم
        print("\n🌐 اختبار الخادم:")
        if not self.test_server_health():
            print("❌ فشل في الاتصال بالخادم - تأكد من تشغيله")
            return False
        
        self.test_api_info()
        
        # اختبار المستخدمين
        print("\n👤 اختبار المستخدمين:")
        
        # تجربة تسجيل دخول بحساب موجود
        user = self.test_user_login("admin", "admin123")
        if not user:
            # إنشاء حساب جديد إذا فشل تسجيل الدخول
            test_user = self.test_user_registration()
            if test_user:
                user = self.test_user_login(test_user['username'], test_user['password'])
        
        if not user:
            print("❌ فشل في تسجيل الدخول - تحقق من قاعدة البيانات")
            return False
        
        # اختبار الغرف
        print("\n🏠 اختبار الغرف:")
        room = self.test_room_creation()
        if room:
            # إنشاء جلسة جديدة لاختبار الانضمام
            new_session = requests.Session()
            
            # تسجيل دخول مستخدم آخر
            new_session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "احمد", "password": "test123"}
            )
            
            # اختبار الانضمام
            response = new_session.post(
                f"{self.base_url}/api/room/join",
                json={"room_code": room.get('room_code')}
            )
            
            if response.status_code == 200:
                self.log_test("انضمام مستخدم ثاني", True, "تم بنجاح")
            else:
                self.log_test("انضمام مستخدم ثاني", False, "فشل الانضمام")
        
        # اختبار الإحصائيات
        print("\n📊 اختبار الإحصائيات:")
        self.test_statistics()
        
        # عرض النتائج
        self.show_results()
        
        return True
    
    def show_results(self):
        """عرض نتائج الاختبار"""
        print("\n" + "=" * 60)
        print("📋 ملخص نتائج الاختبار")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ نجح: {passed}")
        print(f"❌ فشل: {total - passed}")
        print(f"📊 النسبة: {percentage:.1f}%")
        
        if percentage >= 80:
            print("🎉 النظام يعمل بشكل ممتاز!")
        elif percentage >= 60:
            print("✅ النظام يعمل بشكل جيد")
        else:
            print("⚠️ النظام يحتاج لمراجعة")
        
        # عرض الاختبارات الفاشلة
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("\n❌ الاختبارات الفاشلة:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        print("\n" + "=" * 60)

def main():
    """الدالة الرئيسية"""
    print("🎮 اختبار شامل للعبة المافيا")
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # التحقق من وجود خادم محلي
    tester = MafiaGameTester()
    
    try:
        tester.run_complete_test()
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الاختبار بواسطة المستخدم")
    except Exception as e:
        print(f"\n💥 خطأ في الاختبار: {e}")
    
    print("\n👋 انتهى الاختبار")

if __name__ == '__main__':
    main()