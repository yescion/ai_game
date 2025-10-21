"""Building models"""
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from .base import Position2D


class BuildingType:
    """Building type definitions"""
    
    CAMPFIRE = {
        "id": "campfire",
        "name": "篝火",
        "description": "提供光源和温暖，可烹饪食物",
        "requirements": {"wood": 5},
        "build_time": 60.0,  # 游戏时间：60秒
        "size": {"x": 1, "y": 1},
        "unlocks": ["cooking"],
        "provides_warmth": True,
        "provides_cooking": True,
        "sprite": "campfire",
        "requires_cooperation": False  # 单人可建
    }
    
    LEAN_TO = {
        "id": "lean_to",
        "name": "简易棚屋",
        "description": "基础庇护所，可过夜恢复健康",
        "requirements": {"wood": 10, "stone": 5},
        "build_time": 120.0,  # 游戏时间：2分钟
        "size": {"x": 2, "y": 2},
        "capacity": 1,
        "provides_shelter": True,
        "health_regen_bonus": 0.5,  # 休息时额外恢复50%健康
        "sprite": "lean_to",
        "requires_cooperation": False  # 单人可建
    }
    
    WOODEN_HUT = {
        "id": "wooden_hut",
        "name": "木屋",
        "description": "更好的住所，大幅恢复状态",
        "requirements": {"wood": 30, "stone": 15},
        "build_time": 240.0,  # 游戏时间：4分钟
        "size": {"x": 3, "y": 2},
        "capacity": 2,
        "prerequisites": [],  # 移除前置要求，简化游戏
        "provides_shelter": True,
        "health_regen_bonus": 1.0,  # 休息时额外恢复100%健康
        "stamina_regen_bonus": 0.5,  # 休息时额外恢复50%体力
        "sprite": "wooden_hut",
        "requires_cooperation": True  # 需要合作
    }
    
    STORAGE_SHED = {
        "id": "storage_shed",
        "name": "储物棚",
        "description": "存储资源和物品，团队共享",
        "requirements": {"wood": 20},
        "build_time": 150.0,  # 游戏时间：2.5分钟
        "size": {"x": 2, "y": 2},
        "storage_capacity": 200,  # 可存储200个物品
        "sprite": "storage",
        "requires_cooperation": False  # 单人可建
    }
    
    WORKSHOP = {
        "id": "workshop",
        "name": "工作台",
        "description": "解锁高级制作配方",
        "requirements": {"wood": 15, "stone": 10},
        "build_time": 180.0,  # 游戏时间：3分钟
        "size": {"x": 2, "y": 2},
        "unlocks": ["advanced_crafting"],
        "sprite": "workshop",
        "requires_cooperation": True  # 需要合作
    }


def get_building_type(building_id: str) -> Dict:
    """Get building type definition by ID"""
    types = {
        "campfire": BuildingType.CAMPFIRE,
        "lean_to": BuildingType.LEAN_TO,
        "wooden_hut": BuildingType.WOODEN_HUT,
        "storage_shed": BuildingType.STORAGE_SHED,
        "workshop": BuildingType.WORKSHOP
    }
    return types.get(building_id)


def get_all_building_types() -> List[str]:
    """Get list of all building types"""
    return ["campfire", "lean_to", "wooden_hut", "storage_shed", "workshop"]


class Building2D(BaseModel):
    """A building in the 2D world"""
    id: str
    type: str
    name: str
    position: Position2D
    size: Position2D
    description: str = ""
    sprite: str = "default"
    
    # Construction
    is_complete: bool = False
    construction_progress: float = 0.0  # 0.0 to 1.0
    build_time_total: float = 60.0  # Total build time in game seconds
    build_time_elapsed: float = 0.0  # Elapsed build time
    builders: List[str] = Field(default_factory=list)  # NPC IDs currently building
    requires_cooperation: bool = False  # Whether needs multiple NPCs
    
    # Properties
    capacity: int = 0  # How many NPCs can live here
    storage_capacity: int = 0
    storage: Dict[str, int] = Field(default_factory=dict)
    
    # Effects
    provides_shelter: bool = False
    provides_warmth: bool = False
    provides_cooking: bool = False  # For campfire
    health_regen_bonus: float = 0.0  # Extra health regen when resting nearby
    stamina_regen_bonus: float = 0.0  # Extra stamina regen
    unlocks: List[str] = Field(default_factory=list)
    
    def is_position_inside(self, pos: Position2D) -> bool:
        """Check if a position is inside this building"""
        return (
            self.position.x <= pos.x < self.position.x + self.size.x and
            self.position.y <= pos.y < self.position.y + self.size.y
        )
    
    def can_store(self, resource: str, amount: int) -> bool:
        """Check if can store more resources"""
        current_total = sum(self.storage.values())
        return current_total + amount <= self.storage_capacity
    
    def store(self, resource: str, amount: int) -> bool:
        """Store resources"""
        if not self.can_store(resource, amount):
            return False
        self.storage[resource] = self.storage.get(resource, 0) + amount
        return True

