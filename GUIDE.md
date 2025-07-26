# 🎮 الدليل الشامل للعبة المافيا

## 🚀 البدء السريع (3 خطوات)

### 1. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 2. تشغيل التطبيق
```bash
python main.py
```

### 3. اختبار التطبيق
افتح المتصفح واذهب إلى: `http://localhost:5000`

---

## 🎯 اختبار شامل للعبة

### خطوة 1: اختبار API
```bash
# فحص صحة الخادم
curl http://localhost:5000/health

# الحصول على معلومات API
curl http://localhost:5000/api/info

# تسجيل دخول بحساب تجريبي  
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"احمد","password":"test123"}'
```

### خطوة 2: إنشاء غرفة
```bash
# إنشاء غرفة جديدة (يجب تسجيل الدخول أولاً)
curl -X POST http://localhost:5000/api/room/create \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "غرفة تجريبية",
    "max_players": 8,
    "min_players": 4,
    "allow_voice_chat": true
  }'
```

### خطوة 3: اختبار WebSocket
```javascript
// اتصال WebSocket
const socket = io('http://localhost:5000');

// الانضمام لغرفة
socket.emit('join_room', {
    room_code: 'ABC123'
});

// إرسال رسالة
socket.emit('send_message', {
    content: 'مرحبا بالجميع!',
    message_type: 'text'
});

// استلام الرسائل
socket.on('new_message', (data) => {
    console.log('رسالة جديدة:', data);
});
```

---

## 🎭 دليل اللعب الكامل

### الأدوار في اللعبة

#### 👥 المواطنون (الخير)
- **مواطن عادي**: يصوت في النهار لإعدام المشبوهين
- **طبيب**: يحمي لاعباً واحداً كل ليلة من القتل
- **محقق**: يتحقق من هوية لاعب واحد كل ليلة  
- **عدالة شعبية**: يمكنه قتل لاعب واحد كل ليلة
- **عمدة**: صوته يحسب بصوتين في التصويت
- **مهرج**: يفوز وحده إذا تم إعدامه نهاراً

#### 🖤 المافيا (الشر)
- **مافيا**: يقتل المواطنين ليلاً ويحاول البقاء مخفياً نهاراً

### مراحل اللعبة

#### 🌙 الليل
- المافيا تختار ضحية للقتل
- الطبيب يختار شخصاً لحمايته
- المحقق يتحقق من هوية لاعب
- العدالة الشعبية يختار هدفاً للقتل

#### ☀️ النهار  
- الكشف عن ضحايا الليل
- نقاش حر بين اللاعبين
- تحليل الأحداث والاشتباه

#### 🗳️ التصويت
- كل لاعب يصوت لشخص واحد للإعدام
- اللاعب الأكثر أصواتاً يتم إعدامه
- في حالة التعادل، لا يُعدم أحد

### شروط الفوز

#### 🏆 فوز المواطنين
- قتل جميع أعضاء المافيا

#### 🏆 فوز المافيا  
- أن يصبح عددهم مساوياً أو أكثر من المواطنين

#### 🏆 فوز المهرج
- أن يتم إعدامه بالتصويت نهاراً

---

## 🤖 ميزات الذكاء الاصطناعي

### كشف الغش التلقائي
```json
{
  "suspicious_patterns": [
    "كشف الأدوار في الدردشة",
    "التواصل خارج اللعبة", 
    "معلومات لا يجب معرفتها",
    "تسريب استراتيجيات"
  ],
  "actions": [
    "إخفاء الرسالة",
    "تحذير المشرفين",
    "رفع مؤشر الشك"
  ]
}
```

### تحليل الأداء
```bash
# الحصول على تقرير اللاعب
curl http://localhost:5000/api/stats/my-stats

# تحليل لعبة معينة  
curl http://localhost:5000/api/stats/analyze-game/123

# الحصول على تقرير ذكي
curl http://localhost:5000/api/stats/ai-report/456
```

### تحويل الصوت إلى نص
```javascript
// إرسال رسالة صوتية
socket.emit('voice_message', {
    audio_data: base64AudioData,
    duration: 5.2,
    format: 'wav'
});

// استلام النص المحول
socket.on('voice_transcribed', (data) => {
    console.log('النص:', data.transcription);
    console.log('تحليل AI:', data.ai_analysis);
});
```

---

## 🔧 إعداد متقدم

### قاعدة بيانات MySQL
```env
# في ملف .env
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mafia_game
```

### الذكاء الاصطناعي
```env
# مفتاح OpenAI للذكاء الاصطناعي
OPENAI_API_KEY=sk-your-key-here
```

### إعدادات اللعبة
```env
# حد اللاعبين
MIN_PLAYERS=4
MAX_PLAYERS=20

# أوقات المراحل (بالثواني)
GAME_TIME_LIMIT=300  # 5 دقائق
VOTE_TIME_LIMIT=60   # دقيقة
```

---

## 📊 مراقبة النظام

### إحصائيات مباشرة
```bash
# فحص صحة النظام
curl http://localhost:5000/health

# إحصائيات عامة
curl http://localhost:5000/api/stats/global

# الألعاب النشطة
curl http://localhost:5000/api/game/active
```

### مراقبة السجلات
```bash
# عرض السجلات
tail -f logs/app.log

# البحث عن أخطاء
grep "ERROR" logs/app.log

# مراقبة الذكاء الاصطناعي
grep "AI" logs/app.log
```

---

## 🐛 حل المشاكل

### مشاكل شائعة

#### 1. خطأ في قاعدة البيانات
```bash
# إعادة إنشاء قاعدة البيانات
python setup_database.py reset

# أو استخدام SQLite مؤقتاً
echo "DATABASE_TYPE=sqlite" >> .env
```

#### 2. مشكلة في المتطلبات
```bash
# تحديث pip
python -m pip install --upgrade pip

# إعادة تثبيت المتطلبات
pip install -r requirements.txt --force-reinstall
```

#### 3. مشكلة في الذكاء الاصطناعي
```bash
# تعطيل الذكاء الاصطناعي مؤقتاً
# احذف أو علق OPENAI_API_KEY في .env
```

#### 4. مشكلة في المنفذ
```bash
# استخدام منفذ مختلف
echo "PORT=5001" >> .env
```

### التحقق من الأخطاء
```python
# اختبار سريع للمكونات
python -c "
from models import db, User
from game import GameManager
from ai import MessageAnalyzer
print('✅ جميع المكونات تعمل')
"
```

---

## 🎉 أمثلة عملية

### إنشاء لعبة كاملة
```python
from examples.api_usage import MafiaGameAPI

# إنشاء عميل API
api = MafiaGameAPI()

# تسجيل الدخول
api.login("احمد", "test123")

# إنشاء غرفة  
api.create_room("غرفة الأصدقاء", max_players=6)

# دعوة أصدقاء للانضمام
print(f"رمز الغرفة: {api.current_room['room_code']}")

# بدء اللعبة عند اكتمال اللاعبين
api.start_game()
```

### مراقبة لعبة
```python
# تحليل أداء لاعب
from ai import GameAnalyzer
analyzer = GameAnalyzer("your-openai-key")
analysis = analyzer.analyze_player_behavior(123, 456)
print("تحليل اللاعب:", analysis)

# إحصائيات شاملة
from ai import StatsAnalyzer  
stats = StatsAnalyzer("your-openai-key")
report = stats.generate_player_report(123)
print("تقرير اللاعب:", report)
```

---

## 🌟 نصائح للمطورين

### إضافة دور جديد
```python
# في models/player.py
class PlayerRole(Enum):
    # ... الأدوار الموجودة
    NEW_ROLE = "new_role"

# في game/role_manager.py  
def distribute_roles(self, players):
    # ... منطق توزيع الأدوار الجديد
```

### إضافة تحليل ذكي جديد
```python
# في ai/message_analyzer.py
def new_analysis_method(self, message):
    # منطق التحليل الجديد
    return analysis_result
```

### إضافة API جديد
```python
# في api/new_routes.py
from flask import Blueprint
new_bp = Blueprint('new', __name__)

@new_bp.route('/endpoint', methods=['POST'])
def new_endpoint():
    return {'success': True}
```

---

## 📞 الدعم والمساعدة

### موارد إضافية
- 📖 الوثائق الكاملة: [README.md](README.md)
- 🛠️ دليل التثبيت: [INSTALL.md](INSTALL.md) 
- 🚀 البداية السريعة: [START_HERE.md](START_HERE.md)
- 💻 أمثلة الكود: [examples/](examples/)

### في حالة المشاكل
1. ✅ تحقق من [troubleshooting](#-حل-المشاكل)
2. ✅ راجع السجلات والأخطاء
3. ✅ جرب الإعداد الأساسي مع SQLite
4. ✅ تأكد من إصدار Python (3.8+)

---

**🎭 استمتع بلعب المافيا! 🎉**