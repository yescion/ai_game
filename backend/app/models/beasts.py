"""Beast/Animal models"""
from typing import Optional
from pydantic import BaseModel, Field
from .base import Position2D


class BeastType:
    """Beast type definitions"""
    WOLF = {
        "name": "狼",
        "health": 50,
        "damage": 8,  # 从15降低到8
        "speed": 3,
        "aggression": 0.7,
        "group_size": (2, 5),
        "sprite": "wolf"
    }
    
    BEAR = {
        "name": "熊",
        "health": 100,
        "damage": 15,  # 从30降低到15
        "speed": 2,
        "aggression": 0.9,
        "group_size": (1, 1),
        "sprite": "bear"
    }
    
    RABBIT = {
        "name": "兔子",
        "health": 10,
        "damage": 0,
        "speed": 5,
        "aggression": 0.0,
        "group_size": (3, 8),
        "sprite": "rabbit"
    }
    
    DEER = {
        "name": "鹿",
        "health": 30,
        "damage": 5,
        "speed": 4,
        "aggression": 0.1,
        "group_size": (2, 6),
        "sprite": "deer"
    }


class BeastAction(BaseModel):
    """Beast action"""
    type: str  # idle, wander, chase, attack, flee
    target: Optional[str] = None
    direction: Optional[str] = None


class Beast(BaseModel):
    """Beast/Animal entity"""
    id: str
    type: str  # wolf, bear, rabbit, deer
    position: Position2D
    health: float = 100
    max_health: float = 100  # 最大生命值
    aggression: float = 0.5
    speed: float = 2
    damage: float = 10
    state: str = "idle"  # idle, wandering, chasing, fleeing, attacking
    target_npc: Optional[str] = None
    sprite: str = "default"
    
    # 🎬 平滑移动系统
    is_moving: bool = False
    move_target: Optional[Position2D] = None
    
    # ⏰ 攻击冷却系统
    last_attack_time: float = 0.0  # 上次攻击时间
    attack_cooldown: float = 3.0  # 攻击冷却时间（秒）
    
    def take_damage(self, amount: float) -> bool:
        """Take damage, returns True if died"""
        self.health -= amount
        return self.health <= 0
    
    def is_aggressive(self) -> bool:
        """Check if beast is aggressive"""
        return self.aggression > 0.5

