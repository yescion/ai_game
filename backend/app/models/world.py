"""World state models"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .npc import NPC2D
from .buildings import Building2D
from .resources import ResourceNode
from .beasts import Beast
from .conversation import Conversation


class TimeSystem(BaseModel):
    """Game time system"""
    day: int = 1
    hour: int = 8
    minute: float = 0
    season: str = "spring"  # spring, summer, autumn, winter
    
    def is_night(self) -> bool:
        """Check if it's nighttime"""
        return self.hour >= 20 or self.hour < 6
    
    def is_dangerous_time(self) -> bool:
        """Check if it's a dangerous time"""
        return self.is_night()
    
    def get_current_time(self) -> float:
        """Get current time as a float (for comparisons)"""
        return self.day * 24 * 60 + self.hour * 60 + self.minute
    
    def format_time(self) -> str:
        """Format time as a string for logs"""
        return f"Day {self.day}, {self.hour:02d}:{int(self.minute):02d}"
    
    def __str__(self) -> str:
        return self.format_time()


class GameEvent(BaseModel):
    """Game event"""
    id: str
    type: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.now)
    importance: Optional[str] = None  # low, medium, high, critical
    related_npcs: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorldState2D(BaseModel):
    """Complete world state"""
    # Basic info
    width: int = 100
    height: int = 100
    
    # Time
    time: TimeSystem = Field(default_factory=TimeSystem)
    
    # Weather
    weather: str = "clear"  # clear, cloudy, rain, storm
    
    # Entities
    npcs: List[NPC2D] = Field(default_factory=list)
    buildings: List[Building2D] = Field(default_factory=list)
    resources: List[ResourceNode] = Field(default_factory=list)
    beasts: List[Beast] = Field(default_factory=list)
    
    # Social
    conversations: List[Conversation] = Field(default_factory=list)
    
    # Events
    events: List[GameEvent] = Field(default_factory=list)
    
    # Global resources (collected and stored)
    global_resources: Dict[str, int] = Field(default_factory=lambda: {
        "wood": 0,
        "stone": 0,
        "berry": 0,
        "water": 0,
        "meat": 0
    })
    
    # Spawn point
    spawn_point: Optional[tuple] = Field(default=(50, 50))
    
    class Config:
        arbitrary_types_allowed = True
    
    def get_npc_by_id(self, npc_id: str) -> Optional[NPC2D]:
        """Get NPC by ID"""
        for npc in self.npcs:
            if npc.id == npc_id:
                return npc
        return None
    
    def add_event(self, event: GameEvent):
        """Add an event to the world"""
        self.events.append(event)
        # Keep only last 100 events
        if len(self.events) > 100:
            self.events = self.events[-100:]

