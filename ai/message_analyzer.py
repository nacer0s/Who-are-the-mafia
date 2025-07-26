#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محلل الرسائل بالذكاء الاصطناعي
AI Message Analyzer
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class MessageAnalyzer:
    """محلل الرسائل للكشف عن الغش والمحتوى المشبوه"""
    
    def __init__(self, openai_api_key: str = None):
        """إنشاء محلل الرسائل"""
        self.openai_available = OPENAI_AVAILABLE and openai_api_key
        
        if self.openai_available:
            try:
                # محاولة إنشاء العميل مع الإصدار الجديد
                if hasattr(openai, 'OpenAI'):
                    self.client = openai.OpenAI(api_key=openai_api_key)
                else:
                    # الإصدار القديم
                    openai.api_key = openai_api_key
                    self.client = openai
            except Exception as e:
                print(f"⚠️ فشل في تهيئة OpenAI: {e}")
                self.openai_available = False
        
        # قواعد الكشف عن المحتوى المشبوه
        self.suspicious_patterns = {
            'role_revealing': [
                r'أنا\s+(?:مافيا|طبيب|محقق|مواطن)',
                r'دوري\s+(?:مافيا|طبيب|محقق|مواطن)',
                r'أنا\s+من\s+المافيا',
                r'أنا\s+الطبيب',
                r'أنا\s+المحقق',
                r'role.*(?:mafia|doctor|detective|citizen)',
            ],
            'game_disruption': [
                r'(?:أخرجوا|اطردوا|احذفوا)\s+(?:من|اللعبة)',
                r'هذه\s+لعبة\s+غبية',
                r'لن\s+ألعب',
                r'سأغادر\s+اللعبة',
            ],
            'inappropriate_content': [
                r'(?:أحمق|غبي|حقير|لعين)',
                r'(?:كلب|حمار|بقرة)',
                r'اذهب\s+إلى\s+الجحيم',
            ],
            'external_communication': [
                r'(?:واتساب|تليجرام|ديسكورد|تيمز)',
                r'(?:whatsapp|telegram|discord|teams)',
                r'اتصل\s+بي',
                r'رسالة\s+خاصة',
            ],
            'vote_manipulation': [
                r'صوتوا\s+ضد\s+\w+\s+لأنه\s+مافيا',
                r'لا\s+تصوتوا\s+ضدي',
                r'أعرف\s+من\s+المافيا',
                r'صدقوني\s+(?:مافيا|بريء)',
            ]
        }
        
        # كلمات إيجابية وسلبية للتحليل العاطفي
        self.positive_words = [
            'ممتاز', 'رائع', 'جيد', 'مفيد', 'صحيح', 'موافق', 'أحب', 'أستمتع'
        ]
        
        self.negative_words = [
            'سيء', 'خطأ', 'غلط', 'مخطئ', 'أكره', 'ممل', 'صعب', 'مستحيل'
        ]
    
    def analyze_message(self, message_id: int, content: str, user_id: int, 
                       room_id: int, game_round: Optional[int] = None, 
                       game_phase: Optional[str] = None) -> Dict:
        """تحليل رسالة واحدة"""
        
        analysis = {
            'message_id': message_id,
            'user_id': user_id,
            'room_id': room_id,
            'game_round': game_round,
            'game_phase': game_phase,
            'timestamp': datetime.utcnow().isoformat(),
            'content_length': len(content),
            'is_suspicious': False,
            'suspicion_score': 0.0,
            'flags': [],
            'sentiment': 'neutral',
            'detected_patterns': [],
            'ai_analysis': None
        }
        
        try:
            # 1. تحليل الأنماط المشبوهة
            pattern_analysis = self._analyze_patterns(content)
            analysis.update(pattern_analysis)
            
            # 2. تحليل المشاعر
            sentiment_analysis = self._analyze_sentiment(content)
            analysis.update(sentiment_analysis)
            
            # 3. تحليل السياق
            context_analysis = self._analyze_context(content, game_phase)
            analysis.update(context_analysis)
            
            # 4. تحليل OpenAI (إذا كان المحتوى مشبوهاً)
            if analysis['suspicion_score'] > 0.3:
                ai_analysis = self._get_ai_analysis(content, game_phase)
                analysis['ai_analysis'] = ai_analysis
                
                # تحديث النتيجة بناء على تحليل الذكاء الاصطناعي
                if ai_analysis and ai_analysis.get('is_suspicious', False):
                    analysis['suspicion_score'] = max(
                        analysis['suspicion_score'],
                        ai_analysis.get('confidence', 0.5)
                    )
            
            # 5. تحديد الحالة النهائية
            analysis['is_suspicious'] = analysis['suspicion_score'] > 0.5
            
            return analysis
            
        except Exception as e:
            print(f"خطأ في تحليل الرسالة {message_id}: {e}")
            analysis['error'] = str(e)
            return analysis
    
    def _analyze_patterns(self, content: str) -> Dict:
        """تحليل الأنماط المشبوهة"""
        detected_patterns = []
        suspicion_score = 0.0
        flags = []
        
        content_lower = content.lower()
        
        for category, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    detected_patterns.append({
                        'category': category,
                        'pattern': pattern,
                        'severity': self._get_pattern_severity(category)
                    })
                    
                    # زيادة درجة الشك
                    severity_score = self._get_pattern_severity(category)
                    suspicion_score += severity_score
                    
                    # إضافة علم
                    flags.append({
                        'type': category,
                        'reason': self._get_pattern_reason(category),
                        'severity': severity_score
                    })
        
        return {
            'detected_patterns': detected_patterns,
            'suspicion_score': min(suspicion_score, 1.0),
            'flags': flags
        }
    
    def _analyze_sentiment(self, content: str) -> Dict:
        """تحليل المشاعر"""
        content_lower = content.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in content_lower)
        negative_count = sum(1 for word in self.negative_words if word in content_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # تحليل الانفعال الشديد
        exclamation_count = content.count('!')
        caps_ratio = sum(1 for c in content if c.isupper()) / len(content) if content else 0
        
        emotional_intensity = 0.0
        if exclamation_count > 3:
            emotional_intensity += 0.3
        if caps_ratio > 0.5 and len(content) > 10:
            emotional_intensity += 0.4
        
        return {
            'sentiment': sentiment,
            'positive_words_count': positive_count,
            'negative_words_count': negative_count,
            'emotional_intensity': emotional_intensity,
            'exclamation_count': exclamation_count,
            'caps_ratio': caps_ratio
        }
    
    def _analyze_context(self, content: str, game_phase: Optional[str]) -> Dict:
        """تحليل السياق"""
        context_flags = []
        context_score = 0.0
        
        # تحليل حسب مرحلة اللعبة
        if game_phase == 'night':
            # في الليل، الحديث عن الأعمال قد يكون مشبوهاً
            night_patterns = [
                r'سأقتل\s+\w+',
                r'سأعالج\s+\w+',
                r'سأتحقق\s+من\s+\w+',
            ]
            
            for pattern in night_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    context_flags.append({
                        'type': 'night_action_leak',
                        'reason': 'كشف عمل ليلي في الدردشة العامة'
                    })
                    context_score += 0.7
        
        elif game_phase == 'voting':
            # أثناء التصويت، تحليل محاولات التلاعب
            voting_patterns = [
                r'صوتوا\s+معي',
                r'لا\s+تصوتوا\s+ضدي',
                r'أعرف\s+الحقيقة',
            ]
            
            for pattern in voting_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    context_flags.append({
                        'type': 'vote_manipulation',
                        'reason': 'محاولة تلاعب في التصويت'
                    })
                    context_score += 0.4
        
        # تحليل طول الرسالة
        if len(content) > 500:
            context_flags.append({
                'type': 'excessive_length',
                'reason': 'رسالة طويلة جداً قد تكون محاولة إرباك'
            })
            context_score += 0.2
        
        return {
            'context_flags': context_flags,
            'context_suspicion_score': min(context_score, 1.0)
        }
    
    def _get_ai_analysis(self, content: str, game_phase: Optional[str] = None) -> Optional[Dict]:
        """الحصول على تحليل من OpenAI"""
        try:
            prompt = f"""
            أنت محلل ذكي للمحتوى في لعبة المافيا العربية. قم بتحليل الرسالة التالية:

            الرسالة: "{content}"
            مرحلة اللعبة: {game_phase or 'غير معروفة'}

            هل هذه الرسالة مشبوهة أو تحتوي على مخالفات؟

            تحقق من:
            1. كشف الأدوار
            2. التواصل الخارجي
            3. المحتوى غير المناسب
            4. محاولة تخريب اللعبة
            5. التلاعب في التصويت

            أجب بـ JSON:
            {{
                "is_suspicious": boolean,
                "confidence": float (0-1),
                "reasons": ["سبب1", "سبب2"],
                "severity": "low|medium|high",
                "recommendation": "نصيحة للمشرف"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "أنت محلل محتوى خبير في ألعاب المافيا العربية."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # محاولة تحويل الرد إلى JSON
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # إذا فشل التحويل، استخراج المعلومات يدوياً
                return {
                    'is_suspicious': 'مشبوه' in result or 'suspicious' in result.lower(),
                    'confidence': 0.5,
                    'reasons': ['تحليل الذكاء الاصطناعي'],
                    'severity': 'medium',
                    'recommendation': result[:100] + "..." if len(result) > 100 else result
                }
                
        except Exception as e:
            print(f"خطأ في تحليل OpenAI: {e}")
            return None
    
    def _get_pattern_severity(self, category: str) -> float:
        """تحديد شدة النمط"""
        severity_map = {
            'role_revealing': 0.8,  # خطير جداً
            'game_disruption': 0.6,  # خطير
            'inappropriate_content': 0.4,  # متوسط
            'external_communication': 0.7,  # خطير
            'vote_manipulation': 0.5  # متوسط إلى خطير
        }
        return severity_map.get(category, 0.3)
    
    def _get_pattern_reason(self, category: str) -> str:
        """الحصول على سبب النمط"""
        reason_map = {
            'role_revealing': 'كشف الدور في الدردشة',
            'game_disruption': 'محاولة تخريب اللعبة',
            'inappropriate_content': 'محتوى غير مناسب',
            'external_communication': 'محاولة التواصل خارج اللعبة',
            'vote_manipulation': 'محاولة التلاعب في التصويت'
        }
        return reason_map.get(category, 'محتوى مشبوه')
    
    def analyze_voice_message(self, message_id: int, transcription: str, 
                            voice_file_path: str, user_id: int, room_id: int,
                            game_round: Optional[int] = None, 
                            game_phase: Optional[str] = None) -> Dict:
        """تحليل رسالة صوتية"""
        
        # تحليل النص المحول
        text_analysis = self.analyze_message(
            message_id, transcription, user_id, room_id, 
            game_round, game_phase
        )
        
        # إضافة تحليل خاص بالصوت
        voice_analysis = {
            'message_type': 'voice',
            'voice_file_path': voice_file_path,
            'transcription_length': len(transcription),
            'voice_specific_flags': []
        }
        
        # فحص جودة التحويل
        if len(transcription) < 10:
            voice_analysis['voice_specific_flags'].append({
                'type': 'poor_transcription',
                'reason': 'النص المحول قصير جداً، قد يكون التحويل غير دقيق'
            })
        
        # دمج التحليلين
        text_analysis.update(voice_analysis)
        text_analysis['analysis_type'] = 'voice_message'
        
        return text_analysis
    
    def get_user_suspicion_trends(self, user_id: int, recent_messages: List[Dict]) -> Dict:
        """تحليل اتجاهات الشك للمستخدم"""
        
        if not recent_messages:
            return {
                'user_id': user_id,
                'trend': 'no_data',
                'average_suspicion': 0.0,
                'message_count': 0
            }
        
        suspicion_scores = [msg.get('suspicion_score', 0.0) for msg in recent_messages]
        flags_count = sum(1 for msg in recent_messages if msg.get('is_suspicious', False))
        
        average_suspicion = sum(suspicion_scores) / len(suspicion_scores)
        
        # تحديد الاتجاه
        if len(suspicion_scores) >= 3:
            recent_avg = sum(suspicion_scores[-3:]) / 3
            earlier_avg = sum(suspicion_scores[:-3]) / len(suspicion_scores[:-3]) if len(suspicion_scores) > 3 else 0
            
            if recent_avg > earlier_avg + 0.2:
                trend = 'increasing'
            elif recent_avg < earlier_avg - 0.2:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'user_id': user_id,
            'trend': trend,
            'average_suspicion': average_suspicion,
            'message_count': len(recent_messages),
            'flagged_messages': flags_count,
            'flag_ratio': flags_count / len(recent_messages) if recent_messages else 0,
            'recommendation': self._get_user_recommendation(average_suspicion, flags_count, len(recent_messages))
        }
    
    def _get_user_recommendation(self, avg_suspicion: float, flags_count: int, total_messages: int) -> str:
        """توصية للمشرف حول المستخدم"""
        
        flag_ratio = flags_count / total_messages if total_messages > 0 else 0
        
        if avg_suspicion > 0.7 and flag_ratio > 0.5:
            return "مراقبة مشددة - مستخدم عالي الخطورة"
        elif avg_suspicion > 0.5 and flag_ratio > 0.3:
            return "مراقبة عادية - مستخدم متوسط الخطورة"
        elif avg_suspicion > 0.3:
            return "مراقبة خفيفة - بعض السلوكيات المشبوهة"
        else:
            return "لا يحتاج مراقبة خاصة"