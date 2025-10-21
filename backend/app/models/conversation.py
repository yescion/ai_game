"""Conversation system models"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ConversationType(str, Enum):
    """对话类型枚举"""
    GREETING = "greeting"  # 打招呼（不触发行动）
    SMALL_TALK = "small_talk"  # 闲聊（不触发行动）
    INFO_EXCHANGE = "info_exchange"  # 交换信息（可能触发行动）
    PLAN_DISCUSSION = "plan_discussion"  # 商讨计划（触发行动）
    WARNING = "warning"  # 警告危险（可能触发行动）
    RESOURCE_SHARE = "resource_share"  # 资源交换（触发行动）
    COOPERATION = "cooperation"  # 合作请求（触发行动）


class ConversationMessage(BaseModel):
    """A message in a conversation"""
    speaker_id: str
    speaker_name: str
    content: str
    timestamp: float


class Conversation(BaseModel):
    """A conversation between NPCs"""
    id: str
    participants: List[str]  # NPC IDs
    participant_names: List[str]  # NPC names for display
    messages: List[ConversationMessage] = Field(default_factory=list)
    conversation_type: Optional[ConversationType] = None  # 🔥 对话类型
    topic: Optional[str] = None
    started_at: float
    ended_at: Optional[float] = None
    is_active: bool = True
    location: Dict[str, float] = Field(default_factory=dict)  # {x, y} where conversation happens
    triggers_action: bool = False  # 🔥 是否触发后续行动
    planned_action: Optional[Dict] = None  # 🔥 计划的行动内容
    
    def add_message(self, speaker_id: str, speaker_name: str, content: str, timestamp: float):
        """Add a message to the conversation"""
        self.messages.append(ConversationMessage(
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            content=content,
            timestamp=timestamp
        ))
    
    def get_summary(self) -> str:
        """Get a summary of the conversation"""
        if not self.messages:
            return f"{', '.join(self.participant_names)} 开始了对话"
        
        summary = f"{', '.join(self.participant_names)} 的对话:\n"
        for msg in self.messages[-3:]:  # Last 3 messages
            summary += f"  - {msg.speaker_name}: {msg.content[:50]}...\n"
        return summary
    
    def end_conversation(self, timestamp: float):
        """End the conversation"""
        self.is_active = False
        self.ended_at = timestamp

