"""Memory service for NPCs (simplified version without vector DB)"""
import logging
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryService:
    """Simple memory service (in-memory storage)"""
    
    def __init__(self):
        # Store memories in memory (will add ChromaDB later)
        self.memories: Dict[str, List[Dict]] = defaultdict(list)
        # Track last cleanup time for each NPC
        self.last_cleanup: Dict[str, float] = {}
    
    async def retrieve_relevant_memories(
        self,
        npc_id: str,
        context: str,
        limit: int = 5
    ) -> List[Dict]:
        """Retrieve relevant memories for an NPC"""
        
        if npc_id not in self.memories:
            return []
        
        # Simple implementation: return most recent memories
        # TODO: Implement vector similarity search with ChromaDB
        recent_memories = self.memories[npc_id][-limit:]
        return recent_memories
    
    async def record_decision(self, npc_id: str, decision: Dict):
        """Record an NPC's decision"""
        memory = {
            "type": "decision",
            "description": f"决定: {decision.get('action', 'unknown')} - {decision.get('reasoning', '')}",
            "data": decision
        }
        self.memories[npc_id].append(memory)
        
        # Keep only last 30 memories
        if len(self.memories[npc_id]) > 30:
            self.memories[npc_id] = self.memories[npc_id][-30:]
    
    async def record_event(self, npc_id: str, event_type: str, description: str, importance: int = 5):
        """Record an event in NPC's memory
        
        Args:
            npc_id: NPC identifier
            event_type: Type of event
            description: Memory description
            importance: Importance score 1-10 (default 5)
        """
        memory = {
            "type": event_type,
            "description": description,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        }
        self.memories[npc_id].append(memory)
        
        if len(self.memories[npc_id]) > 30:
            self.memories[npc_id] = self.memories[npc_id][-30:]
    
    def get_all_memories(self, npc_id: str) -> List[Dict]:
        """Get all memories for an NPC"""
        return self.memories.get(npc_id, [])
    
    async def cleanup_memories(self, npc_id: str, memory_evaluation: Dict[str, int]):
        """Clean up memories based on AI evaluation
        
        Args:
            npc_id: NPC identifier
            memory_evaluation: Dict mapping memory index to importance score (1-10)
        """
        if npc_id not in self.memories:
            return
        
        memories = self.memories[npc_id]
        
        # 更新记忆的重要性分数
        for idx, importance in memory_evaluation.items():
            idx_int = int(idx)
            if 0 <= idx_int < len(memories):
                memories[idx_int]["importance"] = importance
        
        # 按重要性排序，保留前20条最重要的记忆
        # 为每条记忆添加索引（用于保持原始顺序）
        memories_with_idx = [(i, m) for i, m in enumerate(memories)]
        
        # 按重要性降序排序
        memories_with_idx.sort(key=lambda x: x[1].get("importance", 5), reverse=True)
        
        # 保留前20条最重要的
        top_memories_idx = set(idx for idx, _ in memories_with_idx[:20])
        
        # 同时保留所有重要性>=7的记忆（永久记忆）
        important_memories = []
        for i, memory in enumerate(memories):
            importance = memory.get("importance", 5)
            if importance >= 7 or i in top_memories_idx:
                important_memories.append(memory)
        
        # 更新记忆列表
        self.memories[npc_id] = important_memories
        
        cleaned_count = len(memories) - len(important_memories)
        if cleaned_count > 0:
            logger.info(f"🧹 {npc_id} 清理了 {cleaned_count} 条不重要的记忆，保留 {len(important_memories)} 条")
    
    async def should_cleanup(self, npc_id: str, current_time: float, cleanup_interval: float = 300.0) -> bool:
        """Check if NPC should clean up memories
        
        Args:
            npc_id: NPC identifier
            current_time: Current game time
            cleanup_interval: Time interval between cleanups (default 300 game seconds = 5 game minutes)
        
        Returns:
            True if cleanup is needed
        """
        # 检查记忆数量
        memory_count = len(self.memories.get(npc_id, []))
        if memory_count < 30:
            return False  # 记忆太少，不需要清理
        
        # 检查时间间隔
        last_cleanup_time = self.last_cleanup.get(npc_id, 0)
        if current_time - last_cleanup_time >= cleanup_interval:
            self.last_cleanup[npc_id] = current_time
            return True
        
        return False

