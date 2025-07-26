#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير اللعبة الرئيسي
Game Manager
"""

import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from models import db
from models.room import Room, RoomStatus
from models.game import Game, GamePhase, GameStatus, WinCondition
from models.player import Player, PlayerRole
from models.message import Message
from models.game_log import GameLog
from .role_manager import RoleManager
from .voting_manager import VotingManager
from .phase_manager import PhaseManager

class GameSession:
    """جلسة لعبة واحدة"""
    
    def __init__(self, game_id: int, room_id: int):
        self.game_id = game_id
        self.room_id = room_id
        self.is_active = True
        
        # المدراء المساعدون
        self.role_manager = RoleManager()
        self.voting_manager = VotingManager()
        self.phase_manager = PhaseManager(game_id, self._on_phase_change)
        
        # معلومات اللعبة
        self.players: List[Player] = []
        self.current_round = 1
        
        # أقفال للأمان
        self._lock = threading.Lock()
        
        # معالجات الأحداث
        self.event_callbacks: Dict[str, List[Callable]] = {
            'game_start': [],
            'game_end': [],
            'phase_change': [],
            'player_death': [],
            'voting_start': [],
            'voting_end': []
        }
    
    def add_event_listener(self, event: str, callback: Callable):
        """إضافة مستمع للأحداث"""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _trigger_event(self, event: str, **kwargs):
        """تشغيل معالجات الأحداث"""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(self, **kwargs)
            except Exception as e:
                print(f"خطأ في معالج الحدث {event}: {e}")
    
    def _on_phase_change(self, phase: GamePhase, duration: int, **kwargs):
        """معالج تغيير المرحلة"""
        print(f"تغيرت المرحلة إلى {phase.value} - مدة: {duration} ثانية")
        
        # تحديث اللعبة في قاعدة البيانات
        game = Game.query.get(self.game_id)
        if game:
            game.start_phase(phase, duration)
        
        # تشغيل معالجات خاصة لكل مرحلة
        if phase == GamePhase.VOTING:
            self._start_voting_phase(**kwargs)
        elif phase == GamePhase.NIGHT:
            self._start_night_phase()
        elif phase == GamePhase.DAY:
            self._start_day_phase()
        
        # إشعار المستمعين
        self._trigger_event('phase_change', phase=phase, duration=duration, **kwargs)
    
    def _start_voting_phase(self, **kwargs):
        """بدء مرحلة التصويت"""
        alive_players = [p for p in self.players if p.is_alive]
        eligible_voters = [p.id for p in alive_players]
        eligible_targets = [p.id for p in alive_players]
        
        success, message, session = self.voting_manager.start_voting_session(
            room_id=self.room_id,
            vote_type="lynch",
            duration=60,  # دقيقة واحدة
            eligible_voters=eligible_voters,
            eligible_targets=eligible_targets
        )
        
        if success:
            print(f"بدأ التصويت: {message}")
            self._trigger_event('voting_start', session=session)
        else:
            print(f"فشل في بدء التصويت: {message}")
    
    def _start_night_phase(self):
        """بدء مرحلة الليل"""
        print("بدأت مرحلة الليل - وقت أعمال الأدوار الخاصة")
        
        # إرسال تعليمات للأدوار الخاصة
        mafia_players = self.role_manager.get_mafia_players(self.players)
        doctor_players = self.role_manager.get_players_with_ability(self.players, 'heal')
        detective_players = self.role_manager.get_players_with_ability(self.players, 'investigate')
        vigilante_players = self.role_manager.get_players_with_ability(self.players, 'vigilante_kill')
        
        # إرسال رسائل توجيهية
        if mafia_players:
            Message.create_game_action_message(
                self.room_id,
                "المافيا، اختاروا من تريدون قتله الليلة",
                game_round=self.current_round,
                game_phase="night"
            )
        
        if doctor_players:
            for doctor in doctor_players:
                Message.create_game_action_message(
                    self.room_id,
                    "أيها الطبيب، اختر من تريد حمايته الليلة",
                    user_id=doctor.user_id,
                    game_round=self.current_round,
                    game_phase="night"
                )
    
    def _start_day_phase(self):
        """بدء مرحلة النهار"""
        print("بدأت مرحلة النهار - وقت النقاش")
        
        # عرض نتائج الليل
        self._reveal_night_results()
        
        # التحقق من شروط الفوز
        winner, team = self._check_win_condition()
        if winner:
            self._end_game(winner, team)
    
    def _reveal_night_results(self):
        """كشف نتائج الليل"""
        # سيتم تنفيذ هذا بواسطة PhaseManager
        pass
    
    def _check_win_condition(self) -> tuple[Optional[WinCondition], Optional[str]]:
        """فحص شروط الفوز"""
        alive_players = [p for p in self.players if p.is_alive]
        mafia_count = len([p for p in alive_players if p.role == PlayerRole.MAFIA])
        citizen_count = len(alive_players) - mafia_count
        
        if mafia_count == 0:
            return WinCondition.CITIZENS_WIN, "citizens"
        elif mafia_count >= citizen_count:
            return WinCondition.MAFIA_WIN, "mafia"
        
        return None, None
    
    def _end_game(self, winner: WinCondition, team: str):
        """إنهاء اللعبة"""
        with self._lock:
            if not self.is_active:
                return
            
            self.is_active = False
            
            # تحديث اللعبة في قاعدة البيانات
            game = Game.query.get(self.game_id)
            if game:
                game.finish_game(winner, team)
            
            # تحديث إحصائيات اللاعبين
            self._update_player_statistics(winner, team)
            
            # تحديث حالة الغرفة
            room = Room.query.get(self.room_id)
            if room:
                room.finish_game()
            
            # إيقاف المدراء المساعدين
            self.phase_manager.stop()
            
            # إشعار المستمعين
            self._trigger_event('game_end', winner=winner, team=team)
            
            print(f"انتهت اللعبة - {winner.value}")
    
    def _update_player_statistics(self, winner: WinCondition, team: str):
        """تحديث إحصائيات اللاعبين"""
        game = Game.query.get(self.game_id)
        game_duration = game.get_duration() if game else 0
        
        for player in self.players:
            if not player.user:
                continue
            
            # تحديد الفوز
            player_won = False
            if winner == WinCondition.CITIZENS_WIN and player.role != PlayerRole.MAFIA:
                player_won = True
            elif winner == WinCondition.MAFIA_WIN and player.role == PlayerRole.MAFIA:
                player_won = True
            elif winner == WinCondition.DRAW:
                player_won = None  # تعادل
            
            # تحديث إحصائيات المستخدم الأساسية
            if player_won is not None:
                player.user.update_game_stats(player_won)
            
            # تحديث الإحصائيات المفصلة
            if hasattr(player.user, 'statistics') and player.user.statistics:
                stats = player.user.statistics
                stats.update_game_stats(
                    role=player.role.value,
                    won=player_won,
                    game_duration=game_duration,
                    survived=player.is_alive
                )
    
    def stop(self):
        """إيقاف اللعبة"""
        if self.is_active:
            self._end_game(WinCondition.CANCELLED, None)

class GameManager:
    """المدير الرئيسي للألعاب"""
    
    def __init__(self):
        self.active_games: Dict[int, GameSession] = {}  # room_id -> GameSession
        self.game_sessions_by_id: Dict[int, GameSession] = {}  # game_id -> GameSession
        self._lock = threading.Lock()
    
    def start_game(self, room_id: int) -> tuple[bool, str, Optional[Game]]:
        """بدء لعبة جديدة"""
        
        with self._lock:
            # التحقق من وجود لعبة نشطة
            if room_id in self.active_games:
                return False, "يوجد لعبة نشطة بالفعل في هذه الغرفة", None
            
            try:
                # الحصول على الغرفة
                room = Room.query.get(room_id)
                if not room:
                    return False, "الغرفة غير موجودة", None
                
                # الحصول على اللاعبين
                players = room.get_active_players()
                if len(players) < room.min_players:
                    return False, f"يجب أن يكون هناك {room.min_players} لاعبين على الأقل", None
                
                # إنشاء لعبة جديدة في قاعدة البيانات
                game = Game(room_id=room_id, total_players=len(players))
                db.session.add(game)
                db.session.commit()
                
                # إنشاء جلسة لعبة
                session = GameSession(game.id, room_id)
                session.players = players
                
                # توزيع الأدوار
                if not session.role_manager.assign_roles(players):
                    db.session.delete(game)
                    db.session.commit()
                    return False, "فشل في توزيع الأدوار", None
                
                # تحديث حالة الغرفة
                room.status = RoomStatus.PLAYING
                db.session.commit()
                
                # حفظ الجلسة
                self.active_games[room_id] = session
                self.game_sessions_by_id[game.id] = session
                
                # بدء اللعبة
                session.phase_manager.start_phase(GamePhase.DAY)
                
                # تسجيل بدء اللعبة
                GameLog.log_game_start(game.id, len(players))
                
                # إرسال رسالة بدء اللعبة
                Message.create_system_message(
                    room_id,
                    f"🎮 بدأت اللعبة! عدد اللاعبين: {len(players)}",
                    game_round=1,
                    game_phase="day"
                )
                
                # إرسال الأدوار للاعبين (سيتم عبر WebSocket)
                self._send_roles_to_players(session)
                
                return True, "تم بدء اللعبة بنجاح", game
                
            except Exception as e:
                db.session.rollback()
                return False, f"خطأ في بدء اللعبة: {str(e)}", None
    
    def _send_roles_to_players(self, session: GameSession):
        """إرسال الأدوار للاعبين"""
        for player in session.players:
            role_info = session.role_manager.get_role_info(player.role)
            
            # إرسال رسالة خاصة للاعب
            Message.create_game_action_message(
                session.room_id,
                f"🎭 دورك في اللعبة: {role_info['name']}\n📝 {role_info['description']}\n🎯 شرط الفوز: {role_info['win_condition']}",
                user_id=player.user_id,
                game_round=1,
                game_phase="day"
            )
    
    def get_game_session(self, room_id: int) -> Optional[GameSession]:
        """الحصول على جلسة اللعبة"""
        return self.active_games.get(room_id)
    
    def get_game_by_id(self, game_id: int) -> Optional[GameSession]:
        """الحصول على اللعبة بالمعرف"""
        return self.game_sessions_by_id.get(game_id)
    
    def submit_action(self, room_id: int, player_id: int, action_type: str, target_id: int = None, **details) -> tuple[bool, str]:
        """تقديم إجراء في اللعبة"""
        
        session = self.get_game_session(room_id)
        if not session:
            return False, "لا توجد لعبة نشطة"
        
        return session.phase_manager.submit_action(player_id, action_type, target_id, **details)
    
    def cast_vote(self, room_id: int, voter_id: int, target_id: int = None) -> tuple[bool, str]:
        """تسجيل صوت"""
        
        session = self.get_game_session(room_id)
        if not session:
            return False, "لا توجد لعبة نشطة"
        
        return session.voting_manager.cast_vote(room_id, voter_id, target_id)
    
    def get_game_status(self, room_id: int) -> Dict:
        """الحصول على حالة اللعبة"""
        
        session = self.get_game_session(room_id)
        if not session:
            return {'error': 'لا توجد لعبة نشطة'}
        
        # معلومات اللعبة
        game = Game.query.get(session.game_id)
        phase_info = session.phase_manager.get_phase_info()
        voting_results = session.voting_manager.get_voting_results(room_id)
        
        # معلومات اللاعبين
        players_info = []
        for player in session.players:
            players_info.append({
                'id': player.id,
                'user_id': player.user_id,
                'display_name': player.user.display_name if player.user else 'لاعب',
                'is_alive': player.is_alive,
                'status': player.status.value
            })
        
        # إحصائيات اللعبة
        role_summary = session.role_manager.get_role_summary(session.players)
        
        return {
            'game_id': session.game_id,
            'room_id': session.room_id,
            'is_active': session.is_active,
            'current_round': session.current_round,
            'phase': phase_info,
            'players': players_info,
            'role_summary': role_summary,
            'voting': voting_results,
            'game_info': game.to_dict() if game else None
        }
    
    def get_player_info(self, room_id: int, player_id: int) -> Dict:
        """الحصول على معلومات اللاعب"""
        
        session = self.get_game_session(room_id)
        if not session:
            return {'error': 'لا توجد لعبة نشطة'}
        
        player = Player.query.get(player_id)
        if not player or player.room_id != room_id:
            return {'error': 'اللاعب غير موجود'}
        
        # معلومات أساسية
        info = player.to_dict(include_role=True, include_private=True)
        
        # معلومات إضافية للعبة
        phase_action = session.phase_manager.get_player_action(player_id)
        vote_info = session.voting_manager.get_player_vote(room_id, player_id)
        
        info.update({
            'current_action': phase_action,
            'current_vote': vote_info,
            'can_act': session.phase_manager.current_phase == GamePhase.NIGHT and player.can_take_action(),
            'can_vote': session.phase_manager.current_phase == GamePhase.VOTING and player.can_vote()
        })
        
        return info
    
    def end_game(self, room_id: int, reason: str = "انتهت اللعبة") -> tuple[bool, str]:
        """إنهاء اللعبة"""
        
        with self._lock:
            session = self.get_game_session(room_id)
            if not session:
                return False, "لا توجد لعبة نشطة"
            
            try:
                # إنهاء اللعبة
                session._end_game(WinCondition.CANCELLED, None)
                
                # إزالة الجلسة
                if room_id in self.active_games:
                    del self.active_games[room_id]
                
                if session.game_id in self.game_sessions_by_id:
                    del self.game_sessions_by_id[session.game_id]
                
                # تحديث حالة الغرفة
                room = Room.query.get(room_id)
                if room:
                    room.status = RoomStatus.FINISHED
                    db.session.commit()
                
                return True, reason
                
            except Exception as e:
                return False, f"خطأ في إنهاء اللعبة: {str(e)}"
    
    def cleanup_finished_games(self):
        """تنظيف الألعاب المنتهية"""
        finished_games = []
        
        with self._lock:
            for room_id, session in list(self.active_games.items()):
                if not session.is_active:
                    finished_games.append(room_id)
            
            for room_id in finished_games:
                session = self.active_games[room_id]
                
                # إزالة من القواميس
                del self.active_games[room_id]
                if session.game_id in self.game_sessions_by_id:
                    del self.game_sessions_by_id[session.game_id]
        
        return len(finished_games)
    
    def get_active_games_count(self) -> int:
        """عدد الألعاب النشطة"""
        return len(self.active_games)
    
    def get_statistics(self) -> Dict:
        """إحصائيات المدير"""
        return {
            'active_games': len(self.active_games),
            'total_sessions': len(self.game_sessions_by_id),
            'rooms_with_games': list(self.active_games.keys())
        }