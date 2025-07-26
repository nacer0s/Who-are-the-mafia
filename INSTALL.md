# 🚀 دليل التثبيت السريع - لعبة المافيا

## 📋 التثبيت خطوة بخطوة

### 1. متطلبات النظام
- **Python 3.8+** - [تحميل Python](https://www.python.org/downloads/)
- **XAMPP** (للمايسكل) - [تحميل XAMPP](https://www.apachefriends.org/download.html)
- **مفتاح OpenAI** (اختياري) - [الحصول على مفتاح](https://platform.openai.com/api-keys)

### 2. إعداد قاعدة البيانات

#### أ) استخدام XAMPP (موصى به):
1. **تثبيت XAMPP** وتشغيله
2. **تشغيل Apache و MySQL** من لوحة التحكم
3. **فتح phpMyAdmin**: `http://localhost/phpmyadmin`
4. **إنشاء قاعدة بيانات جديدة**:
   ```sql
   CREATE DATABASE mafia_game CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

#### ب) استخدام SQLite (للتطوير السريع):
- لا حاجة لإعداد إضافي، سيتم إنشاء الملف تلقائياً

### 3. إعداد المشروع

```bash
# 1. إنشاء مجلد المشروع
mkdir mafia-game
cd mafia-game

# 2. إنشاء بيئة افتراضية
python -m venv venv

# 3. تفعيل البيئة الافتراضية
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. تثبيت المتطلبات
pip install -r requirements.txt
```

### 4. إعداد متغيرات البيئة

إنشاء ملف `.env` في جذر المشروع:

```env
# ===== إعدادات قاعدة البيانات =====
# للمايسكل (XAMPP):
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=mafia_game

# أو للـ SQLite (أسهل للتجربة):
# DATABASE_TYPE=sqlite

# ===== إعدادات Flask =====
SECRET_KEY=24/05/2007-your-secret-key-here
DEBUG=True
HOST=0.0.0.0
PORT=5000

# ===== إعدادات OpenAI (اختياري) =====
OPENAI_API_KEY=sk-your-openai-api-key-here

# ===== إعدادات اللعبة =====
MIN_PLAYERS=4
MAX_PLAYERS=20
```

### 5. إعداد قاعدة البيانات

```bash
# إنشاء الجداول والبيانات الأساسية
python setup_database.py

# للتحقق من صحة الإعداد
python setup_database.py verify
```

### 6. تشغيل التطبيق

```bash
# الطريقة الأولى
python app.py

# أو الطريقة الثانية
python run.py
```

**✅ التطبيق يعمل الآن على:** `http://localhost:5000`

## 🔧 اختبار التطبيق

### 1. فحص الصحة
```bash
curl http://localhost:5000/health
```

### 2. معلومات API
```bash
curl http://localhost:5000/api/info
```

### 3. تسجيل مستخدم جديد
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "display_name": "مستخدم تجريبي",
    "password": "123456",
    "email": "test@example.com"
  }'
```

## 👥 الحسابات الافتراضية

بعد تشغيل `setup_database.py`:

### حساب المدير:
- **اسم المستخدم:** `admin`
- **كلمة المرور:** `admin123`

### حسابات تجريبية:
- **أسماء المستخدمين:** `احمد`, `فاطمة`, `محمد`, `عائشة`, إلخ
- **كلمة المرور:** `test123`

## 🐛 حل المشاكل الشائعة

### مشكلة الاتصال بقاعدة البيانات
```bash
# تأكد من تشغيل MySQL في XAMPP
# أو استخدم SQLite مؤقتاً
DATABASE_TYPE=sqlite
```

### مشكلة المتطلبات
```bash
# تحديث pip
python -m pip install --upgrade pip

# إعادة تثبيت المتطلبات
pip install -r requirements.txt --force-reinstall
```

### مشكلة الذكاء الاصطناعي
```bash
# الذكاء الاصطناعي اختياري، يمكن تشغيل التطبيق بدونه
# تأكد من صحة مفتاح OpenAI أو احذفه من .env
```

## 📱 استخدام واجهة الويب

### إنشاء غرفة جديدة:
1. سجل دخول بحساب تجريبي
2. اذهب إلى `/api/room/create`
3. أدخل اسم الغرفة وإعداداتها

### الانضمام لغرفة:
1. احصل على رمز الغرفة
2. استخدم `/api/room/join`
3. ابدأ اللعب!

## 🎮 اختبار اللعبة الكاملة

### 1. إنشاء عدة مستخدمين
```bash
# سيتم إنشاؤهم تلقائياً عند تشغيل setup_database.py
```

### 2. إنشاء غرفة وبدء لعبة
```bash
# استخدم حسابات متعددة في متصفحات مختلفة
# أو استخدم أدوات اختبار API
```

### 3. اختبار الميزات
- ✅ الدردشة النصية
- ✅ الأدوار المختلفة  
- ✅ التصويت
- ✅ مراحل اللعبة
- ✅ الإحصائيات

## 📞 الحصول على المساعدة

إذا واجهت مشاكل:

1. **تحقق من السجلات** في وحدة التحكم
2. **تأكد من الإعدادات** في ملف `.env`
3. **جرب الإعداد الأساسي** مع SQLite أولاً
4. **اقرأ رسائل الخطأ** بعناية

## 🎉 تهانينا!

إذا وصلت لهنا، فقد نجحت في تثبيت وتشغيل لعبة المافيا!

**استمتع باللعب! 🎭**