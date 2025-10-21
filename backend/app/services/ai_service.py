"""AI Service for NPC decision making"""
import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from openai import OpenAI

from app.models.npc import NPC2D
from app.models.world import WorldState2D
from app.models.actions import NPCAction
from app.prompts.npc_decision_prompt import generate_npc_decision_prompt

logger = logging.getLogger(__name__)

# 🔥 创建日志目录
NPC_LOG_DIR = Path("logs/npc_decisions")
NPC_LOG_DIR.mkdir(parents=True, exist_ok=True)


class AIService:
    """AI service for generating NPC decisions"""
    
    def __init__(self):
        api_key = os.getenv('DEEPSEEK_API_KEY')
        base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY not set, AI features will be limited")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
    
    async def generate_npc_decision(
        self,
        npc: NPC2D,
        world_state: WorldState2D,
        memories: List[Dict] = None
    ) -> NPCAction:
        """Generate a decision for an NPC"""
        
        if not self.client:
            # Fallback to simple rule-based decision
            return self._fallback_decision(npc, world_state)
        
        try:
            # Generate prompt
            prompt = generate_npc_decision_prompt(npc, world_state, memories or [])
            
            # 🔥 记录请求开始时间
            request_time = datetime.now()
            
            # Call AI
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个在原始平原上生存的NPC。请根据当前状况做出合理的决策，优先考虑生存需求。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            # Parse response
            decision_text = response.choices[0].message.content
            decision_dict = self._parse_decision(decision_text)
            
            # Create NPCAction
            action = NPCAction(
                action=decision_dict.get("action", "rest"),
                target=decision_dict.get("target"),
                reasoning=decision_dict.get("reasoning", "AI决策"),
                duration=decision_dict.get("duration", 30),
                priority=decision_dict.get("priority", "medium"),
                cooperate_with=decision_dict.get("cooperate_with", [])
            )
            
            # 🔥 记录到NPC专属日志文件
            self._log_npc_decision(npc, prompt, decision_text, action, request_time)
            
            # 🔥 减少日志输出（前端已有显示）
            logger.debug(f"[AI决策] {npc.name}: {action.action} - {action.reasoning}")
            return action
            
        except Exception as e:
            logger.error(f"AI decision failed for {npc.name}: {e}")
            return self._fallback_decision(npc, world_state)
    
    def _parse_decision(self, decision_text: str) -> Dict[str, Any]:
        """Parse AI response to extract decision"""
        try:
            # Try to extract JSON from response
            if "```json" in decision_text:
                json_start = decision_text.find("```json") + 7
                json_end = decision_text.find("```", json_start)
                decision_text = decision_text[json_start:json_end].strip()
            elif "```" in decision_text:
                json_start = decision_text.find("```") + 3
                json_end = decision_text.find("```", json_start)
                decision_text = decision_text[json_start:json_end].strip()
            
            # Try to find JSON object
            if "{" in decision_text and "}" in decision_text:
                json_start = decision_text.find("{")
                json_end = decision_text.rfind("}") + 1
                decision_text = decision_text[json_start:json_end]
            
            decision = json.loads(decision_text)
            return decision
            
        except Exception as e:
            logger.error(f"Failed to parse AI decision: {e}")
            logger.debug(f"Decision text was: {decision_text}")
            return {
                "action": "rest",
                "reasoning": "决策解析失败",
                "duration": 30
            }
    
    def _fallback_decision(self, npc: NPC2D, world_state: WorldState2D) -> NPCAction:
        """Fallback rule-based decision when AI is unavailable"""
        
        # Critical health
        if npc.attributes.health < 30:
            return NPCAction(
                action="rest",
                reasoning="生命值过低，需要休息恢复",
                duration=60,
                priority="critical"
            )
        
        # Very hungry
        if npc.attributes.hunger > 80:
            # Look for food in inventory
            if npc.inventory.get("berry", 0) > 0:
                return NPCAction(
                    action="eat",
                    target="berry",
                    reasoning="非常饥饿，吃浆果",
                    duration=10,
                    priority="high"
                )
            # Find berry bush
            nearby_berries = [
                r for r in world_state.resources
                if r.type == "berry" and
                npc.position.distance_to(r.position) < 20
            ]
            if nearby_berries:
                closest = min(nearby_berries, key=lambda r: npc.position.distance_to(r.position))
                return NPCAction(
                    action="gather",
                    target=closest.id,
                    target_position=closest.position,
                    reasoning="寻找浆果充饥",
                    duration=30,
                    priority="high"
                )
        
        # Low stamina
        if npc.attributes.stamina < 20:
            return NPCAction(
                action="rest",
                reasoning="体力不足，需要休息",
                duration=40,
                priority="medium"
            )
        
        # Default: gather resources
        nearby_wood = [
            r for r in world_state.resources
            if r.type == "wood" and
            npc.position.distance_to(r.position) < 30
        ]
        
        if nearby_wood:
            closest = min(nearby_wood, key=lambda r: npc.position.distance_to(r.position))
            return NPCAction(
                action="gather",
                target=closest.id,
                target_position=closest.position,
                reasoning="采集木材",
                duration=40,
                priority="medium"
            )
        
        # Wander/explore
        return NPCAction(
            action="explore",
            reasoning="探索周围环境",
            duration=50,
            priority="low"
        )
    
    def _log_npc_decision(self, npc: NPC2D, prompt: str, response: str, action: NPCAction, timestamp: datetime):
        """记录NPC决策到专属日志文件"""
        try:
            # 生成日志文件名（按NPC名称）
            log_file = NPC_LOG_DIR / f"{npc.name}.log"
            
            # 准备日志内容
            log_entry = f"""
{'='*80}
时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
NPC: {npc.name} (ID: {npc.id})
位置: ({npc.position.x:.1f}, {npc.position.y:.1f})
状态: 健康={npc.attributes.health:.0f}, 饱食度={100-npc.attributes.hunger:.0f}, 体力={npc.attributes.stamina:.0f}

{'='*80}
【发送给AI的Prompt】
{'='*80}
{prompt}

{'='*80}
【AI返回的Response】
{'='*80}
{response}

{'='*80}
【解析后的决策】
{'='*80}
行动类型: {action.action}
目标: {action.target or 'None'}
理由: {action.reasoning}
持续时间: {action.duration}秒
优先级: {action.priority}
{'='*80}

"""
            
            # 追加写入文件
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            logger.debug(f"📝 已记录 {npc.name} 的决策日志到 {log_file}")
            
        except Exception as e:
            logger.error(f"记录NPC决策日志失败: {e}")
    
    async def evaluate_memory_importance(self, npc: NPC2D, memories: List[Dict]) -> Dict[str, int]:
        """让AI评估记忆的重要性
        
        Args:
            npc: NPC对象
            memories: 记忆列表
        
        Returns:
            Dict mapping memory index to importance score (1-10)
        """
        if not self.client or not memories:
            return {}
        
        try:
            # 构建记忆列表文本
            memory_list = []
            for i, memory in enumerate(memories):
                desc = memory.get('description', '未知记忆')
                memory_list.append(f"{i}. {desc}")
            
            memory_text = "\n".join(memory_list)
            
            prompt = f"""你是 {npc.name}，现在需要整理你的记忆。

以下是你的所有记忆（共{len(memories)}条）：
{memory_text}

请评估每条记忆的重要性，给出1-10的分数：
- 1-2分：完全不重要，可以遗忘（如：重复的信息、过时的观察）
- 3-4分：不太重要，可能遗忘（如：日常琐事、普通移动）
- 5-6分：一般重要，保留（如：普通采集、一般交流）
- 7-8分：比较重要，必须保留（如：危险遭遇、重要决策、工具制造）
- 9-10分：非常重要，永久保留（如：生死经历、重大事件、关键发现）

评估标准：
- 与生存相关的记忆（危险、受伤、饥饿）→ 高分
- 重要的社交互动（合作、冲突、分享）→ 中高分
- 成功的制造/建造/狩猎 → 中高分
- 失败经验（如材料不足）如果重复多次 → 低分（学到教训就够了）
- 普通的采集、移动、观察 → 低分
- 重复的信息 → 低分

以JSON格式回复，只包含需要调整分数的记忆索引：
{{
    "0": 8,
    "5": 2,
    "12": 9
}}

如果某条记忆可以保持默认重要性(5分)，就不用列出。
"""
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个帮助NPC整理记忆的助手。请客观评估每条记忆的重要性。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 降低温度以获得更一致的评分
                max_tokens=500
            )
            
            evaluation_text = response.choices[0].message.content
            
            # 🔥 记录记忆评估日志
            self._log_memory_evaluation(npc, prompt, evaluation_text, datetime.now())
            
            # 解析JSON
            try:
                # 尝试提取JSON
                import json
                import re
                
                # 查找JSON块
                json_match = re.search(r'\{[^{}]*\}', evaluation_text)
                if json_match:
                    evaluation = json.loads(json_match.group())
                    logger.info(f"🧠 {npc.name} 评估了记忆重要性: {len(evaluation)} 条需要调整")
                    return evaluation
                else:
                    logger.warning(f"无法从AI响应中提取JSON: {evaluation_text}")
                    return {}
            
            except Exception as parse_error:
                logger.error(f"解析记忆评估失败: {parse_error}")
                return {}
        
        except Exception as e:
            logger.error(f"AI记忆评估失败: {e}")
            return {}
    
    def _log_memory_evaluation(self, npc: NPC2D, prompt: str, response: str, timestamp: datetime):
        """记录NPC记忆评估到日志文件"""
        try:
            # 使用与决策相同的日志目录
            log_file = NPC_LOG_DIR / f"{npc.name}_memory.log"
            
            # 准备日志内容
            log_entry = f"""
{'='*80}
时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
NPC: {npc.name} (ID: {npc.id})
记忆管理: 评估记忆重要性

{'='*80}
【发送给AI的Prompt】
{'='*80}
{prompt}

{'='*80}
【AI返回的Response】
{'='*80}
{response}

{'='*80}

"""
            
            # 追加写入文件
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            logger.debug(f"📝 已记录 {npc.name} 的记忆评估日志到 {log_file}")
            
        except Exception as e:
            logger.error(f"记录NPC记忆评估日志失败: {e}")
    
    async def generate_conversation_summary(
        self,
        participant_names: List[str],
        participants_info: List[str],
        topic: str,
        duration: float
    ) -> Dict[str, any]:
        """生成对话的具体内容和每个参与者的记忆
        
        Returns:
            {
                'summary': '对话摘要',
                'npc_id1': {'memory': '从自己角度的记忆'},
                'npc_id2': {'memory': '从自己角度的记忆'},
                ...
            }
        """
        if not self.client:
            return {
                'summary': f"关于{topic}的对话"
            }
        
        try:
            participants_str = "\n".join([f"- {info}" for info in participants_info])
            names_str = "、".join(participant_names)
            
            prompt = f"""
{names_str}进行了一次对话，持续了约{duration:.0f}秒。

对话话题: {topic}

参与者状态:
{participants_str}

请生成这次对话的具体内容：
1. 他们具体讨论了什么？交换了哪些有用信息？
2. 根据每个人的状态和装备，他们可能分享了什么实用信息？
   - 有装备的人可能分享制造经验
   - 库存多的人可能提供资源线索
   - 状态好的人可能提供生存建议
3. 对话要简短实用，不要空谈

⚠️ 重要：对话内容要对未来决策有帮助！例如：
- "Alice告诉Bob石斧制造需要3石头2木头，并且装备石斧后采集木材效率更高"
- "Charlie分享了西边有大片浆果丛的信息，建议大家饱食度低时可以去那里"
- "Diana提醒大家东北方向有狼群出没，建议组队行动更安全"

以JSON格式回复：
{{
    "summary": "简短总结对话内容和收获(20-40字)",
    "{participant_names[0]}": "从{participant_names[0]}角度，记录对自己有用的信息(30-60字)",
    "{participant_names[1]}": "从{participant_names[1]}角度，记录对自己有用的信息(30-60字)"
}}

记住：每个人的记忆要记录对【自己】有用的具体信息！
"""
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个对话内容生成助手。生成简短、实用、对未来决策有帮助的对话内容。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            
            # 解析JSON
            try:
                import json
                import re
                
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    logger.info(f"💬 生成了对话内容摘要")
                    return result
                else:
                    logger.warning(f"无法从对话响应中提取JSON")
                    return {'summary': f"关于{topic}的对话"}
            
            except Exception as parse_error:
                logger.error(f"解析对话内容失败: {parse_error}")
                return {'summary': f"关于{topic}的对话"}
        
        except Exception as e:
            logger.error(f"AI生成对话内容失败: {e}")
            return {'summary': f"关于{topic}的对话"}
    
    async def generate_conversation_dialogue(
        self,
        initiator: NPC2D,
        partners: List[NPC2D],
        world_state: WorldState2D
    ) -> Dict[str, Any]:
        """
        生成真实的NPC对话内容和类型
        
        返回格式:
        {
            "conversation_type": "greeting|small_talk|info_exchange|plan_discussion|warning|resource_share|cooperation",
            "topic": "对话主题",
            "messages": [
                {"speaker": "NPC名称", "content": "对话内容"},
                ...
            ],
            "triggers_action": true/false,
            "planned_action": {"action": "build", "target": "lean_to", "reason": "..."}  # 如果触发行动
        }
        """
        if not self.client:
            return self._fallback_conversation(initiator, partners)
        
        try:
            # 构建对话生成提示词
            prompt = self._build_conversation_prompt(initiator, partners, world_state)
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个NPC对话生成助手。生成真实、自然的对话内容。
                        
规则:
1. 对话内容要基于NPC的记忆和当前状态
2. 对话要自然、真实，像真人交流一样
3. 根据情况决定对话类型和是否触发后续行动
4. 对话类型:
   - greeting: 打招呼（不触发行动）
   - small_talk: 闲聊（不触发行动）
   - info_exchange: 交换信息（可能触发行动）
   - plan_discussion: 商讨计划（触发行动）
   - warning: 警告危险（可能触发行动）
   - resource_share: 资源交换（触发行动）
   - cooperation: 合作请求（触发行动）

返回JSON格式，每个NPC说2-3句话。"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"💬 AI对话生成原始响应: {response_text[:200]}...")
            
            # 解析JSON
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    logger.info(f"💬 成功生成{result.get('conversation_type')}类型对话")
                    return result
                else:
                    logger.warning(f"无法从对话响应中提取JSON")
                    return self._fallback_conversation(initiator, partners)
            
            except Exception as parse_error:
                logger.error(f"解析对话内容失败: {parse_error}")
                return self._fallback_conversation(initiator, partners)
        
        except Exception as e:
            logger.error(f"AI生成对话失败: {e}")
            return self._fallback_conversation(initiator, partners)
    
    def _build_conversation_prompt(self, initiator: NPC2D, partners: List[NPC2D], world_state: WorldState2D) -> str:
        """构建对话生成提示词"""
        all_npcs = [initiator] + partners
        
        prompt = f"""生成以下NPCs的对话:

"""
        
        for i, npc in enumerate(all_npcs):
            prompt += f"""
【NPC{i+1}: {npc.name}】
- 性格: 勇敢度{npc.personality.bravery}, 社交性{npc.personality.sociability}, 勤奋度{npc.personality.diligence}
- 状态: 健康{npc.attributes.health}, 饱食度{npc.attributes.hunger}
- 装备: {', '.join(npc.equipment) if npc.equipment else '无'}
- 库存: {', '.join([f"{k}×{v}" for k,v in npc.inventory.items() if v > 0]) if npc.inventory else '无'}
- 最近记忆: {'; '.join(npc.memories[-3:]) if npc.memories else '无'}
"""
        
        # 环境信息
        prompt += f"""

【环境状况】
- 时间: {world_state.time.format_time()}
- 天气: {world_state.weather}
- 建筑: {len([b for b in world_state.buildings if b.is_complete])}个已完成
- 未完成建筑: {len([b for b in world_state.buildings if not b.is_complete])}个
- 野兽威胁: {'是' if any(b.is_aggressive() for b in world_state.beasts) else '否'}

请生成真实的对话内容（每人2-3句话），并决定对话类型和是否触发后续行动。

返回JSON格式:
{{
    "conversation_type": "对话类型（见系统提示）",
    "topic": "对话主题",
    "messages": [
        {{"speaker": "NPC名称", "content": "对话内容"}},
        {{"speaker": "NPC名称", "content": "对话内容"}},
        ...
    ],
    "triggers_action": true或false,
    "planned_action": {{"action": "行动类型", "target": "目标", "reason": "原因"}}  // 如果triggers_action为true
}}
"""
        return prompt
    
    def _fallback_conversation(self, initiator: NPC2D, partners: List[NPC2D]) -> Dict[str, Any]:
        """备用对话生成（AI不可用时）"""
        return {
            "conversation_type": "greeting",
            "topic": "打招呼",
            "messages": [
                {"speaker": initiator.name, "content": f"你好！"},
                {"speaker": partners[0].name, "content": f"嗨，{initiator.name}！"}
            ],
            "triggers_action": False
        }

