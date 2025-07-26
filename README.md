# 🎮 لعبة المافيا - خادم خلفي متكامل

## 📖 وصف المشروع

لعبة المافيا هي تطبيق ويب تفاعلي متعدد اللاعبين مبني بـ Python Flask. تدعم اللعبة الدردشة النصية والصوتية مع ذكاء اصطناعي متطور للكشف عن الغش وتحليل الأداء.

### ✨ الميزات الرئيسية

- 🎭 **أدوار متنوعة**: مافيا، مواطن، طبيب، محقق، عدالة شعبية، عمدة، مهرج
- 💬 **دردشة نصية وصوتية**: تواصل مباشر بين اللاعبين
- 🤖 **ذكاء اصطناعي**: كشف تلقائي للغش وتحليل المحادثات
- 📊 **إحصائيات تفصيلية**: تتبع الأداء وتحليل الاستراتيجيات
- 🏠 **إدارة الغرف**: إنشاء وإدارة غرف اللعب
- ⚡ **الوقت الفعلي**: استخدام WebSocket للتحديثات المباشرة
- 🛡️ **أمان متقدم**: حماية ضد التلاعب والغش

## 🏗️ هيكل المشروع

```
Who The Mafia/
├── 📁 models/              # نماذج قاعدة البيانات
│   ├── __init__.py
│   ├── user.py            # نموذج المستخدم
│   ├── room.py            # نموذج الغرفة
│   ├── game.py            # نموذج اللعبة
│   ├── player.py          # نموذج اللاعب
│   ├── message.py         # نموذج الرسائل
│   ├── game_log.py        # سجل أحداث اللعبة
│   └── statistics.py      # إحصائيات المستخدمين
├── 📁 game/               # منطق اللعبة
│   ├── __init__.py
│   ├── game_manager.py    # مدير الألعاب الرئيسي
│   ├── room_manager.py    # مدير الغرف
│   ├── role_manager.py    # مدير الأدوار
│   ├── voting_manager.py  # مدير التصويت
│   └── phase_manager.py   # مدير مراحل اللعبة
├── 📁 api/                # واجهات برمجة التطبيقات
│   ├── __init__.py
│   ├── auth_routes.py     # مسارات التوثيق
│   ├── game_routes.py     # مسارات اللعبة
│   ├── room_routes.py     # مسارات الغرف
│   └── stats_routes.py    # مسارات الإحصائيات
├── 📁 websocket/          # أحداث الوقت الفعلي
│   ├── __init__.py
│   ├── game_events.py     # أحداث اللعبة
│   ├── room_events.py     # أحداث الغرف
│   ├── chat_events.py     # أحداث الدردشة
│   └── voice_events.py    # أحداث الصوت
├── 📁 ai/                 # محركات الذكاء الاصطناعي
│   ├── __init__.py
│   ├── message_analyzer.py # محلل الرسائل
│   ├── speech_to_text.py   # تحويل الصوت إلى نص
│   ├── game_analyzer.py    # محلل الألعاب
│   └── stats_analyzer.py   # محلل الإحصائيات
├── 📁 static/             # الملفات الثابتة
│   └── voice_messages/    # الرسائل الصوتية
├── app.py                 # الملف الرئيسي
├── config.py             # إعدادات التطبيق
├── requirements.txt      # متطلبات Python
├── .env                  # متغيرات البيئة
└── README.md            # هذا الملف
```

## 🚀 التثبيت والتشغيل

### 1. متطلبات النظام

- Python 3.8 أو أحدث
- MySQL أو SQLite
- مفتاح OpenAI API (اختياري للذكاء الاصطناعي)

### 2. استنساخ المشروع

```bash
git clone <repository-url>
cd "Who The Mafia"
```

### 3. إنشاء بيئة افتراضية

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 4. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 5. إعداد متغيرات البيئة

قم بتحرير ملف `.env`:

```env
# إعدادات قاعدة البيانات
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mafia_game

# إعدادات Flask
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=5000

# إعدادات OpenAI (اختياري)
OPENAI_API_KEY=your_openai_api_key

# إعدادات اللعبة
MIN_PLAYERS=4
MAX_PLAYERS=20
```

### 6. إعداد قاعدة البيانات

#### استخدام MySQL (موصى به):

1. تثبيت XAMPP من [هنا](https://www.apachefriends.org/download.html)
2. تشغيل Apache و MySQL من لوحة تحكم XAMPP
3. إنشاء قاعدة بيانات جديدة:
   ```sql
   CREATE DATABASE mafia_game CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

#### استخدام SQLite (للتطوير):

```env
DATABASE_TYPE=sqlite
```

### 7. تشغيل التطبيق

```bash
python app.py
```

الخادم سيعمل على: `http://localhost:5000`

## 🎮 كيفية اللعب

### إنشاء حساب

```bash
POST /api/auth/register
{
    "username": "player1",
    "display_name": "اللاعب الأول", 
    "password": "123456",
    "email": "player1@example.com"
}
```

### تسجيل الدخول

```bash
POST /api/auth/login
{
    "username": "player1",
    "password": "123456"
}
```

### إنشاء غرفة

```bash
POST /api/room/create
{
    "name": "غرفة تجريبية",
    "max_players": 8,
    "min_players": 4,
    "allow_voice_chat": true
}
```

### الانضمام لغرفة

```bash
POST /api/room/join
{
    "room_code": "ABC123",
    "password": "optional"
}
```

## 🔌 واجهات برمجة التطبيقات

### 🔐 التوثيق (`/api/auth`)

- `POST /register` - تسجيل مستخدم جديد
- `POST /login` - تسجيل الدخول
- `POST /logout` - تسجيل الخروج
- `GET /profile` - الملف الشخصي
- `PUT /profile` - تحديث الملف الشخصي
- `POST /change-password` - تغيير كلمة المرور

### 🏠 الغرف (`/api/room`)

- `POST /create` - إنشاء غرفة جديدة
- `POST /join` - الانضمام لغرفة
- `POST /leave` - مغادرة الغرفة
- `GET /my-room` - الغرفة الحالية
- `GET /public` - الغرف العامة
- `GET /<room_code>` - معلومات غرفة
- `POST /<room_code>/ready` - تعيين الاستعداد

### 🎮 اللعبة (`/api/game`)

- `POST /start` - بدء اللعبة
- `GET /status` - حالة اللعبة
- `POST /action` - تنفيذ إجراء
- `POST /vote` - التصويت
- `GET /player-info` - معلومات اللاعب

### 📊 الإحصائيات (`/api/stats`)

- `GET /my-stats` - إحصائياتي
- `GET /user/<user_id>` - إحصائيات مستخدم
- `GET /leaderboard` - لوحة المتصدرين
- `GET /global` - إحصائيات عامة
- `GET /analyze-game/<game_id>` - تحليل لعبة

## 🔄 أحداث WebSocket

### اتصال الغرف

```javascript
// الانضمام لغرفة
socket.emit('join_room', {
    room_code: 'ABC123',
    password: 'optional'
});

// مغادرة الغرفة
socket.emit('leave_room');

// تعيين الاستعداد
socket.emit('set_ready', { ready: true });
```

### اللعبة

```javascript
// بدء اللعبة
socket.emit('start_game');

// تنفيذ إجراء
socket.emit('submit_action', {
    action_type: 'kill',
    target_id: 123
});

// التصويت
socket.emit('cast_vote', { target_id: 123 });
```

### الدردشة

```javascript
// إرسال رسالة
socket.emit('send_message', {
    content: 'مرحبا بالجميع!',
    message_type: 'text'
});

// إرسال رسالة صوتية
socket.emit('voice_message', {
    audio_data: 'base64_encoded_audio',
    duration: 5.2
});
```

## 🤖 الذكاء الاصطناعي

### تحليل الرسائل

النظام يحلل تلقائياً:
- كشف الأدوار في الدردشة
- المحتوى غير المناسب
- محاولات التواصل الخارجي
- التلاعب في التصويت
- تخريب اللعبة

### تحويل الصوت إلى نص

```python
# يتم تلقائياً عند إرسال رسائل صوتية
transcription = speech_to_text.transcribe(audio_file_path)
```

### تحليل الأداء

```python
# تحليل أداء لاعب
analysis = game_analyzer.analyze_player_behavior(player_id, game_id)

# تقرير شامل للاعب
report = stats_analyzer.generate_player_report(user_id)
```

## 🎭 الأدوار في اللعبة

### 👥 المواطنون

1. **مواطن عادي** - يصوت لإعدام المافيا
2. **طبيب** - يحمي لاعباً واحداً كل ليلة
3. **محقق** - يتحقق من هوية لاعب كل ليلة
4. **عدالة شعبية** - يقتل لاعباً واحداً كل ليلة
5. **عمدة** - صوته يحسب بصوتين
6. **مهرج** - يفوز إذا تم إعدامه

### 🖤 المافيا

- **مافيا** - يقتل المواطنين ليلاً ويحاول البقاء مخفياً

## 📊 نظام الإحصائيات

### إحصائيات شخصية

- إجمالي الألعاب والانتصارات
- معدل البقاء
- أداء كل دور
- دقة التصويت
- تحليل السلوك

### إحصائيات متقدمة

- اتجاهات الأداء
- التحليل النفسي
- نصائح للتحسين
- مقارنة مع اللاعبين الآخرين

## 🛡️ الأمان ومكافحة الغش

### الكشف التلقائي

- تحليل المحادثات بالذكاء الاصطناعي
- كشف كشف الأدوار
- مراقبة التواصل الخارجي
- تتبع الأنماط المشبوهة

### الإجراءات التلقائية

- إخفاء الرسائل المخالفة
- تحذيرات للمشرفين
- نقاط الشك للاعبين

## 🔧 التطوير والمساهمة

### إضافة دور جديد

1. تحديث `PlayerRole` في `models/player.py`
2. إضافة منطق الدور في `game/role_manager.py`
3. تحديث توزيع الأدوار في `RoleDistribution`

### إضافة تحليل جديد

1. تحديث `MessageAnalyzer` في `ai/message_analyzer.py`
2. إضافة أنماط جديدة في `suspicious_patterns`
3. تحديث منطق التحليل

## 🐛 استكشاف الأخطاء

### مشاكل شائعة

1. **خطأ في الاتصال بقاعدة البيانات**
   ```
   تأكد من تشغيل MySQL وصحة إعدادات الاتصال في .env
   ```

2. **فشل في تحويل الصوت إلى نص**
   ```
   تأكد من صحة مفتاح OpenAI API
   ```

3. **مشاكل في WebSocket**
   ```
   تأكد من عدم حجب المنافذ والسماح للاتصالات
   ```

### سجلات النظام

```bash
# مراقبة السجلات
tail -f app.log

# فحص حالة النظام
curl http://localhost:5000/health
```

## 📝 الترخيص

هذا المشروع مفتوح المصدر ومتاح للاستخدام التعليمي والتجاري.

## 🤝 الدعم والمساهمة

للإبلاغ عن مشاكل أو طلب ميزات جديدة، يرجى إنشاء issue في المستودع.

---

**تم تطوير هذا المشروع بـ ❤️ باللغة العربية بواسطة نصر الدين**

*آخر تحديث: 26 يوليوز 2025*