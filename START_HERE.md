# 🎮 ابدأ هنا - لعبة المافيا

## 🚀 تشغيل سريع (5 دقائق)

### الخطوة 1: تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### الخطوة 2: إعداد قاعدة البيانات
```bash
python setup_database.py
```

### الخطوة 3: تشغيل التطبيق
```bash
python app.py
```

**🎉 التطبيق يعمل الآن على: http://localhost:5000**

---

## 🔧 إعداد متقدم

### 1. إعداد XAMPP (MySQL)

1. تحميل وتثبيت [XAMPP](https://www.apachefriends.org/download.html)
2. تشغيل Apache و MySQL
3. إنشاء قاعدة بيانات `mafia_game` في phpMyAdmin
4. تحديث ملف `.env`:
```env
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=mafia_game
```

### 2. إعداد الذكاء الاصطناعي (اختياري)

1. الحصول على مفتاح من [OpenAI](https://platform.openai.com/api-keys)
2. إضافته للملف `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
```

---

## 🧪 اختبار التطبيق

### حسابات جاهزة للاختبار:

| اسم المستخدم | كلمة المرور | النوع |
|---|---|---|
| `admin` | `admin123` | مدير |
| `احمد` | `test123` | لاعب |
| `فاطمة` | `test123` | لاعب |
| `محمد` | `test123` | لاعب |
| `عائشة` | `test123` | لاعب |

### روابط مفيدة:
- **الصفحة الرئيسية**: http://localhost:5000
- **معلومات API**: http://localhost:5000/api/info
- **فحص الصحة**: http://localhost:5000/health

### اختبار API:
```bash
# اختبار سريع
python examples/api_usage.py quick

# اختبار كامل
python examples/api_usage.py
```

---

## 📱 كيفية اللعب

### 1. إنشاء حساب
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","display_name":"مستخدم تجريبي","password":"123456"}'
```

### 2. تسجيل الدخول
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'
```

### 3. إنشاء غرفة
```bash
curl -X POST http://localhost:5000/api/room/create \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"name":"غرفة تجريبية","max_players":8}'
```

---

## 🎭 الأدوار في اللعبة

| الدور | الوصف | القدرات |
|---|---|---|
| 👥 **مواطن** | الدور الأساسي | التصويت فقط |
| 🖤 **مافيا** | الأشرار | قتل المواطنين ليلاً |
| 👨‍⚕️ **طبيب** | المعالج | حماية لاعب واحد كل ليلة |
| 🕵️ **محقق** | المحقق | التحقق من هوية لاعب كل ليلة |
| ⚖️ **عدالة شعبية** | المنتقم | قتل لاعب واحد كل ليلة |
| 👑 **عمدة** | القائد | صوته يحسب بصوتين |
| 🃏 **مهرج** | المخرب | يفوز إذا تم إعدامه |

---

## 🤖 ميزات الذكاء الاصطناعي

- **🔍 كشف الغش**: تحليل الرسائل للكشف عن كشف الأدوار
- **🗣️ تحويل الصوت**: تحويل الرسائل الصوتية إلى نص
- **📊 تحليل الأداء**: تقارير ذكية عن أداء اللاعبين
- **⚠️ الإنذار المبكر**: تحذيرات من السلوك المشبوه

---

## 🐛 حل المشاكل

### مشكلة قاعدة البيانات
```bash
# استخدم SQLite مؤقتاً
echo "DATABASE_TYPE=sqlite" >> .env
python setup_database.py reset
```

### مشكلة المتطلبات
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### مشكلة الاتصال
```bash
# تأكد من عدم استخدام المنفذ
netstat -an | findstr :5000
```

---

## 📚 مزيد من التفاصيل

- **📖 دليل كامل**: [README.md](README.md)
- **🛠️ دليل التثبيت المفصل**: [INSTALL.md](INSTALL.md)
- **💻 أمثلة الكود**: [examples/](examples/)

---

## 🆘 طلب المساعدة

إذا واجهت مشاكل:

1. ✅ تأكد من تشغيل `python setup_database.py`
2. ✅ تحقق من ملف `.env`
3. ✅ اقرأ رسائل الخطأ في الكونسول
4. ✅ جرب الإعداد الأساسي مع SQLite أولاً

---

## 🎉 استمتع باللعب!

**مبروك! 🎊 أصبح لديك خادم لعبة المافيا جاهز للاستخدام!**

🎮 **ادعُ أصدقاءك وابدأوا اللعب الآن!**