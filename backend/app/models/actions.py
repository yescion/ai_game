"""Action models"""
from typing import Optional, List
from pydantic import BaseModel, Field
from .base import Position2D


class ActionType:
    """Available action types"""
    MOVE = "move"
    GATHER = "gather"
    HUNT = "hunt"
    CRAFT = "craft"
    BUILD = "build"
    EAT = "eat"
    REST = "rest"
    TALK = "talk"
    EXPLORE = "explore"
    FLEE = "flee"
    DEFEND = "defend"
    STORE = "store"  # Store items in building


class NPCAction(BaseModel):
    """An action that an NPC can perform"""
    action: str
    target: Optional[str] = None  # Target ID or coordinate string
    target_position: Optional[Position2D] = None
    description: str = ""
    reasoning: str = ""
    duration: float = 30  # seconds
    priority: str = "medium"  # low, medium, high, critical
    cooperate_with: List[str] = Field(default_factory=list)  # NPC IDs to cooperate with
    
    # Resource related
    resource_type: Optional[str] = None
    resource_amount: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True

