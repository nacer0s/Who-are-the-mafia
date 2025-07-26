#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أمثلة على استخدام API لعبة المافيا
Mafia Game API Usage Examples
"""

import requests
import json
from typing import Dict, Any

class MafiaGameAPI:
    """عميل API للعبة المافيا"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.current_user = None
        self.current_room = None
    
    def register(self, username: str, display_name: str, password: str, email: str = "") -> Dict[str, Any]:
        """تسجيل مستخدم جديد"""
        
        data = {
            "username": username,
            "display_name": display_name,
            "password": password,
            "email": email
        }
        
        response = self.session.post(f"{self.base_url}/api/auth/register", json=data)
        result = response.json()
        
        if result.get('success'):
            self.current_user = result.get('user')
            print(f"✅ تم تسجيل المستخدم: {display_name}")
        else:
            print(f"❌ فشل التسجيل: {result.get('message')}")
        
        return result
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """تسجيل الدخول"""
        
        data = {
            "username": username,
            "password": password
        }
        
        response = self.session.post(f"{self.base_url}/api/auth/login", json=data)
        result = response.json()
        
        if result.get('success'):
            self.current_user = result.get('user')
            print(f"✅ تم تسجيل الدخول: {self.current_user['display_name']}")
        else:
            print(f"❌ فشل تسجيل الدخول: {result.get('message')}")
        
        return result
    
    def create_room(self, name: str, max_players: int = 8, min_players: int = 4, 
                   password: str = None, allow_voice_chat: bool = True) -> Dict[str, Any]:
        """إنشاء غرفة جديدة"""
        
        if not self.current_user:
            print("❌ يجب تسجيل الدخول أولاً")
            return {"success": False, "message": "غير مسجل الدخول"}
        
        data = {
            "name": name,
            "max_players": max_players,
            "min_players": min_players,
            "password": password,
            "allow_voice_chat": allow_voice_chat,
            "allow_text_chat": True,
            "auto_start": False
        }
        
        response = self.session.post(f"{self.base_url}/api/room/create", json=data)
        result = response.json()
        
        if result.get('success'):
            self.current_room = result.get('room')
            print(f"✅ تم إنشاء الغرفة: {name} - الرمز: {self.current_room['room_code']}")
        else:
            print(f"❌ فشل إنشاء الغرفة: {result.get('message')}")
        
        return result
    
    def join_room(self, room_code: str, password: str = None) -> Dict[str, Any]:
        """الانضمام لغرفة"""
        
        if not self.current_user:
            print("❌ يجب تسجيل الدخول أولاً")
            return {"success": False, "message": "غير مسجل الدخول"}
        
        data = {
            "room_code": room_code,
            "password": password
        }
        
        response = self.session.post(f"{self.base_url}/api/room/join", json=data)
        result = response.json()
        
        if result.get('success'):
            self.current_room = result.get('room')
            print(f"✅ تم الانضمام للغرفة: {self.current_room['name']}")
        else:
            print(f"❌ فشل الانضمام: {result.get('message')}")
        
        return result
    
    def set_ready(self, ready: bool = True) -> Dict[str, Any]:
        """تعيين حالة الاستعداد"""
        
        if not self.current_room:
            print("❌ لست في أي غرفة")
            return {"success": False, "message": "لست في غرفة"}
        
        data = {"ready": ready}
        
        response = self.session.post(
            f"{self.base_url}/api/room/{self.current_room['room_code']}/ready", 
            json=data
        )
        result = response.json()
        
        status = "مستعد" if ready else "غير مستعد"
        if result.get('success'):
            print(f"✅ تم تعيين الحالة: {status}")
        else:
            print(f"❌ فشل تعيين الحالة: {result.get('message')}")
        
        return result
    
    def start_game(self) -> Dict[str, Any]:
        """بدء اللعبة"""
        
        if not self.current_room:
            print("❌ لست في أي غرفة")
            return {"success": False, "message": "لست في غرفة"}
        
        response = self.session.post(f"{self.base_url}/api/game/start")
        result = response.json()
        
        if result.get('success'):
            print("🎮 تم بدء اللعبة!")
        else:
            print(f"❌ فشل بدء اللعبة: {result.get('message')}")
        
        return result
    
    def get_game_status(self) -> Dict[str, Any]:
        """الحصول على حالة اللعبة"""
        
        response = self.session.get(f"{self.base_url}/api/game/status")
        result = response.json()
        
        if result.get('success'):
            status = result.get('status', {})
            print(f"📊 حالة اللعبة: {status.get('phase', {}).get('phase', 'غير معروفة')}")
            print(f"👥 اللاعبون الأحياء: {len([p for p in status.get('players', []) if p.get('is_alive')])}")
        
        return result
    
    def cast_vote(self, target_player_id: int = None) -> Dict[str, Any]:
        """التصويت"""
        
        data = {"target_id": target_player_id}
        
        response = self.session.post(f"{self.base_url}/api/game/vote", json=data)
        result = response.json()
        
        if result.get('success'):
            if target_player_id:
                print(f"✅ تم التصويت ضد اللاعب {target_player_id}")
            else:
                print("✅ تم الامتناع عن التصويت")
        else:
            print(f"❌ فشل التصويت: {result.get('message')}")
        
        return result
    
    def get_my_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائياتي"""
        
        response = self.session.get(f"{self.base_url}/api/stats/my-stats")
        result = response.json()
        
        if result.get('success'):
            stats = result.get('statistics', {})
            print(f"📈 إحصائياتك:")
            print(f"   🎮 إجمالي الألعاب: {stats.get('total_games_played', 0)}")
            print(f"   🏆 معدل الفوز: {stats.get('win_rate', 0):.1f}%")
            print(f"   💬 الرسائل المرسلة: {stats.get('total_messages_sent', 0)}")
        
        return result
    
    def get_leaderboard(self) -> Dict[str, Any]:
        """الحصول على لوحة المتصدرين"""
        
        response = self.session.get(f"{self.base_url}/api/stats/leaderboard")
        result = response.json()
        
        if result.get('success'):
            leaderboard = result.get('leaderboard', [])
            print("🏆 لوحة المتصدرين:")
            for i, player in enumerate(leaderboard[:5], 1):
                print(f"   {i}. {player['display_name']} - {player['win_rate']:.1f}%")
        
        return result
    
    def health_check(self) -> Dict[str, Any]:
        """فحص صحة الخادم"""
        
        response = self.session.get(f"{self.base_url}/health")
        result = response.json()
        
        print(f"🏥 حالة الخادم: {result.get('status', 'غير معروفة')}")
        print(f"🎮 الألعاب النشطة: {result.get('active_games', 0)}")
        print(f"🏠 الغرف النشطة: {result.get('active_rooms', 0)}")
        
        return result

# أمثلة على الاستخدام
def example_complete_game():
    """مثال كامل على لعبة"""
    
    print("🎮 مثال على لعبة كاملة")
    print("=" * 50)
    
    # إنشاء عملاء API
    host = MafiaGameAPI()
    player1 = MafiaGameAPI()
    player2 = MafiaGameAPI()
    
    # فحص الخادم
    print("\n1. فحص صحة الخادم:")
    host.health_check()
    
    # تسجيل المستخدمين
    print("\n2. تسجيل المستخدمين:")
    host.register("host_user", "منظم اللعبة", "123456", "host@test.com")
    player1.register("player1", "اللاعب الأول", "123456", "player1@test.com")
    player2.register("player2", "اللاعب الثاني", "123456", "player2@test.com")
    
    # إنشاء غرفة
    print("\n3. إنشاء غرفة:")
    room_result = host.create_room("غرفة تجريبية", max_players=4, min_players=3)
    room_code = room_result.get('room', {}).get('room_code')
    
    if not room_code:
        print("❌ فشل في الحصول على رمز الغرفة")
        return
    
    # انضمام اللاعبين
    print("\n4. انضمام اللاعبين:")
    player1.join_room(room_code)
    player2.join_room(room_code)
    
    # تعيين الاستعداد
    print("\n5. تعيين الاستعداد:")
    host.set_ready()
    player1.set_ready()
    player2.set_ready()
    
    # بدء اللعبة
    print("\n6. بدء اللعبة:")
    host.start_game()
    
    # فحص حالة اللعبة
    print("\n7. حالة اللعبة:")
    host.get_game_status()
    
    # عرض الإحصائيات
    print("\n8. الإحصائيات:")
    host.get_my_stats()
    host.get_leaderboard()
    
    print("\n✅ انتهى المثال بنجاح!")

def example_quick_test():
    """اختبار سريع للـ API"""
    
    print("⚡ اختبار سريع للـ API")
    print("=" * 30)
    
    api = MafiaGameAPI()
    
    # فحص الخادم
    api.health_check()
    
    # تسجيل دخول بحساب تجريبي
    api.login("احمد", "test123")
    
    # عرض الإحصائيات
    api.get_my_stats()
    
    print("\n✅ انتهى الاختبار!")

if __name__ == "__main__":
    # تشغيل المثال المطلوب
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        example_quick_test()
    else:
        example_complete_game()