#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير الغرف
Room Manager
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db, Room, Player, User
from models.room import RoomStatus

class RoomManager:
    """مدير الغرف في اللعبة"""
    
    def __init__(self):
        self.active_rooms: Dict[str, Room] = {}  # room_code -> Room
        self.player_rooms: Dict[int, str] = {}   # user_id -> room_code
        self.room_locks: Dict[str, threading.Lock] = {}
        self._cleanup_timer = None
        self._start_cleanup_timer()
    
    def create_room(self, creator_id: int, room_name: str, **settings) -> tuple[bool, str, Optional[Room]]:
        """إنشاء غرفة جديدة"""
        try:
            # التحقق من وجود المستخدم
            creator = User.query.get(creator_id)
            if not creator:
                return False, "المستخدم غير موجود", None
            
            # التحقق من وجود اللاعب في غرفة أخرى
            if creator_id in self.player_rooms:
                return False, "أنت موجود بالفعل في غرفة أخرى", None
            
            # إنشاء الغرفة
            room = Room(
                name=room_name,
                creator_id=creator_id,
                **settings
            )
            
            db.session.add(room)
            db.session.commit()
            
            # إضافة الغرفة للذاكرة
            self.active_rooms[room.room_code] = room
            self.room_locks[room.room_code] = threading.Lock()
            
            # إضافة المنشئ كلاعب
            success, message = self.join_room(creator_id, room.room_code)
            if not success:
                # حذف الغرفة إذا فشل انضمام المنشئ
                db.session.delete(room)
                db.session.commit()
                return False, f"فشل في إضافة المنشئ: {message}", None
            
            return True, "تم إنشاء الغرفة بنجاح", room
            
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ في إنشاء الغرفة: {str(e)}", None
    
    def join_room(self, user_id: int, room_code: str, password: str = None) -> tuple[bool, str]:
        """الانضمام إلى غرفة"""
        try:
            # التحقق من وجود المستخدم
            user = User.query.get(user_id)
            if not user:
                return False, "المستخدم غير موجود"
            
            # التحقق من وجود اللاعب في غرفة أخرى
            if user_id in self.player_rooms:
                current_room_code = self.player_rooms[user_id]
                if current_room_code == room_code:
                    return False, "أنت موجود بالفعل في هذه الغرفة"
                else:
                    return False, "يجب مغادرة الغرفة الحالية أولاً"
            
            # البحث عن الغرفة
            room = self.get_room(room_code)
            if not room:
                return False, "الغرفة غير موجودة"
            
            # الحصول على قفل الغرفة
            with self.room_locks.get(room_code, threading.Lock()):
                # التحقق من إمكانية الانضمام
                if not room.can_join():
                    if room.is_full():
                        return False, "الغرفة ممتلئة"
                    else:
                        return False, "لا يمكن الانضمام إلى الغرفة الآن"
                
                # التحقق من كلمة المرور للغرف الخاصة
                if room.password and room.password != password:
                    return False, "كلمة مرور خاطئة"
                
                # إضافة اللاعب
                success, message = room.add_player(user_id)
                if success:
                    self.player_rooms[user_id] = room_code
                    user.update_last_seen()
                
                return success, message
                
        except Exception as e:
            return False, f"خطأ في الانضمام: {str(e)}"
    
    def leave_room(self, user_id: int) -> tuple[bool, str]:
        """مغادرة الغرفة"""
        try:
            # التحقق من وجود اللاعب في غرفة
            if user_id not in self.player_rooms:
                return False, "لست في أي غرفة"
            
            room_code = self.player_rooms[user_id]
            room = self.get_room(room_code)
            
            if not room:
                # إزالة من الذاكرة إذا لم تعد الغرفة موجودة
                del self.player_rooms[user_id]
                return False, "الغرفة غير موجودة"
            
            # الحصول على قفل الغرفة
            with self.room_locks.get(room_code, threading.Lock()):
                # إزالة اللاعب من الغرفة
                success, message = room.remove_player(user_id)
                if success:
                    del self.player_rooms[user_id]
                    
                    # التحقق من حاجة حذف الغرفة
                    if room.current_players == 0:
                        self._cleanup_empty_room(room_code)
                
                return success, message
                
        except Exception as e:
            return False, f"خطأ في المغادرة: {str(e)}"
    
    def remove_player_from_all_rooms(self, user_id: int):
        """إزالة اللاعب من جميع الغرف (عند قطع الاتصال)"""
        if user_id in self.player_rooms:
            self.leave_room(user_id)
        
        # تحديث حالة المستخدم
        user = User.query.get(user_id)
        if user:
            user.set_offline()
    
    def get_room(self, room_code: str) -> Optional[Room]:
        """الحصول على غرفة بالرمز"""
        # محاولة الحصول من الذاكرة أولاً
        if room_code in self.active_rooms:
            return self.active_rooms[room_code]
        
        # البحث في قاعدة البيانات
        room = Room.query.filter_by(room_code=room_code).first()
        if room and room.status in [RoomStatus.WAITING, RoomStatus.STARTING, RoomStatus.PLAYING]:
            self.active_rooms[room_code] = room
            if room_code not in self.room_locks:
                self.room_locks[room_code] = threading.Lock()
        
        return room
    
    def get_user_room(self, user_id: int) -> Optional[Room]:
        """الحصول على غرفة المستخدم"""
        if user_id in self.player_rooms:
            room_code = self.player_rooms[user_id]
            return self.get_room(room_code)
        return None
    
    def get_room_players(self, room_code: str) -> List[Player]:
        """الحصول على لاعبي الغرفة"""
        room = self.get_room(room_code)
        if room:
            return room.get_active_players()
        return []
    
    def get_public_rooms(self, limit: int = 20) -> List[Room]:
        """الحصول على الغرف العامة"""
        return Room.query.filter(
            Room.password.is_(None),
            Room.status.in_([RoomStatus.WAITING, RoomStatus.STARTING])
        ).order_by(Room.created_at.desc()).limit(limit).all()
    
    def search_rooms(self, query: str, limit: int = 10) -> List[Room]:
        """البحث في الغرف"""
        return Room.query.filter(
            Room.name.contains(query),
            Room.password.is_(None),
            Room.status.in_([RoomStatus.WAITING, RoomStatus.STARTING])
        ).order_by(Room.created_at.desc()).limit(limit).all()
    
    def get_room_stats(self, room_code: str) -> dict:
        """الحصول على إحصائيات الغرفة"""
        room = self.get_room(room_code)
        if not room:
            return {}
        
        players = self.get_room_players(room_code)
        
        return {
            'room_code': room_code,
            'name': room.name,
            'current_players': len(players),
            'max_players': room.max_players,
            'status': room.status.value,
            'created_at': room.created_at.isoformat(),
            'creator_name': room.creator.display_name if room.creator else None,
            'players': [
                {
                    'user_id': p.user_id,
                    'display_name': p.user.display_name,
                    'is_ready': p.is_ready,
                    'joined_at': p.joined_at.isoformat()
                }
                for p in players
            ]
        }
    
    def set_player_ready(self, user_id: int, ready: bool = True) -> tuple[bool, str]:
        """تعيين حالة استعداد اللاعب"""
        try:
            room = self.get_user_room(user_id)
            if not room:
                return False, "لست في أي غرفة"
            
            player = Player.query.filter_by(
                user_id=user_id,
                room_id=room.id
            ).first()
            
            if not player:
                return False, "لاعب غير موجود"
            
            player.is_ready = ready
            db.session.commit()
            
            # التحقق من استعداد جميع اللاعبين للبدء التلقائي
            if ready and room.auto_start:
                players = self.get_room_players(room.room_code)
                all_ready = all(p.is_ready for p in players)
                enough_players = len(players) >= room.min_players
                
                if all_ready and enough_players:
                    room.start_game()
            
            return True, "تم تحديث حالة الاستعداد"
            
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    def update_room_settings(self, room_code: str, user_id: int, **settings) -> tuple[bool, str]:
        """تحديث إعدادات الغرفة"""
        try:
            room = self.get_room(room_code)
            if not room:
                return False, "الغرفة غير موجودة"
            
            # التحقق من صلاحية التعديل
            if room.creator_id != user_id:
                return False, "ليس لديك صلاحية تعديل إعدادات الغرفة"
            
            if room.status != RoomStatus.WAITING:
                return False, "لا يمكن تعديل الإعدادات أثناء اللعبة"
            
            # تطبيق الإعدادات
            allowed_settings = [
                'name', 'description', 'max_players', 'min_players',
                'allow_voice_chat', 'allow_text_chat', 'auto_start'
            ]
            
            for key, value in settings.items():
                if key in allowed_settings and hasattr(room, key):
                    setattr(room, key, value)
            
            db.session.commit()
            return True, "تم تحديث الإعدادات"
            
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    def delete_room(self, room_code: str, user_id: int) -> tuple[bool, str]:
        """حذف الغرفة"""
        try:
            room = self.get_room(room_code)
            if not room:
                return False, "الغرفة غير موجودة"
            
            # التحقق من الصلاحية
            if room.creator_id != user_id:
                return False, "ليس لديك صلاحية حذف الغرفة"
            
            # إزالة جميع اللاعبين
            players = self.get_room_players(room_code)
            for player in players:
                if player.user_id in self.player_rooms:
                    del self.player_rooms[player.user_id]
            
            # حذف الغرفة
            room.cancel_game()
            self._cleanup_empty_room(room_code)
            
            return True, "تم حذف الغرفة"
            
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    def _cleanup_empty_room(self, room_code: str):
        """تنظيف الغرفة الفارغة"""
        try:
            if room_code in self.active_rooms:
                del self.active_rooms[room_code]
            
            if room_code in self.room_locks:
                del self.room_locks[room_code]
            
            # تحديث حالة الغرفة في قاعدة البيانات
            room = Room.query.filter_by(room_code=room_code).first()
            if room and room.current_players == 0:
                room.status = RoomStatus.CANCELLED
                db.session.commit()
                
        except Exception as e:
            print(f"خطأ في تنظيف الغرفة {room_code}: {e}")
    
    def _cleanup_inactive_rooms(self):
        """تنظيف الغرف غير النشطة"""
        try:
            # حذف الغرف القديمة (أكثر من ساعة بدون نشاط)
            cutoff = datetime.utcnow() - timedelta(hours=1)
            
            inactive_rooms = Room.query.filter(
                Room.status == RoomStatus.WAITING,
                Room.current_players == 0,
                Room.created_at < cutoff
            ).all()
            
            for room in inactive_rooms:
                if room.room_code in self.active_rooms:
                    del self.active_rooms[room.room_code]
                if room.room_code in self.room_locks:
                    del self.room_locks[room.room_code]
                
                room.status = RoomStatus.CANCELLED
                db.session.commit()
            
            print(f"تم تنظيف {len(inactive_rooms)} غرفة غير نشطة")
            
        except Exception as e:
            print(f"خطأ في تنظيف الغرف: {e}")
    
    def _start_cleanup_timer(self):
        """بدء مؤقت التنظيف"""
        self._cleanup_inactive_rooms()
        
        # إعادة جدولة التنظيف كل 30 دقيقة
        self._cleanup_timer = threading.Timer(1800, self._start_cleanup_timer)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
    
    def get_active_rooms_count(self) -> int:
        """عدد الغرف النشطة"""
        return len(self.active_rooms)
    
    def get_total_players_count(self) -> int:
        """عدد اللاعبين الإجمالي"""
        return len(self.player_rooms)
    
    def __del__(self):
        """تنظيف الموارد"""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()