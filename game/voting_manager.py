#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير التصويت
Voting Manager
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from models import db
from models.player import Player, PlayerRole

class Vote:
    """كلاس يمثل صوت واحد"""
    
    def __init__(self, voter_id: int, target_id: int, vote_weight: int = 1):
        self.voter_id = voter_id
        self.target_id = target_id
        self.vote_weight = vote_weight  # للعمدة (صوتين)
        self.timestamp = datetime.utcnow()

class VotingSession:
    """جلسة تصويت"""
    
    def __init__(self, session_id: str, room_id: int, vote_type: str = "lynch", duration: int = 60):
        self.session_id = session_id
        self.room_id = room_id
        self.vote_type = vote_type  # "lynch", "skip", "custom"
        self.duration = duration
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + timedelta(seconds=duration)
        
        self.votes: Dict[int, Vote] = {}  # voter_id -> Vote
        self.vote_counts: Dict[int, int] = defaultdict(int)  # target_id -> vote_count
        self.eligible_voters: List[int] = []
        self.eligible_targets: List[int] = []
        
        self.is_active = True
        self.is_completed = False
        self.result = None
        
        self._lock = threading.Lock()
    
    def add_eligible_voter(self, player_id: int):
        """إضافة لاعب مؤهل للتصويت"""
        if player_id not in self.eligible_voters:
            self.eligible_voters.append(player_id)
    
    def add_eligible_target(self, player_id: int):
        """إضافة هدف مؤهل للتصويت عليه"""
        if player_id not in self.eligible_targets:
            self.eligible_targets.append(player_id)
    
    def can_vote(self, voter_id: int) -> bool:
        """التحقق من إمكانية التصويت"""
        return (self.is_active and 
                not self.is_expired() and 
                voter_id in self.eligible_voters)
    
    def can_be_voted_for(self, target_id: int) -> bool:
        """التحقق من إمكانية التصويت للهدف"""
        return target_id in self.eligible_targets
    
    def cast_vote(self, voter_id: int, target_id: int, vote_weight: int = 1) -> Tuple[bool, str]:
        """تسجيل صوت"""
        with self._lock:
            if not self.can_vote(voter_id):
                return False, "لا يمكنك التصويت الآن"
            
            if target_id and not self.can_be_voted_for(target_id):
                return False, "لا يمكن التصويت لهذا اللاعب"
            
            # إزالة الصوت السابق إن وجد
            if voter_id in self.votes:
                old_vote = self.votes[voter_id]
                self.vote_counts[old_vote.target_id] -= old_vote.vote_weight
                if self.vote_counts[old_vote.target_id] <= 0:
                    del self.vote_counts[old_vote.target_id]
            
            # تسجيل الصوت الجديد
            if target_id:  # تصويت حقيقي (ليس امتناع)
                vote = Vote(voter_id, target_id, vote_weight)
                self.votes[voter_id] = vote
                self.vote_counts[target_id] += vote_weight
            else:  # امتناع عن التصويت
                if voter_id in self.votes:
                    del self.votes[voter_id]
            
            return True, "تم تسجيل الصوت"
    
    def get_vote_results(self) -> Dict:
        """الحصول على نتائج التصويت"""
        with self._lock:
            results = {
                'session_id': self.session_id,
                'vote_type': self.vote_type,
                'is_active': self.is_active,
                'is_completed': self.is_completed,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'remaining_time': self.get_remaining_time(),
                'total_eligible_voters': len(self.eligible_voters),
                'total_votes_cast': len(self.votes),
                'vote_counts': dict(self.vote_counts),
                'votes': [
                    {
                        'voter_id': vote.voter_id,
                        'target_id': vote.target_id,
                        'vote_weight': vote.vote_weight,
                        'timestamp': vote.timestamp.isoformat()
                    }
                    for vote in self.votes.values()
                ]
            }
            
            if self.result:
                results['result'] = self.result
            
            return results
    
    def get_remaining_time(self) -> int:
        """الوقت المتبقي بالثواني"""
        if not self.is_active:
            return 0
        
        remaining = (self.end_time - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
    
    def is_expired(self) -> bool:
        """التحقق من انتهاء وقت التصويت"""
        return datetime.utcnow() >= self.end_time
    
    def complete_voting(self) -> Dict:
        """إنهاء التصويت وحساب النتيجة"""
        with self._lock:
            if self.is_completed:
                return self.result
            
            self.is_active = False
            self.is_completed = True
            
            # حساب النتيجة
            if not self.vote_counts:
                # لا توجد أصوات
                self.result = {
                    'outcome': 'no_votes',
                    'message': 'لم يصوت أحد',
                    'eliminated_player_id': None
                }
            else:
                # العثور على اللاعب الأكثر حصولاً على أصوات
                max_votes = max(self.vote_counts.values())
                candidates = [pid for pid, votes in self.vote_counts.items() if votes == max_votes]
                
                if len(candidates) == 1:
                    # فائز واضح
                    eliminated_id = candidates[0]
                    self.result = {
                        'outcome': 'elimination',
                        'message': f'تم إعدام اللاعب',
                        'eliminated_player_id': eliminated_id,
                        'vote_count': max_votes
                    }
                else:
                    # تعادل
                    self.result = {
                        'outcome': 'tie',
                        'message': f'تعادل بين {len(candidates)} لاعبين',
                        'tied_players': candidates,
                        'vote_count': max_votes
                    }
            
            return self.result

class VotingManager:
    """مدير التصويت في اللعبة"""
    
    def __init__(self):
        self.active_sessions: Dict[str, VotingSession] = {}
        self.room_sessions: Dict[int, str] = {}  # room_id -> session_id
        self._session_counter = 0
        self._lock = threading.Lock()
    
    def start_voting_session(self, room_id: int, vote_type: str = "lynch", 
                           duration: int = 60, eligible_voters: List[int] = None, 
                           eligible_targets: List[int] = None) -> Tuple[bool, str, Optional[VotingSession]]:
        """بدء جلسة تصويت جديدة"""
        
        with self._lock:
            # التحقق من وجود جلسة نشطة
            if room_id in self.room_sessions:
                current_session = self.active_sessions.get(self.room_sessions[room_id])
                if current_session and current_session.is_active:
                    return False, "يوجد تصويت نشط بالفعل", None
            
            # إنشاء جلسة جديدة
            self._session_counter += 1
            session_id = f"vote_{room_id}_{self._session_counter}_{int(datetime.utcnow().timestamp())}"
            
            session = VotingSession(session_id, room_id, vote_type, duration)
            
            # إضافة المصوتين المؤهلين
            if eligible_voters:
                for voter_id in eligible_voters:
                    session.add_eligible_voter(voter_id)
            
            # إضافة الأهداف المؤهلة
            if eligible_targets:
                for target_id in eligible_targets:
                    session.add_eligible_target(target_id)
            
            # حفظ الجلسة
            self.active_sessions[session_id] = session
            self.room_sessions[room_id] = session_id
            
            return True, "تم بدء التصويت", session
    
    def cast_vote(self, room_id: int, voter_id: int, target_id: int = None) -> Tuple[bool, str]:
        """تسجيل صوت"""
        
        session = self.get_active_session(room_id)
        if not session:
            return False, "لا يوجد تصويت نشط"
        
        # تحديد وزن الصوت (العمدة له صوتين)
        voter = Player.query.get(voter_id)
        vote_weight = 2 if voter and voter.role == PlayerRole.MAYOR else 1
        
        return session.cast_vote(voter_id, target_id, vote_weight)
    
    def get_active_session(self, room_id: int) -> Optional[VotingSession]:
        """الحصول على الجلسة النشطة للغرفة"""
        if room_id not in self.room_sessions:
            return None
        
        session_id = self.room_sessions[room_id]
        session = self.active_sessions.get(session_id)
        
        if session and session.is_active and not session.is_expired():
            return session
        
        return None
    
    def get_voting_results(self, room_id: int) -> Optional[Dict]:
        """الحصول على نتائج التصويت"""
        session = self.get_active_session(room_id)
        if session:
            return session.get_vote_results()
        
        # البحث عن آخر جلسة مكتملة
        if room_id in self.room_sessions:
            session_id = self.room_sessions[room_id]
            session = self.active_sessions.get(session_id)
            if session and session.is_completed:
                return session.get_vote_results()
        
        return None
    
    def complete_voting(self, room_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """إنهاء التصويت قبل انتهاء الوقت"""
        
        session = self.get_active_session(room_id)
        if not session:
            return False, "لا يوجد تصويت نشط", None
        
        result = session.complete_voting()
        return True, "تم إنهاء التصويت", result
    
    def force_complete_voting(self, room_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """إنهاء التصويت بالقوة"""
        return self.complete_voting(room_id)
    
    def check_expired_sessions(self):
        """فحص الجلسات المنتهية الصلاحية"""
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if session.is_active and session.is_expired():
                session.complete_voting()
                expired_sessions.append(session_id)
        
        return expired_sessions
    
    def get_vote_summary(self, room_id: int) -> Dict:
        """الحصول على ملخص التصويت"""
        session = self.get_active_session(room_id)
        if not session:
            return {'error': 'لا يوجد تصويت نشط'}
        
        results = session.get_vote_results()
        
        # إضافة معلومات اللاعبين
        vote_summary = {}
        for target_id, vote_count in results['vote_counts'].items():
            player = Player.query.get(target_id)
            vote_summary[target_id] = {
                'player_name': player.user.display_name if player and player.user else 'لاعب',
                'vote_count': vote_count
            }
        
        # ترتيب حسب عدد الأصوات
        sorted_summary = dict(sorted(vote_summary.items(), key=lambda x: x[1]['vote_count'], reverse=True))
        
        return {
            'session_info': {
                'session_id': results['session_id'],
                'vote_type': results['vote_type'],
                'remaining_time': results['remaining_time'],
                'total_voters': results['total_eligible_voters'],
                'votes_cast': results['total_votes_cast']
            },
            'vote_summary': sorted_summary,
            'leading_candidate': list(sorted_summary.keys())[0] if sorted_summary else None
        }
    
    def get_player_vote(self, room_id: int, player_id: int) -> Optional[Dict]:
        """الحصول على صوت لاعب معين"""
        session = self.get_active_session(room_id)
        if not session or player_id not in session.votes:
            return None
        
        vote = session.votes[player_id]
        target_player = Player.query.get(vote.target_id)
        
        return {
            'target_id': vote.target_id,
            'target_name': target_player.user.display_name if target_player and target_player.user else 'لاعب',
            'vote_weight': vote.vote_weight,
            'timestamp': vote.timestamp.isoformat()
        }
    
    def cancel_voting_session(self, room_id: int) -> Tuple[bool, str]:
        """إلغاء جلسة التصويت"""
        
        with self._lock:
            if room_id not in self.room_sessions:
                return False, "لا يوجد تصويت في هذه الغرفة"
            
            session_id = self.room_sessions[room_id]
            session = self.active_sessions.get(session_id)
            
            if session:
                session.is_active = False
                session.result = {
                    'outcome': 'cancelled',
                    'message': 'تم إلغاء التصويت',
                    'eliminated_player_id': None
                }
            
            # تنظيف المراجع
            del self.room_sessions[room_id]
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return True, "تم إلغاء التصويت"
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """تنظيف الجلسات القديمة"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        old_sessions = []
        
        for session_id, session in list(self.active_sessions.items()):
            if session.start_time < cutoff_time:
                old_sessions.append(session_id)
                
                # إزالة من room_sessions أيضاً
                for room_id, sid in list(self.room_sessions.items()):
                    if sid == session_id:
                        del self.room_sessions[room_id]
                        break
        
        # حذف الجلسات القديمة
        for session_id in old_sessions:
            del self.active_sessions[session_id]
        
        return len(old_sessions)
    
    def get_session_statistics(self) -> Dict:
        """الحصول على إحصائيات الجلسات"""
        active_count = len([s for s in self.active_sessions.values() if s.is_active])
        completed_count = len([s for s in self.active_sessions.values() if s.is_completed])
        
        return {
            'total_sessions': len(self.active_sessions),
            'active_sessions': active_count,
            'completed_sessions': completed_count,
            'rooms_with_voting': len(self.room_sessions)
        }