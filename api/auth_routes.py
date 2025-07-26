#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات التوثيق
Authentication Routes
"""

from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User
from models.statistics import UserStatistics

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """تسجيل مستخدم جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['username', 'display_name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'حقل {field} مطلوب'
                }), 400
        
        username = data['username'].strip().lower()
        display_name = data['display_name'].strip()
        password = data['password']
        email = data.get('email', '').strip()
        
        # التحقق من صحة البيانات
        if len(username) < 3:
            return jsonify({
                'success': False,
                'message': 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل'
            }), 400
        
        if len(display_name) < 2:
            return jsonify({
                'success': False,
                'message': 'الاسم المعروض يجب أن يكون حرفين على الأقل'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'
            }), 400
        
        # التحقق من عدم وجود المستخدم
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': 'اسم المستخدم موجود بالفعل'
            }), 409
        
        if email and User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني موجود بالفعل'
            }), 409
        
        # إنشاء المستخدم
        user = User(
            username=username,
            display_name=display_name,
            email=email or None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # إنشاء إحصائيات المستخدم
        stats = UserStatistics(user_id=user.id)
        db.session.add(stats)
        db.session.commit()
        
        # تسجيل دخول تلقائي
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': 'تم التسجيل بنجاح',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في التسجيل: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """تسجيل الدخول"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        if not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'اسم المستخدم وكلمة المرور مطلوبان'
            }), 400
        
        username = data['username'].strip().lower()
        password = data['password']
        
        # البحث عن المستخدم
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': 'الحساب معطل'
            }), 403
        
        # تسجيل الدخول
        login_user(user, remember=data.get('remember', False))
        user.update_last_seen()
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الدخول بنجاح',
            'user': user.to_dict(include_stats=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تسجيل الدخول: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """تسجيل الخروج"""
    try:
        current_user.set_offline()
        logout_user()
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الخروج بنجاح'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تسجيل الخروج: {str(e)}'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """الحصول على الملف الشخصي"""
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict(include_stats=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في الحصول على الملف الشخصي: {str(e)}'
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """تحديث الملف الشخصي"""
    try:
        data = request.get_json()
        
        # الحقول القابلة للتحديث
        updatable_fields = ['display_name', 'email', 'bio', 'avatar_url']
        
        for field in updatable_fields:
            if field in data:
                value = data[field]
                
                # تحقق خاص لكل حقل
                if field == 'display_name':
                    if not value or len(value.strip()) < 2:
                        return jsonify({
                            'success': False,
                            'message': 'الاسم المعروض يجب أن يكون حرفين على الأقل'
                        }), 400
                    value = value.strip()
                
                elif field == 'email':
                    if value:  # إذا لم يكن فارغ
                        value = value.strip().lower()
                        # التحقق من عدم وجود البريد لمستخدم آخر
                        existing_user = User.query.filter(
                            User.email == value,
                            User.id != current_user.id
                        ).first()
                        
                        if existing_user:
                            return jsonify({
                                'success': False,
                                'message': 'البريد الإلكتروني موجود بالفعل'
                            }), 409
                    else:
                        value = None
                
                elif field == 'bio':
                    if value and len(value) > 500:
                        return jsonify({
                            'success': False,
                            'message': 'النبذة الشخصية يجب أن تكون أقل من 500 حرف'
                        }), 400
                
                setattr(current_user, field, value)
        
        current_user.updated_at = db.func.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث الملف الشخصي بنجاح',
            'user': current_user.to_dict(include_stats=True)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث الملف الشخصي: {str(e)}'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """تغيير كلمة المرور"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        if not all([data.get('current_password'), data.get('new_password')]):
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الحالية والجديدة مطلوبتان'
            }), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # التحقق من كلمة المرور الحالية
        if not current_user.check_password(current_password):
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الحالية غير صحيحة'
            }), 401
        
        # التحقق من كلمة المرور الجديدة
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل'
            }), 400
        
        if current_password == new_password:
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الجديدة يجب أن تكون مختلفة عن الحالية'
            }), 400
        
        # تحديث كلمة المرور
        current_user.set_password(new_password)
        current_user.updated_at = db.func.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تغيير كلمة المرور بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تغيير كلمة المرور: {str(e)}'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """الحصول على معلومات المستخدم الحالي"""
    try:
        current_user.update_last_seen()
        return jsonify({
            'success': True,
            'user': current_user.to_dict(include_stats=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في الحصول على بيانات المستخدم: {str(e)}'
        }), 500

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """التحقق من حالة التوثيق"""
    try:
        if current_user.is_authenticated:
            current_user.update_last_seen()
            return jsonify({
                'authenticated': True,
                'user': current_user.to_dict(include_stats=True)
            })
        else:
            return jsonify({
                'authenticated': False,
                'user': None
            })
            
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500

@auth_bp.route('/users/search', methods=['GET'])
@login_required
def search_users():
    """البحث عن المستخدمين"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if len(query) < 2:
            return jsonify({
                'success': False,
                'message': 'يجب أن يكون النص المراد البحث عنه حرفين على الأقل'
            }), 400
        
        # البحث في الاسم المعروض واسم المستخدم
        users = User.query.filter(
            db.or_(
                User.display_name.contains(query),
                User.username.contains(query)
            ),
            User.is_active == True,
            User.id != current_user.id
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'count': len(users)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في البحث: {str(e)}'
        }), 500

@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_profile(user_id):
    """الحصول على ملف مستخدم آخر"""
    try:
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict(include_stats=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في الحصول على المستخدم: {str(e)}'
        }), 500