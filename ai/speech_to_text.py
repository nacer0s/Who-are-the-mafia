#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحويل الصوت إلى نص
Speech to Text Converter
"""

import os
from typing import Optional
import tempfile

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class SpeechToText:
    """محول الصوت إلى نص باستخدام OpenAI Whisper"""
    
    def __init__(self, openai_api_key: str = None):
        """إنشاء محول الصوت إلى نص"""
        self.openai_available = OPENAI_AVAILABLE and openai_api_key
        
        if self.openai_available:
            try:
                if hasattr(openai, 'OpenAI'):
                    self.client = openai.OpenAI(api_key=openai_api_key)
                else:
                    openai.api_key = openai_api_key
                    self.client = openai
            except Exception as e:
                print(f"⚠️ فشل في تهيئة OpenAI للصوت: {e}")
                self.openai_available = False
        
        # الإعدادات
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
        self.max_file_size = 25 * 1024 * 1024  # 25 MB
        self.language = 'ar'  # اللغة العربية
    
    def transcribe(self, audio_file_path: str, language: str = 'ar') -> Optional[str]:
        """تحويل ملف صوتي إلى نص"""
        
        if not self.openai_available:
            print("⚠️ OpenAI غير متاح للتحويل الصوتي")
            return "[تعذر تحويل الرسالة الصوتية]"
        
        try:
            # التحقق من وجود الملف
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"الملف الصوتي غير موجود: {audio_file_path}")
            
            # التحقق من حجم الملف
            file_size = os.path.getsize(audio_file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"حجم الملف كبير جداً: {file_size / (1024*1024):.1f} MB")
            
            # التحقق من صيغة الملف
            file_extension = os.path.splitext(audio_file_path)[1].lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"صيغة الملف غير مدعومة: {file_extension}")
            
            # تحويل الصوت إلى نص
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
            
            # تنظيف النص
            cleaned_text = self._clean_transcription(transcript)
            
            return cleaned_text
            
        except Exception as e:
            print(f"خطأ في تحويل الصوت إلى نص: {e}")
            return None
    
    def transcribe_with_timestamps(self, audio_file_path: str, language: str = 'ar') -> Optional[dict]:
        """تحويل الصوت إلى نص مع الطوابع الزمنية"""
        try:
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"الملف الصوتي غير موجود: {audio_file_path}")
            
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            
            return {
                'text': self._clean_transcription(transcript.text),
                'language': transcript.language,
                'duration': transcript.duration,
                'words': transcript.words if hasattr(transcript, 'words') else [],
                'segments': transcript.segments if hasattr(transcript, 'segments') else []
            }
            
        except Exception as e:
            print(f"خطأ في تحويل الصوت إلى نص مع الطوابع الزمنية: {e}")
            return None
    
    def _clean_transcription(self, text: str) -> str:
        """تنظيف النص المحول"""
        if not text:
            return ""
        
        # إزالة المسافات الزائدة
        cleaned = ' '.join(text.split())
        
        # إزالة الأصوات التقليدية (um, uh, etc.)
        filler_words = ['أه', 'أم', 'إيه', 'يعني', 'أي', 'ممم']
        words = cleaned.split()
        words = [word for word in words if word not in filler_words]
        
        cleaned = ' '.join(words)
        
        # تصحيح علامات الترقيم
        cleaned = cleaned.replace(' ,', ',').replace(' .', '.')
        cleaned = cleaned.replace(' ؟', '؟').replace(' !', '!')
        
        return cleaned.strip()
    
    def detect_language(self, audio_file_path: str) -> Optional[str]:
        """اكتشاف لغة الملف الصوتي"""
        try:
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"الملف الصوتي غير موجود: {audio_file_path}")
            
            with open(audio_file_path, 'rb') as audio_file:
                # استخدام نموذج Whisper لاكتشاف اللغة
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            return transcript.language if hasattr(transcript, 'language') else None
            
        except Exception as e:
            print(f"خطأ في اكتشاف اللغة: {e}")
            return None
    
    def transcribe_chunk(self, audio_chunk: bytes, format: str = 'wav') -> Optional[str]:
        """تحويل قطعة صوتية من الذاكرة إلى نص"""
        try:
            # إنشاء ملف مؤقت
            with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as temp_file:
                temp_file.write(audio_chunk)
                temp_file_path = temp_file.name
            
            try:
                # تحويل الملف المؤقت
                result = self.transcribe(temp_file_path)
                return result
            finally:
                # حذف الملف المؤقت
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"خطأ في تحويل القطعة الصوتية: {e}")
            return None
    
    def is_audio_file_valid(self, file_path: str) -> tuple[bool, str]:
        """التحقق من صحة الملف الصوتي"""
        try:
            # التحقق من وجود الملف
            if not os.path.exists(file_path):
                return False, "الملف غير موجود"
            
            # التحقق من حجم الملف
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "الملف فارغ"
            
            if file_size > self.max_file_size:
                return False, f"حجم الملف كبير جداً ({file_size / (1024*1024):.1f} MB)"
            
            # التحقق من صيغة الملف
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension not in self.supported_formats:
                return False, f"صيغة الملف غير مدعومة: {file_extension}"
            
            return True, "الملف صحيح"
            
        except Exception as e:
            return False, f"خطأ في فحص الملف: {str(e)}"
    
    def get_audio_duration(self, file_path: str) -> Optional[float]:
        """الحصول على مدة الملف الصوتي بالثواني"""
        try:
            # محاولة استخدام مكتبة mutagen للحصول على مدة الملف
            try:
                from mutagen import File
                audio_file = File(file_path)
                if audio_file and hasattr(audio_file, 'info'):
                    return audio_file.info.length
            except ImportError:
                print("مكتبة mutagen غير مثبتة، لا يمكن الحصول على مدة الملف")
                pass
            
            # كطريقة بديلة، استخدام Whisper للحصول على المدة
            result = self.transcribe_with_timestamps(file_path)
            if result and 'duration' in result:
                return result['duration']
            
            return None
            
        except Exception as e:
            print(f"خطأ في الحصول على مدة الملف: {e}")
            return None
    
    def batch_transcribe(self, file_paths: list) -> dict:
        """تحويل عدة ملفات صوتية إلى نص"""
        results = {}
        
        for file_path in file_paths:
            try:
                transcript = self.transcribe(file_path)
                results[file_path] = {
                    'success': True,
                    'transcript': transcript,
                    'error': None
                }
            except Exception as e:
                results[file_path] = {
                    'success': False,
                    'transcript': None,
                    'error': str(e)
                }
        
        return results
    
    def analyze_speech_quality(self, transcript_with_timestamps: dict) -> dict:
        """تحليل جودة الكلام"""
        if not transcript_with_timestamps or 'words' not in transcript_with_timestamps:
            return {
                'quality_score': 0.0,
                'issues': ['لا توجد بيانات كافية للتحليل']
            }
        
        words = transcript_with_timestamps.get('words', [])
        if not words:
            return {
                'quality_score': 0.0,
                'issues': ['لم يتم اكتشاف كلمات']
            }
        
        # تحليل السرعة
        duration = transcript_with_timestamps.get('duration', 0)
        word_count = len(words)
        words_per_minute = (word_count / duration * 60) if duration > 0 else 0
        
        # تحليل الوضوح (بناء على ثقة النموذج إن كانت متاحة)
        confidence_scores = []
        for word in words:
            if 'confidence' in word:
                confidence_scores.append(word['confidence'])
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.8
        
        # تحليل التردد والتوقف
        pauses = 0
        if len(words) > 1:
            for i in range(1, len(words)):
                if 'start' in words[i] and 'end' in words[i-1]:
                    pause_duration = words[i]['start'] - words[i-1]['end']
                    if pause_duration > 1.0:  # توقف أكثر من ثانية
                        pauses += 1
        
        # حساب نقاط الجودة
        quality_score = 0.0
        issues = []
        
        # سرعة الكلام
        if 80 <= words_per_minute <= 180:
            quality_score += 0.3
        else:
            if words_per_minute < 80:
                issues.append('الكلام بطيء جداً')
            else:
                issues.append('الكلام سريع جداً')
        
        # وضوح الكلام
        if avg_confidence > 0.8:
            quality_score += 0.4
        elif avg_confidence > 0.6:
            quality_score += 0.2
        else:
            issues.append('وضوح الكلام منخفض')
        
        # التردد والتوقف
        pause_ratio = pauses / word_count if word_count > 0 else 0
        if pause_ratio < 0.1:
            quality_score += 0.3
        elif pause_ratio < 0.2:
            quality_score += 0.1
        else:
            issues.append('توقفات كثيرة في الكلام')
        
        return {
            'quality_score': min(quality_score, 1.0),
            'words_per_minute': words_per_minute,
            'average_confidence': avg_confidence,
            'pause_ratio': pause_ratio,
            'total_words': word_count,
            'duration': duration,
            'issues': issues if issues else ['جودة الكلام جيدة']
        }