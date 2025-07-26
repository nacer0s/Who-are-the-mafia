#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير الأدوار
Role Manager
"""

import random
from typing import Dict, List, Tuple
from models.player import Player, PlayerRole

class RoleDistribution:
    """توزيع الأدوار حسب عدد اللاعبين"""
    
    # توزيع الأدوار الافتراضي
    DEFAULT_DISTRIBUTIONS = {
        4: {PlayerRole.MAFIA: 1, PlayerRole.CITIZEN: 2, PlayerRole.DOCTOR: 1},
        5: {PlayerRole.MAFIA: 1, PlayerRole.CITIZEN: 3, PlayerRole.DOCTOR: 1},
        6: {PlayerRole.MAFIA: 2, PlayerRole.CITIZEN: 3, PlayerRole.DOCTOR: 1},
        7: {PlayerRole.MAFIA: 2, PlayerRole.CITIZEN: 3, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1},
        8: {PlayerRole.MAFIA: 2, PlayerRole.CITIZEN: 4, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1},
        9: {PlayerRole.MAFIA: 2, PlayerRole.CITIZEN: 5, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1},
        10: {PlayerRole.MAFIA: 3, PlayerRole.CITIZEN: 5, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1},
        11: {PlayerRole.MAFIA: 3, PlayerRole.CITIZEN: 5, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1},
        12: {PlayerRole.MAFIA: 3, PlayerRole.CITIZEN: 6, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1},
        13: {PlayerRole.MAFIA: 3, PlayerRole.CITIZEN: 7, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1},
        14: {PlayerRole.MAFIA: 4, PlayerRole.CITIZEN: 7, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1},
        15: {PlayerRole.MAFIA: 4, PlayerRole.CITIZEN: 8, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1},
        16: {PlayerRole.MAFIA: 4, PlayerRole.CITIZEN: 8, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1, PlayerRole.MAYOR: 1},
        17: {PlayerRole.MAFIA: 4, PlayerRole.CITIZEN: 9, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1, PlayerRole.MAYOR: 1},
        18: {PlayerRole.MAFIA: 5, PlayerRole.CITIZEN: 9, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1, PlayerRole.MAYOR: 1},
        19: {PlayerRole.MAFIA: 5, PlayerRole.CITIZEN: 10, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1, PlayerRole.MAYOR: 1},
        20: {PlayerRole.MAFIA: 5, PlayerRole.CITIZEN: 10, PlayerRole.DOCTOR: 1, PlayerRole.DETECTIVE: 1, PlayerRole.VIGILANTE: 1, PlayerRole.MAYOR: 1, PlayerRole.JESTER: 1},
    }

class RoleManager:
    """مدير الأدوار في اللعبة"""
    
    def __init__(self):
        self.role_descriptions = {
            PlayerRole.CITIZEN: {
                'name': 'مواطن',
                'description': 'مواطن عادي، هدفك العثور على المافيا والقضاء عليهم',
                'team': 'citizens',
                'abilities': ['vote'],
                'win_condition': 'القضاء على جميع أفراد المافيا'
            },
            PlayerRole.MAFIA: {
                'name': 'مافيا',
                'description': 'أنت من المافيا، هدفك القضاء على جميع المواطنين',
                'team': 'mafia',
                'abilities': ['vote', 'kill'],
                'win_condition': 'أن يكون عدد المافيا مساوياً أو أكبر من عدد المواطنين'
            },
            PlayerRole.DOCTOR: {
                'name': 'طبيب',
                'description': 'يمكنك حماية لاعب واحد كل ليلة من الموت',
                'team': 'citizens',
                'abilities': ['vote', 'heal'],
                'win_condition': 'القضاء على جميع أفراد المافيا'
            },
            PlayerRole.DETECTIVE: {
                'name': 'محقق',
                'description': 'يمكنك التحقق من هوية لاعب واحد كل ليلة',
                'team': 'citizens',
                'abilities': ['vote', 'investigate'],
                'win_condition': 'القضاء على جميع أفراد المافيا'
            },
            PlayerRole.VIGILANTE: {
                'name': 'عدالة شعبية',
                'description': 'يمكنك قتل لاعب واحد كل ليلة',
                'team': 'citizens',
                'abilities': ['vote', 'vigilante_kill'],
                'win_condition': 'القضاء على جميع أفراد المافيا'
            },
            PlayerRole.MAYOR: {
                'name': 'عمدة',
                'description': 'صوتك يحسب بصوتين في التصويت',
                'team': 'citizens',
                'abilities': ['vote', 'double_vote'],
                'win_condition': 'القضاء على جميع أفراد المافيا'
            },
            PlayerRole.JESTER: {
                'name': 'مهرج',
                'description': 'هدفك أن يتم إعدامك بالتصويت',
                'team': 'neutral',
                'abilities': ['vote'],
                'win_condition': 'أن يتم إعدامك بالتصويت'
            }
        }
    
    def get_role_distribution(self, player_count: int, custom_distribution: Dict[PlayerRole, int] = None) -> Dict[PlayerRole, int]:
        """الحصول على توزيع الأدوار لعدد معين من اللاعبين"""
        
        if custom_distribution:
            # التحقق من صحة التوزيع المخصص
            if sum(custom_distribution.values()) != player_count:
                raise ValueError("مجموع الأدوار لا يساوي عدد اللاعبين")
            return custom_distribution
        
        # استخدام التوزيع الافتراضي
        if player_count in RoleDistribution.DEFAULT_DISTRIBUTIONS:
            return RoleDistribution.DEFAULT_DISTRIBUTIONS[player_count]
        
        # إنشاء توزيع تلقائي للأعداد غير المحددة
        return self._generate_automatic_distribution(player_count)
    
    def _generate_automatic_distribution(self, player_count: int) -> Dict[PlayerRole, int]:
        """إنشاء توزيع تلقائي للأدوار"""
        if player_count < 4:
            raise ValueError("يجب أن يكون عدد اللاعبين 4 على الأقل")
        
        # نسبة المافيا تتراوح بين 25% و 33%
        mafia_count = max(1, min(player_count // 3, player_count // 4 + 1))
        
        remaining = player_count - mafia_count
        
        distribution = {PlayerRole.MAFIA: mafia_count}
        
        # إضافة الأدوار الخاصة
        if remaining > 2:
            distribution[PlayerRole.DOCTOR] = 1
            remaining -= 1
        
        if remaining > 3:
            distribution[PlayerRole.DETECTIVE] = 1
            remaining -= 1
        
        if remaining > 5:
            distribution[PlayerRole.VIGILANTE] = 1
            remaining -= 1
        
        if remaining > 7:
            distribution[PlayerRole.MAYOR] = 1
            remaining -= 1
        
        # باقي اللاعبين مواطنون عاديون
        distribution[PlayerRole.CITIZEN] = remaining
        
        return distribution
    
    def assign_roles(self, players: List[Player], custom_distribution: Dict[PlayerRole, int] = None) -> bool:
        """توزيع الأدوار على اللاعبين"""
        try:
            player_count = len(players)
            
            if player_count < 4:
                raise ValueError("يجب أن يكون عدد اللاعبين 4 على الأقل")
            
            # الحصول على توزيع الأدوار
            distribution = self.get_role_distribution(player_count, custom_distribution)
            
            # إنشاء قائمة الأدوار
            role_list = []
            for role, count in distribution.items():
                role_list.extend([role] * count)
            
            # خلط الأدوار عشوائياً
            random.shuffle(role_list)
            
            # توزيع الأدوار على اللاعبين
            for i, player in enumerate(players):
                player.assign_role(role_list[i])
            
            return True
            
        except Exception as e:
            print(f"خطأ في توزيع الأدوار: {e}")
            return False
    
    def get_role_info(self, role: PlayerRole) -> Dict:
        """الحصول على معلومات الدور"""
        return self.role_descriptions.get(role, {})
    
    def get_team_players(self, players: List[Player], team: str) -> List[Player]:
        """الحصول على لاعبي فريق معين"""
        team_players = []
        
        for player in players:
            role_info = self.get_role_info(player.role)
            if role_info.get('team') == team:
                team_players.append(player)
        
        return team_players
    
    def get_mafia_players(self, players: List[Player]) -> List[Player]:
        """الحصول على لاعبي المافيا"""
        return [p for p in players if p.role == PlayerRole.MAFIA and p.is_alive]
    
    def get_citizen_players(self, players: List[Player]) -> List[Player]:
        """الحصول على المواطنين"""
        return [p for p in players if p.role != PlayerRole.MAFIA and p.is_alive]
    
    def get_players_with_ability(self, players: List[Player], ability: str) -> List[Player]:
        """الحصول على اللاعبين الذين يملكون قدرة معينة"""
        ability_players = []
        
        for player in players:
            if not player.is_alive:
                continue
                
            role_info = self.get_role_info(player.role)
            if ability in role_info.get('abilities', []):
                ability_players.append(player)
        
        return ability_players
    
    def can_use_ability(self, player: Player, ability: str, phase: str) -> bool:
        """التحقق من إمكانية استخدام القدرة"""
        if not player.is_alive:
            return False
        
        role_info = self.get_role_info(player.role)
        abilities = role_info.get('abilities', [])
        
        if ability not in abilities:
            return False
        
        # قواعد استخدام القدرات حسب المرحلة
        night_abilities = ['kill', 'heal', 'investigate', 'vigilante_kill']
        day_abilities = ['vote', 'double_vote']
        
        if phase == 'night' and ability in night_abilities:
            return True
        elif phase in ['day', 'voting'] and ability in day_abilities:
            return True
        
        return False
    
    def get_role_targets(self, player: Player, all_players: List[Player], ability: str) -> List[Player]:
        """الحصول على الأهداف المحتملة للدور"""
        if not self.can_use_ability(player, ability, 'night'):  # معظم القدرات ليلية
            return []
        
        targets = []
        
        if ability == 'kill':
            # المافيا يمكنهم قتل غير المافيا
            targets = [p for p in all_players if p.is_alive and p.role != PlayerRole.MAFIA and p.id != player.id]
        
        elif ability in ['heal', 'investigate', 'vigilante_kill']:
            # يمكن استهداف أي لاعب حي عدا النفس
            targets = [p for p in all_players if p.is_alive and p.id != player.id]
        
        elif ability == 'vote':
            # يمكن التصويت ضد أي لاعب حي عدا النفس
            targets = [p for p in all_players if p.is_alive and p.id != player.id]
        
        return targets
    
    def validate_role_distribution(self, distribution: Dict[PlayerRole, int]) -> Tuple[bool, str]:
        """التحقق من صحة توزيع الأدوار"""
        total_players = sum(distribution.values())
        
        if total_players < 4:
            return False, "يجب أن يكون العدد الإجمالي للاعبين 4 على الأقل"
        
        if total_players > 20:
            return False, "العدد الإجمالي للاعبين يجب ألا يزيد عن 20"
        
        mafia_count = distribution.get(PlayerRole.MAFIA, 0)
        citizen_count = total_players - mafia_count
        
        if mafia_count == 0:
            return False, "يجب أن يكون هناك لاعب مافيا واحد على الأقل"
        
        if mafia_count >= citizen_count:
            return False, "عدد المافيا يجب أن يكون أقل من عدد المواطنين"
        
        # التحقق من النسب
        mafia_ratio = mafia_count / total_players
        if mafia_ratio > 0.4:  # أكثر من 40%
            return False, "نسبة المافيا عالية جداً"
        
        if mafia_ratio < 0.2:  # أقل من 20%
            return False, "نسبة المافيا منخفضة جداً"
        
        return True, "توزيع الأدوار صحيح"
    
    def get_balanced_distribution(self, player_count: int) -> Dict[PlayerRole, int]:
        """الحصول على توزيع متوازن للأدوار"""
        try:
            distribution = self.get_role_distribution(player_count)
            is_valid, message = self.validate_role_distribution(distribution)
            
            if not is_valid:
                # محاولة إنشاء توزيع متوازن بديل
                distribution = self._generate_automatic_distribution(player_count)
                is_valid, message = self.validate_role_distribution(distribution)
                
                if not is_valid:
                    raise ValueError(f"لا يمكن إنشاء توزيع متوازن للأدوار: {message}")
            
            return distribution
            
        except Exception as e:
            print(f"خطأ في إنشاء التوزيع المتوازن: {e}")
            # توزيع افتراضي آمن
            mafia_count = max(1, player_count // 4)
            return {
                PlayerRole.MAFIA: mafia_count,
                PlayerRole.DOCTOR: 1 if player_count > 4 else 0,
                PlayerRole.CITIZEN: player_count - mafia_count - (1 if player_count > 4 else 0)
            }
    
    def get_role_summary(self, players: List[Player]) -> Dict:
        """الحصول على ملخص الأدوار"""
        role_counts = {}
        team_counts = {'mafia': 0, 'citizens': 0, 'neutral': 0}
        
        for player in players:
            if player.role:
                role_counts[player.role.value] = role_counts.get(player.role.value, 0) + 1
                
                role_info = self.get_role_info(player.role)
                team = role_info.get('team', 'neutral')
                team_counts[team] += 1
        
        return {
            'total_players': len(players),
            'role_counts': role_counts,
            'team_counts': team_counts,
            'alive_players': len([p for p in players if p.is_alive]),
            'dead_players': len([p for p in players if not p.is_alive])
        }