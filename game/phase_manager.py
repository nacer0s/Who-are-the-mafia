#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير المراحل
Phase Manager
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from models.game import GamePhase
from models.player import Player, PlayerRole

class PhaseAction:
    """إجراء في مرحلة معينة"""
    
    def __init__(self, player_id: int, action_type: str, target_id: int = None, details: dict = None):
        self.player_id = player_id
        self.action_type = action_type
        self.target_id = target_id
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        self.is_processed = False

class PhaseTimer:
    """مؤقت المرحلة"""
    
    def __init__(self, duration: int, callback: Callable = None):
        self.duration = duration
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + timedelta(seconds=duration)
        self.callback = callback
        self.timer = None
        self.is_active = True
        
        if callback and duration > 0:
            self.timer = threading.Timer(duration, self._on_timeout)
            self.timer.daemon = True
            self.timer.start()
    
    def _on_timeout(self):
        """معالج انتهاء الوقت"""
        if self.is_active and self.callback:
            self.callback()
    
    def get_remaining_time(self) -> int:
        """الحصول على الوقت المتبقي"""
        if not self.is_active:
            return 0
        
        remaining = (self.end_time - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
    
    def is_expired(self) -> bool:
        """التحقق من انتهاء الوقت"""
        return datetime.utcnow() >= self.end_time
    
    def cancel(self):
        """إلغاء المؤقت"""
        self.is_active = False
        if self.timer:
            self.timer.cancel()
    
    def extend(self, additional_seconds: int):
        """تمديد الوقت"""
        if self.is_active:
            self.end_time += timedelta(seconds=additional_seconds)
            # إعادة إنشاء المؤقت
            if self.timer:
                self.timer.cancel()
                remaining = self.get_remaining_time()
                if remaining > 0 and self.callback:
                    self.timer = threading.Timer(remaining, self._on_timeout)
                    self.timer.daemon = True
                    self.timer.start()

class PhaseManager:
    """مدير مراحل اللعبة"""
    
    # مدد المراحل الافتراضية (بالثانية)
    DEFAULT_PHASE_DURATIONS = {
        GamePhase.DAY: 300,      # 5 دقائق للنقاش
        GamePhase.VOTING: 60,    # دقيقة للتصويت
        GamePhase.NIGHT: 120,    # دقيقتان لأعمال الليل
        GamePhase.TRIAL: 180     # 3 دقائق للمحاكمة
    }
    
    def __init__(self, game_id: int, on_phase_change: Callable = None):
        self.game_id = game_id
        self.on_phase_change = on_phase_change
        
        self.current_phase = GamePhase.DAY
        self.phase_timer: Optional[PhaseTimer] = None
        self.phase_actions: Dict[int, PhaseAction] = {}  # player_id -> action
        self.phase_start_time = datetime.utcnow()
        
        self._lock = threading.Lock()
        self.is_active = True
        
        # معالجات المراحل
        self.phase_handlers = {
            GamePhase.DAY: self._handle_day_phase,
            GamePhase.VOTING: self._handle_voting_phase,
            GamePhase.NIGHT: self._handle_night_phase,
            GamePhase.TRIAL: self._handle_trial_phase
        }
    
    def start_phase(self, phase: GamePhase, duration: int = None, **kwargs) -> bool:
        """بدء مرحلة جديدة"""
        
        with self._lock:
            if not self.is_active:
                return False
            
            # إنهاء المرحلة الحالية
            self._cleanup_current_phase()
            
            # تعيين المرحلة الجديدة
            self.current_phase = phase
            self.phase_start_time = datetime.utcnow()
            self.phase_actions.clear()
            
            # تحديد مدة المرحلة
            if duration is None:
                duration = self.DEFAULT_PHASE_DURATIONS.get(phase, 300)
            
            # إنشاء مؤقت المرحلة
            if duration > 0:
                self.phase_timer = PhaseTimer(
                    duration, 
                    lambda: self._on_phase_timeout()
                )
            
            # تشغيل معالج المرحلة
            handler = self.phase_handlers.get(phase)
            if handler:
                handler(**kwargs)
            
            # إشعار بتغيير المرحلة
            if self.on_phase_change:
                try:
                    self.on_phase_change(phase, duration, **kwargs)
                except Exception as e:
                    print(f"خطأ في معالج تغيير المرحلة: {e}")
            
            return True
    
    def _cleanup_current_phase(self):
        """تنظيف المرحلة الحالية"""
        if self.phase_timer:
            self.phase_timer.cancel()
            self.phase_timer = None
    
    def _on_phase_timeout(self):
        """معالج انتهاء وقت المرحلة"""
        with self._lock:
            if not self.is_active:
                return
            
            print(f"انتهى وقت مرحلة {self.current_phase.value}")
            
            # معالجة انتهاء الوقت حسب المرحلة
            if self.current_phase == GamePhase.DAY:
                # الانتقال للتصويت
                self.start_phase(GamePhase.VOTING)
            
            elif self.current_phase == GamePhase.VOTING:
                # إنهاء التصويت والانتقال للليل أو النهار
                self._process_voting_results()
            
            elif self.current_phase == GamePhase.NIGHT:
                # معالجة أعمال الليل والانتقال للنهار
                self._process_night_actions()
                self.start_phase(GamePhase.DAY)
            
            elif self.current_phase == GamePhase.TRIAL:
                # انتهاء المحاكمة
                self._process_trial_results()
    
    def submit_action(self, player_id: int, action_type: str, target_id: int = None, **details) -> tuple[bool, str]:
        """تقديم إجراء في المرحلة الحالية"""
        
        with self._lock:
            if not self.is_active:
                return False, "اللعبة غير نشطة"
            
            # التحقق من صحة الإجراء
            is_valid, message = self._validate_action(player_id, action_type, target_id)
            if not is_valid:
                return False, message
            
            # حفظ الإجراء
            action = PhaseAction(player_id, action_type, target_id, details)
            self.phase_actions[player_id] = action
            
            return True, "تم تسجيل الإجراء"
    
    def _validate_action(self, player_id: int, action_type: str, target_id: int = None) -> tuple[bool, str]:
        """التحقق من صحة الإجراء"""
        
        # الحصول على اللاعب
        player = Player.query.get(player_id)
        if not player or not player.is_alive:
            return False, "اللاعب غير موجود أو ميت"
        
        # التحقق من الإجراءات المسموحة في كل مرحلة
        if self.current_phase == GamePhase.DAY:
            # في النهار: يمكن التحدث فقط
            allowed_actions = ["speak", "accuse", "defend"]
            if action_type not in allowed_actions:
                return False, "إجراء غير مسموح في النهار"
        
        elif self.current_phase == GamePhase.VOTING:
            # في التصويت: يمكن التصويت فقط
            if action_type != "vote":
                return False, "يمكن التصويت فقط في هذه المرحلة"
        
        elif self.current_phase == GamePhase.NIGHT:
            # في الليل: إجراءات الأدوار الخاصة
            role_actions = {
                PlayerRole.MAFIA: ["kill"],
                PlayerRole.DOCTOR: ["heal"],
                PlayerRole.DETECTIVE: ["investigate"],
                PlayerRole.VIGILANTE: ["vigilante_kill"]
            }
            
            allowed_actions = role_actions.get(player.role, [])
            if action_type not in allowed_actions:
                return False, "إجراء غير مسموح لدورك في الليل"
            
            # التحقق من الهدف
            if target_id:
                target = Player.query.get(target_id)
                if not target or not target.is_alive:
                    return False, "الهدف غير موجود أو ميت"
                
                if target_id == player_id:
                    return False, "لا يمكن استهداف نفسك"
                
                # قواعد خاصة للمافيا
                if action_type == "kill" and target.role == PlayerRole.MAFIA:
                    return False, "لا يمكن قتل أفراد المافيا"
        
        return True, "إجراء صحيح"
    
    def _handle_day_phase(self, **kwargs):
        """معالج مرحلة النهار"""
        print(f"بدأت مرحلة النهار - مدة: {self.phase_timer.duration if self.phase_timer else 0} ثانية")
        
        # في النهار يمكن للاعبين التحدث والنقاش
        # لا توجد إجراءات خاصة مطلوبة
    
    def _handle_voting_phase(self, **kwargs):
        """معالج مرحلة التصويت"""
        print(f"بدأت مرحلة التصويت - مدة: {self.phase_timer.duration if self.phase_timer else 0} ثانية")
        
        # سيتم التعامل مع التصويت عبر VotingManager
    
    def _handle_night_phase(self, **kwargs):
        """معالج مرحلة الليل"""
        print(f"بدأت مرحلة الليل - مدة: {self.phase_timer.duration if self.phase_timer else 0} ثانية")
        
        # في الليل، الأدوار الخاصة تأخذ أعمالها
        # المافيا يقتل، الطبيب يعالج، المحقق يتحقق
    
    def _handle_trial_phase(self, **kwargs):
        """معالج مرحلة المحاكمة"""
        print(f"بدأت مرحلة المحاكمة - مدة: {self.phase_timer.duration if self.phase_timer else 0} ثانية")
        
        # مرحلة محاكمة اللاعب المتهم
        accused_player_id = kwargs.get('accused_player_id')
        if accused_player_id:
            print(f"محاكمة اللاعب: {accused_player_id}")
    
    def _process_voting_results(self):
        """معالجة نتائج التصويت"""
        # سيتم التعامل مع هذا عبر VotingManager و GameManager
        print("معالجة نتائج التصويت...")
    
    def _process_night_actions(self):
        """معالجة أعمال الليل"""
        print("معالجة أعمال الليل...")
        
        # تجميع الأعمال حسب النوع
        kills = []
        heals = []
        investigations = []
        vigilante_kills = []
        
        for action in self.phase_actions.values():
            if action.action_type == "kill":
                kills.append(action)
            elif action.action_type == "heal":
                heals.append(action)
            elif action.action_type == "investigate":
                investigations.append(action)
            elif action.action_type == "vigilante_kill":
                vigilante_kills.append(action)
        
        # معالجة الأعمال بالترتيب المناسب
        results = {
            'kills': self._process_kills(kills, heals),
            'heals': self._process_heals(heals),
            'investigations': self._process_investigations(investigations),
            'vigilante_kills': self._process_vigilante_kills(vigilante_kills, heals)
        }
        
        return results
    
    def _process_kills(self, kills: List[PhaseAction], heals: List[PhaseAction]) -> List[Dict]:
        """معالجة عمليات القتل"""
        results = []
        
        # تجميع الأهداف المحمية
        protected_targets = {heal.target_id for heal in heals}
        
        for kill in kills:
            target_id = kill.target_id
            target = Player.query.get(target_id)
            
            if target and target.is_alive:
                if target_id in protected_targets:
                    # الهدف محمي
                    results.append({
                        'action': 'kill_blocked',
                        'killer_id': kill.player_id,
                        'target_id': target_id,
                        'message': f'تم حماية {target.user.display_name} من القتل'
                    })
                else:
                    # قتل ناجح
                    target.kill('mafia_kill', kill.player_id)
                    results.append({
                        'action': 'kill_success',
                        'killer_id': kill.player_id,
                        'target_id': target_id,
                        'message': f'تم قتل {target.user.display_name}'
                    })
        
        return results
    
    def _process_heals(self, heals: List[PhaseAction]) -> List[Dict]:
        """معالجة عمليات العلاج"""
        results = []
        
        for heal in heals:
            target_id = heal.target_id
            target = Player.query.get(target_id)
            
            if target:
                results.append({
                    'action': 'heal',
                    'healer_id': heal.player_id,
                    'target_id': target_id,
                    'message': f'تم حماية {target.user.display_name}'
                })
        
        return results
    
    def _process_investigations(self, investigations: List[PhaseAction]) -> List[Dict]:
        """معالجة التحقيقات"""
        results = []
        
        for investigation in investigations:
            target_id = investigation.target_id
            target = Player.query.get(target_id)
            
            if target:
                is_mafia = target.role == PlayerRole.MAFIA
                results.append({
                    'action': 'investigate',
                    'investigator_id': investigation.player_id,
                    'target_id': target_id,
                    'result': 'mafia' if is_mafia else 'citizen',
                    'message': f'{target.user.display_name} {"من المافيا" if is_mafia else "مواطن بريء"}'
                })
        
        return results
    
    def _process_vigilante_kills(self, vigilante_kills: List[PhaseAction], heals: List[PhaseAction]) -> List[Dict]:
        """معالجة قتل العدالة الشعبية"""
        results = []
        
        # تجميع الأهداف المحمية
        protected_targets = {heal.target_id for heal in heals}
        
        for kill in vigilante_kills:
            target_id = kill.target_id
            target = Player.query.get(target_id)
            
            if target and target.is_alive:
                if target_id in protected_targets:
                    # الهدف محمي
                    results.append({
                        'action': 'vigilante_kill_blocked',
                        'killer_id': kill.player_id,
                        'target_id': target_id,
                        'message': f'تم حماية {target.user.display_name} من العدالة الشعبية'
                    })
                else:
                    # قتل ناجح
                    target.kill('vigilante_kill', kill.player_id)
                    results.append({
                        'action': 'vigilante_kill_success',
                        'killer_id': kill.player_id,
                        'target_id': target_id,
                        'message': f'قتلت العدالة الشعبية {target.user.display_name}'
                    })
        
        return results
    
    def _process_trial_results(self):
        """معالجة نتائج المحاكمة"""
        print("معالجة نتائج المحاكمة...")
    
    def get_phase_info(self) -> Dict:
        """الحصول على معلومات المرحلة الحالية"""
        return {
            'phase': self.current_phase.value,
            'start_time': self.phase_start_time.isoformat(),
            'remaining_time': self.phase_timer.get_remaining_time() if self.phase_timer else 0,
            'duration': self.phase_timer.duration if self.phase_timer else 0,
            'actions_submitted': len(self.phase_actions),
            'is_active': self.is_active
        }
    
    def get_player_action(self, player_id: int) -> Optional[Dict]:
        """الحصول على إجراء اللاعب في المرحلة الحالية"""
        action = self.phase_actions.get(player_id)
        if action:
            return {
                'action_type': action.action_type,
                'target_id': action.target_id,
                'details': action.details,
                'timestamp': action.timestamp.isoformat()
            }
        return None
    
    def extend_phase(self, additional_seconds: int) -> bool:
        """تمديد المرحلة الحالية"""
        if self.phase_timer and self.is_active:
            self.phase_timer.extend(additional_seconds)
            return True
        return False
    
    def force_end_phase(self) -> bool:
        """إنهاء المرحلة بالقوة"""
        if self.phase_timer and self.is_active:
            self.phase_timer.cancel()
            self._on_phase_timeout()
            return True
        return False
    
    def stop(self):
        """إيقاف مدير المراحل"""
        self.is_active = False
        self._cleanup_current_phase()
    
    def __del__(self):
        """تنظيف الموارد"""
        self.stop()