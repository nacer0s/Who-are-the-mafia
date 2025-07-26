#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد قاعدة البيانات
Database Setup Script
"""

import os
import sys
from datetime import datetime

# إضافة المشروع للمسار
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User
from models.statistics import UserStatistics

def create_database():
    """إنشاء قاعدة البيانات والجداول"""
    
    print("🗄️ بدء إعداد قاعدة البيانات...")
    
    # إنشاء التطبيق
    app, _ = create_app('development')
    
    with app.app_context():
        try:
            # إنشاء جميع الجداول
            db.create_all()
            print("✅ تم إنشاء جميع الجداول بنجاح")
            
            # فحص الجداول المنشأة
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 الجداول المنشأة: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
            return False

def create_admin_user():
    """إنشاء مستخدم مدير"""
    
    app, _ = create_app('development')
    
    with app.app_context():
        try:
            # التحقق من وجود المدير
            admin = User.query.filter_by(username='admin').first()
            
            if admin:
                print("ℹ️ المستخدم المدير موجود بالفعل")
                return True
            
            # إنشاء المدير
            admin = User(
                username='admin',
                display_name='المدير العام',
                email='admin@mafia.game'
            )
            admin.set_password('admin123')
            admin.is_admin = True
            
            db.session.add(admin)
            db.session.commit()
            
            # إنشاء إحصائيات المدير
            admin_stats = UserStatistics(user_id=admin.id)
            db.session.add(admin_stats)
            db.session.commit()
            
            print("✅ تم إنشاء المستخدم المدير")
            print("👤 اسم المستخدم: admin")
            print("🔑 كلمة المرور: admin123")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء المستخدم المدير: {e}")
            db.session.rollback()
            return False

def create_test_users():
    """إنشاء مستخدمين للاختبار"""
    
    app, _ = create_app('development')
    
    with app.app_context():
        try:
            test_users_data = [
                ('احمد', 'أحمد محمد', 'ahmed@test.com'),
                ('فاطمة', 'فاطمة علي', 'fatima@test.com'),
                ('محمد', 'محمد حسن', 'mohammed@test.com'),
                ('عائشة', 'عائشة أحمد', 'aisha@test.com'),
                ('يوسف', 'يوسف إبراهيم', 'youssef@test.com'),
                ('مريم', 'مريم خليل', 'mariam@test.com'),
                ('عمر', 'عمر سعد', 'omar@test.com'),
                ('زينب', 'زينب محمود', 'zeinab@test.com')
            ]
            
            created_count = 0
            
            for username, display_name, email in test_users_data:
                # التحقق من وجود المستخدم
                existing_user = User.query.filter_by(username=username).first()
                
                if existing_user:
                    continue
                
                # إنشاء المستخدم
                user = User(
                    username=username,
                    display_name=display_name,
                    email=email
                )
                user.set_password('test123')
                
                db.session.add(user)
                db.session.flush()  # للحصول على ID
                
                # إنشاء إحصائيات المستخدم
                user_stats = UserStatistics(user_id=user.id)
                db.session.add(user_stats)
                
                created_count += 1
            
            db.session.commit()
            
            print(f"✅ تم إنشاء {created_count} مستخدم للاختبار")
            if created_count > 0:
                print("🔑 كلمة مرور جميع المستخدمين: test123")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء المستخدمين التجريبيين: {e}")
            db.session.rollback()
            return False

def verify_database():
    """التحقق من صحة قاعدة البيانات"""
    
    app, _ = create_app('development')
    
    with app.app_context():
        try:
            # فحص الجداول
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'users', 'rooms', 'games', 'players', 
                'messages', 'game_logs', 'user_statistics'
            ]
            
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️ جداول مفقودة: {', '.join(missing_tables)}")
                return False
            
            # فحص البيانات
            user_count = User.query.count()
            stats_count = UserStatistics.query.count()
            
            print(f"📊 إحصائيات قاعدة البيانات:")
            print(f"   👥 المستخدمون: {user_count}")
            print(f"   📈 سجلات الإحصائيات: {stats_count}")
            
            # فحص المدير
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print(f"   👑 المدير: {admin.display_name}")
            else:
                print("   ⚠️ لا يوجد مدير")
            
            print("✅ قاعدة البيانات تعمل بشكل صحيح")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
            return False

def reset_database():
    """إعادة تعيين قاعدة البيانات"""
    
    print("⚠️ سيتم حذف جميع البيانات!")
    confirm = input("هل أنت متأكد؟ (yes/no): ").lower()
    
    if confirm != 'yes':
        print("❌ تم إلغاء العملية")
        return False
    
    app, _ = create_app('development')
    
    with app.app_context():
        try:
            # حذف جميع الجداول
            db.drop_all()
            print("🗑️ تم حذف جميع الجداول")
            
            # إنشاء الجداول من جديد
            db.create_all()
            print("✅ تم إنشاء الجداول من جديد")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إعادة تعيين قاعدة البيانات: {e}")
            return False

def main():
    """الدالة الرئيسية"""
    
    print("=" * 50)
    print("🎮 إعداد قاعدة بيانات لعبة المافيا")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'reset':
            success = reset_database()
        elif command == 'verify':
            success = verify_database()
        elif command == 'admin':
            success = create_admin_user()
        elif command == 'test-users':
            success = create_test_users()
        else:
            print(f"❌ أمر غير معروف: {command}")
            print("الأوامر المتاحة: reset, verify, admin, test-users")
            return
    else:
        # الإعداد الكامل
        success = True
        
        # 1. إنشاء قاعدة البيانات
        if success:
            success = create_database()
        
        # 2. إنشاء المدير
        if success:
            success = create_admin_user()
        
        # 3. إنشاء مستخدمين للاختبار
        if success:
            success = create_test_users()
        
        # 4. التحقق من النتيجة
        if success:
            success = verify_database()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 تم إعداد قاعدة البيانات بنجاح!")
        print("🚀 يمكنك الآن تشغيل التطبيق بالأمر: python app.py")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ فشل في إعداد قاعدة البيانات")
        print("🔧 تحقق من الإعدادات وحاول مرة أخرى")
        print("=" * 50)

if __name__ == '__main__':
    main()