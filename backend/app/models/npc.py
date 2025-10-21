"""NPC data models"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .base import Position2D


class NPCAttributes(BaseModel):
    """NPC attributes"""
    health: float = Field(default=100, ge=0, le=100)
    hunger: float = Field(default=0, ge=0, le=100)
    stamina: float = Field(default=100, ge=0, le=100)
    temperature: float = Field(default=37.0, ge=20, le=42)  # Body temperature


class NPCRole(BaseModel):
    """NPC role/profession"""
    role: str = "新手"
    description: str = "还在探索自己的专长"
    suggested_tasks: List[str] = Field(default_factory=list)


class NPCPersonality(BaseModel):
    """NPC personality traits"""
    personality_type: str = "平衡型"  # 性格类型
    description: str = ""  # 性格描述
    
    # 性格特质（0-100）
    bravery: int = Field(default=50, ge=0, le=100)  # 勇敢度
    sociability: int = Field(default=50, ge=0, le=100)  # 社交性
    cautiousness: int = Field(default=50, ge=0, le=100)  # 谨慎度
    curiosity: int = Field(default=50, ge=0, le=100)  # 好奇心
    cooperation: int = Field(default=50, ge=0, le=100)  # 合作性
    ambition: int = Field(default=50, ge=0, le=100)  # 进取心


class NPC2D(BaseModel):
    """NPC in the 2D world"""
    id: str
    name: str
    position: Position2D
    direction: str = "down"  # up, down, left, right
    sprite: str = "default"
    
    # Attributes
    attributes: NPCAttributes = Field(default_factory=NPCAttributes)
    
    # Skills (0-100)
    skills: Dict[str, float] = Field(default_factory=lambda: {
        "woodcutting": 0,
        "mining": 0,
        "foraging": 0,
        "combat": 0,
        "construction": 0,
        "crafting": 0,
        "social": 0,
        "survival": 0
    })
    
    # Inventory (resources)
    inventory: Dict[str, int] = Field(default_factory=dict)
    
    # 🔧 Equipment/Tools (装备/工具系统)
    equipment: Dict[str, Dict] = Field(default_factory=dict)  # tool_name -> {durability, quality, crafted_at}
    
    # Current state
    current_action: Optional[str] = None
    action_target: Optional[str] = None
    action_end_time: Optional[float] = None
    reasoning: Optional[str] = None
    action_state: str = "idle"  # idle, moving, executing, cooling
    action_start_time: Optional[float] = None
    action_duration: float = 0.0  # 行动持续时间（用于计算进度）
    
    # 🔥 生存状态
    is_alive: bool = True  # 是否存活
    
    # 🔥 移动系统字段
    is_moving: bool = False  # 是否正在移动
    move_target: Optional[Position2D] = None  # 移动目标位置
    move_speed: float = 2.0  # 移动速度（单位/秒）
    
    # 🔥 待办事项和日志系统
    current_todo: Optional[str] = None  # 当前待办事项描述
    todo_steps: List[str] = Field(default_factory=list)  # 待办步骤列表
    action_log: List[str] = Field(default_factory=list)  # 行动日志（最近20条）
    memories: List[str] = Field(default_factory=list)  # 事件记忆（最近50条）
    
    # 🎯 上次行动结果反馈（用于AI决策）
    last_action_result: Optional[str] = None  # 上次行动的执行结果（成功/失败及详细原因）
    
    # 💬 社交会话系统
    in_conversation: bool = False  # 是否正在对话中
    conversation_id: Optional[str] = None  # 当前参与的对话ID
    conversation_partners: List[str] = Field(default_factory=list)  # 对话伙伴的NPC ID列表
    
    # Role
    role: NPCRole = Field(default_factory=NPCRole)
    
    # 🎭 Personality (性格系统)
    personality: NPCPersonality = Field(default_factory=NPCPersonality)
    
    # Relationships
    relationships: Dict[str, float] = Field(default_factory=dict)  # npc_id -> affinity (-100 to 100)
    
    class Config:
        arbitrary_types_allowed = True
    
    def is_idle(self, current_time: float) -> bool:
        """Check if NPC is idle"""
        return not self.current_action or (
            self.action_end_time and self.action_end_time <= current_time
        )
    
    def needs_urgent_action(self) -> bool:
        """Check if NPC needs urgent action"""
        return (
            self.attributes.health < 30 or
            self.attributes.hunger > 80 or
            self.attributes.stamina < 10
        )

