"""Resource models"""
from pydantic import BaseModel, Field
from .base import Position2D


class ResourceType:
    """Resource type definitions"""
    WOOD = {
        "name": "木材",
        "gathering_time": 5,
        "tool_required": "axe",
        "skill": "woodcutting",
        "yield_range": (1, 3),
        "sprite": "tree"
    }
    
    STONE = {
        "name": "石头",
        "gathering_time": 8,
        "tool_required": "pickaxe",
        "skill": "mining",
        "yield_range": (1, 2),
        "sprite": "rock"
    }
    
    BERRY = {
        "name": "浆果",
        "gathering_time": 3,
        "tool_required": None,
        "skill": "foraging",
        "yield_range": (2, 5),
        "sprite": "berry_bush",
        "edible": True,
        "nutrition": 20
    }
    
    WATER = {
        "name": "水源",
        "gathering_time": 2,
        "tool_required": "container",
        "skill": None,
        "yield_range": (1, 1),
        "sprite": "water",
        "drinkable": True
    }


class ResourceNode(BaseModel):
    """A resource node in the world"""
    id: str
    type: str  # wood, stone, berry, water
    position: Position2D
    quantity: int = 100
    max_quantity: int = 100
    regeneration_rate: float = 0.1  # Per game hour
    quality: int = Field(default=3, ge=1, le=5)
    is_depleted: bool = False  # 🔥 新增：资源是否枯竭
    depleted_time: float = 0.0  # 🔥 新增：枯竭时间（游戏时间）
    occupied_by: str | None = None  # 🎯 资源点占用者（NPC ID）
    
    def gather(self, amount: int = 1) -> int:
        """Gather from this resource"""
        actual_amount = min(amount, self.quantity)
        self.quantity -= actual_amount
        
        # 🔥 检查是否枯竭
        if self.quantity <= 0:
            self.is_depleted = True
        
        return actual_amount
    
    def regenerate(self):
        """Regenerate resource"""
        if self.quantity < self.max_quantity:
            self.quantity = min(
                self.max_quantity,
                self.quantity + int(self.regeneration_rate)
            )

