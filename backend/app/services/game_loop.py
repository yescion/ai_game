"""Main game loop"""
import asyncio
import time
import logging
import uuid
import random
import math
from typing import Dict, Optional, List

from app.models.world import WorldState2D, GameEvent
from app.models.npc import NPC2D
from app.models.base import Position2D
from app.models.crafting import get_recipe, can_craft, consume_materials, get_all_craftable_items
from app.models.conversation import Conversation, ConversationMessage
from app.services.ai_service import AIService
from app.services.memory_service import MemoryService
from app.services.world_generator import WorldGenerator
from app.services.physics_engine import PhysicsEngine, VisionSystem, MovementSystem  # 🔥 新增

logger = logging.getLogger(__name__)


class GameConfig:
    """Game configuration"""
    def __init__(
        self,
        map_width: int = 100,
        map_height: int = 100,
        initial_npc_count: int = 5,
        time_scale: float = 60.0  # 1 second real = 60 seconds game
    ):
        self.map_width = map_width
        self.map_height = map_height
        self.initial_npc_count = initial_npc_count
        self.time_scale = time_scale


class MainGameLoop:
    """Main game loop coordinating all systems"""
    
    def __init__(self):
        self.world_state: Optional[WorldState2D] = None
        self.ai_service = AIService()
        self.memory_service = MemoryService()
        self.world_generator = WorldGenerator()
        
        # 🔥 物理引擎系统
        self.physics_engine = PhysicsEngine()
        self.vision_system = VisionSystem(self.physics_engine)
        self.movement_system = MovementSystem(self.physics_engine)
        
        self.is_running = False
        self.game_started = False  # 游戏是否已开始主循环
        self.waiting_for_client = True  # 是否在等待客户端连接
        self.tick_interval = 1.0  # Process every second
        self.time_scale = 60.0  # 1 second real = 60 seconds game
        
        # Decision interval (avoid too frequent AI calls)
        self.npc_decision_interval = 30  # 30 game seconds
        self.npc_last_decision: Dict[str, float] = {}
        
        # 🐺 Beast decision interval (same as NPC)
        self.beast_decision_interval = 30  # 30 game seconds
        self.beast_last_decision: Dict[str, float] = {}
        
        # 💬 Conversation management
        self.active_conversations: Dict[str, Conversation] = {}  # conversation_id -> Conversation
        
        # 🌦️ Weather tracking
        self.last_weather_check = 0  # Track last weather check time
        self.weather_check_interval = 1800  # 30 minutes game time
        
        # Broadcast callback
        self.broadcast_callback = None
    
    def set_broadcast_callback(self, callback):
        """Set callback for broadcasting updates"""
        self.broadcast_callback = callback
    
    def on_client_connected(self):
        """Called when first client connects"""
        if self.waiting_for_client:
            self.waiting_for_client = False
            logger.info("🎮 ✅ Client ready signal received! Game will start now!")
        else:
            logger.info("ℹ️ Client ready signal received (game already started)")
    
    async def start_game(self, config: GameConfig):
        """Start the game"""
        logger.info("Starting game...")
        
        # Generate world
        self.world_state = self.world_generator.generate_world(
            width=config.map_width,
            height=config.map_height
        )
        
        self.time_scale = config.time_scale
        
        # Generate initial NPCs
        npc_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
        spawn_x, spawn_y = self.world_state.spawn_point
        
        for i in range(config.initial_npc_count):
            name = npc_names[i] if i < len(npc_names) else f"NPC_{i+1}"
            # Spawn in a small area around spawn point
            pos = Position2D(
                x=spawn_x + (i - config.initial_npc_count // 2) * 2,
                y=spawn_y + ((i % 3) - 1) * 2
            )
            npc = self.world_generator.generate_npc(name, pos)
            self.world_state.npcs.append(npc)
            
            logger.info(f"Created NPC: {npc.name} at {npc.position}")
        
        # Add spawn event
        self.world_state.add_event(GameEvent(
            id=f"event_{uuid.uuid4().hex[:8]}",
            type="game_start",
            description=f"{len(self.world_state.npcs)}个NPC来到了原始平原",
            importance="high"
        ))
        
        # Broadcast initial state
        await self.broadcast_world_state()
        
        # 🔥 等待客户端连接（无限等待，直到客户端连接）
        logger.info("✅ Game initialized, waiting for client connection...")
        logger.info("💡 Backend is ready. Waiting indefinitely for frontend to connect...")
        logger.info("📌 Game will NOT start until frontend sends 'client_ready' signal")
        
        wait_time = 0
        while self.waiting_for_client:
            await asyncio.sleep(0.5)
            wait_time += 0.5
            
            # 每30秒提示一次
            if wait_time % 30 == 0:
                logger.info(f"⏰ Still waiting for client... ({wait_time:.0f}s elapsed)")
                logger.info("   💡 Tip: Make sure frontend is running on http://localhost:5173")
        
        logger.info("🎮 ✅ Client connected! Starting game loop now!")
        
        # Start main loop
        self.is_running = True
        self.game_started = True
        asyncio.create_task(self.main_loop())
        
        logger.info("Game started successfully!")
    
    async def main_loop(self):
        """Main game loop"""
        last_time = time.time()
        
        while self.is_running:
            try:
                current_time = time.time()
                delta_time = current_time - last_time
                last_time = current_time
                
                # Update game time
                self.update_time(delta_time)
                
                # 🌦️ Update weather (every 30-60 minutes game time for realistic changes)
                game_time = self.world_state.time.get_current_time()
                # 随机间隔30-60分钟检查天气变化，模拟真实天气的不确定性
                if game_time - self.last_weather_check >= self.weather_check_interval:  # 30 minutes minimum
                    if random.random() < 0.5:  # 50%概率真正改变
                        self.update_weather()
                        self.last_weather_check = game_time
                    else:
                        self.last_weather_check += 600  # 再等10分钟
                
                # Process NPCs
                await self.process_npcs()
                
                # Process beasts (simplified)
                await self.process_beasts()
                
                # Process resources (regeneration)
                self.process_resources()
                
                # Process buildings
                self.process_buildings()
                
                # Broadcast update (every tick)
                await self.broadcast_world_update()
                
                # Wait for next tick
                await asyncio.sleep(self.tick_interval)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(self.tick_interval)
    
    def update_time(self, delta_time: float):
        """Update game time"""
        if not self.world_state:
            return
        
        # Convert real time to game time
        game_minutes = delta_time * (self.time_scale / 60)
        
        self.world_state.time.minute += game_minutes
        
        # Handle time overflow
        if self.world_state.time.minute >= 60:
            self.world_state.time.hour += int(self.world_state.time.minute // 60)
            self.world_state.time.minute = self.world_state.time.minute % 60
        
        if self.world_state.time.hour >= 24:
            self.world_state.time.day += int(self.world_state.time.hour // 24)
            self.world_state.time.hour = self.world_state.time.hour % 24
            
            logger.info(f"New day: Day {self.world_state.time.day}")
    
    def update_weather(self):
        """Update weather dynamically - 更真实的天气系统"""
        if not self.world_state:
            return
        
        old_weather = self.world_state.weather
        
        # 🌦️ 更真实的天气转换系统：使用渐进式变化
        # clear → cloudy → rain → storm
        # storm → rain → cloudy → clear
        weather_transitions = {
            "clear": {"clear": 0.60, "cloudy": 0.35, "rain": 0.05, "storm": 0.0},  # 晴天很少直接变暴风雨
            "cloudy": {"clear": 0.30, "cloudy": 0.40, "rain": 0.25, "storm": 0.05},  # 阴天是过渡状态
            "rain": {"clear": 0.10, "cloudy": 0.25, "rain": 0.50, "storm": 0.15},  # 雨天可能加强
            "storm": {"clear": 0.0, "cloudy": 0.10, "rain": 0.60, "storm": 0.30},  # 暴风雨不会突然转晴
        }
        
        # Get transitions for current weather
        transitions = weather_transitions.get(old_weather, {"clear": 1.0})
        
        # Randomly choose new weather based on probabilities
        rand_val = random.random()
        cumulative = 0
        new_weather = old_weather
        
        for weather, prob in transitions.items():
            cumulative += prob
            if rand_val <= cumulative:
                new_weather = weather
                break
        
        self.world_state.weather = new_weather
        
        if new_weather != old_weather:
            # Weather changed, log and create event
            weather_descriptions = {
                "clear": "☀️ 天气转晴了",
                "cloudy": "☁️ 天空变阴了",
                "rain": "🌧️ 开始下雨了",
                "storm": "⛈️ 暴风雨来临！"
            }
            
            description = weather_descriptions.get(new_weather, f"天气变成{new_weather}")
            logger.info(f"🌦️ 天气变化: {old_weather} → {new_weather}")
            
            # 🌦️ Add weather event (这是公共事件，所有NPC通过world_state可见)
            self.world_state.add_event(GameEvent(
                id=f"weather_{uuid.uuid4().hex[:8]}",
                type="weather_change",
                description=description,
                importance="medium" if new_weather == "storm" else "low"
            ))
            
            # ❌ 不再给每个NPC添加天气记忆！
            # 天气是世界状态的一部分，所有NPC可以通过world_state.weather直接访问
            # AI在做决策时会自动看到当前天气
    
    async def process_npcs(self):
        """Process all NPCs"""
        if not self.world_state:
            return
        
        current_time = self.world_state.time.get_current_time()
        delta_time = 1.0  # 1 second per tick
        
        for npc in self.world_state.npcs:
            # 🔥 跳过已死亡的NPC
            if not npc.is_alive:
                continue
            # Update NPC state
            await self.update_npc_attributes(npc, current_time)
            
            # 🔥 处理移动状态
            if npc.is_moving and npc.move_target:
                speed = self.movement_system.get_npc_speed(npc)
                arrived, new_pos = self.movement_system.move_towards_target(
                    npc.position,
                    npc.move_target,
                    speed,
                    delta_time
                )
                
                npc.position.x = new_pos.x
                npc.position.y = new_pos.y
                
                if arrived:
                    # 到达目标
                    npc.is_moving = False
                    npc.move_target = None
                    logger.info(f"✅ {npc.name} 到达目标位置")
                    
                    # 如果有待执行的行动，现在可以执行
                    if npc.action_state == "executing":
                        pass  # 继续等待行动时间结束
            
            # Check if needs new decision
            elif self.should_make_decision(npc, current_time):
                await self.process_npc_decision(npc, current_time)
            
            # Update ongoing action
            if npc.action_state == "executing" and npc.action_end_time:
                if current_time >= npc.action_end_time:
                    await self.complete_npc_action(npc)
            
            # 冷却结束，回到idle
            elif npc.action_state == "cooling" and npc.action_end_time:
                if current_time >= npc.action_end_time:
                    self.release_resource_occupation(npc)  # 🎯 释放资源
                    npc.action_state = "idle"
                    npc.current_action = None
                    npc.action_target = None
                    npc.action_end_time = None
                    logger.info(f"{npc.name} 冷却完成，进入idle")
            
            # 🧹 检查是否需要清理记忆
            if await self.memory_service.should_cleanup(npc.id, current_time):
                await self.cleanup_npc_memories(npc)
        
        # Process social interactions (every few seconds)
        if random.random() < 0.1:  # 10% chance per update
            await self.process_social_interactions(current_time)
    
    def release_resource_occupation(self, npc: NPC2D):
        """释放NPC占用的资源点"""
        if npc.current_action == "gather" and npc.action_target:
            for resource in self.world_state.resources:
                if resource.id == npc.action_target and resource.occupied_by == npc.id:
                    resource.occupied_by = None
                    logger.info(f"🔓 {npc.name} 释放资源点 {resource.type}[{resource.id[:8]}]")
                    break
    
    async def update_npc_attributes(self, npc: NPC2D, current_time: float):
        """Update NPC attributes over time"""
        # Increase hunger slowly (减慢饥饿速度)
        npc.attributes.hunger = min(100, npc.attributes.hunger + 0.05)  # 从0.1降到0.05
        
        # 🔥 饥饿造成伤害
        if npc.attributes.hunger > 90:
            npc.attributes.health = max(0, npc.attributes.health - 0.05)  # 非常饿时掉血
        
        # 🌦️ 天气影响
        weather_effects = {
            "clear": {"stamina_mult": 1.0, "health_mult": 1.0},
            "rain": {"stamina_mult": 0.7, "health_mult": 0.9},  # 雨天恢复慢
            "storm": {"stamina_mult": 0.5, "health_mult": 0.8},  # 暴风雨恢复更慢
        }
        weather_effect = weather_effects.get(self.world_state.weather, {"stamina_mult": 1.0, "health_mult": 1.0})
        
        # Decrease stamina when working, regenerate when resting
        if npc.current_action == "rest":
            # 基础恢复
            stamina_regen = 1.5
            health_regen = 0.8
            
            # 🏠 检查附近是否有庇护所，提供额外恢复
            in_shelter = False
            for building in self.world_state.buildings:
                if building.is_complete and building.provides_shelter:
                    distance = self.physics_engine.calculate_distance(
                        npc.position, building.position
                    )
                    if distance < 10:  # 10单位内受益
                        health_regen += building.health_regen_bonus
                        stamina_regen += building.stamina_regen_bonus
                        in_shelter = True
                        # 只从最近的一个庇护所获得加成
                        break
            
            # 🌦️ 应用天气影响（在庇护所内不受天气影响）
            if not in_shelter:
                stamina_regen *= weather_effect["stamina_mult"]
                health_regen *= weather_effect["health_mult"]
            
            npc.attributes.stamina = min(100, npc.attributes.stamina + stamina_regen)
            npc.attributes.health = min(100, npc.attributes.health + health_regen)
        elif npc.current_action and npc.current_action != "idle":
            npc.attributes.stamina = max(0, npc.attributes.stamina - 0.15)  # 从0.2降到0.15
        else:
            # idle时也缓慢恢复体力
            npc.attributes.stamina = min(100, npc.attributes.stamina + 0.2)
        
        # 🔥 体力耗尽造成伤害
        if npc.attributes.stamina < 10:
            npc.attributes.health = max(0, npc.attributes.health - 0.02)
        
        # 🔥 检查死亡
        if npc.attributes.health <= 0:
            await self._handle_npc_death(npc)
            return  # 死亡后不再更新
        
        # 🔥 添加持续的微小移动（让NPC看起来有生命力）
        # 这样即使不做特殊行动，NPC也会略微移动
        if random.random() < 0.15:  # 15%概率每次更新
            old_x, old_y = npc.position.x, npc.position.y
            npc.position.x += random.uniform(-0.3, 0.3)
            npc.position.y += random.uniform(-0.3, 0.3)
            # 边界检查
            npc.position.x = max(5, min(95, npc.position.x))
            npc.position.y = max(5, min(95, npc.position.y))
            # 记录移动（仅用于调试）
            if abs(npc.position.x - old_x) > 0.01 or abs(npc.position.y - old_y) > 0.01:
                logger.debug(f"🚶 {npc.name} 微移动: ({old_x:.1f},{old_y:.1f}) -> ({npc.position.x:.1f},{npc.position.y:.1f})")
    
    async def _handle_npc_death(self, npc: NPC2D):
        """处理NPC死亡"""
        if npc.is_alive:  # 只在第一次死亡时处理
            npc.is_alive = False
            npc.action_state = "dead"
            npc.current_action = None
            npc.is_moving = False
            npc.move_target = None
            
            # 记录死亡事件
            self.world_state.add_event(GameEvent(
                id=f"death_{uuid.uuid4().hex[:8]}",
                type="npc_death",
                description=f"💀 {npc.name} 死亡了！",
                related_npcs=[npc.id],
                importance="critical"
            ))
            
            logger.error(f"💀 {npc.name} 死亡了！位置: ({npc.position.x:.1f}, {npc.position.y:.1f})")
            
            # 通知其他NPC
            for other_npc in self.world_state.npcs:
                if other_npc.id != npc.id and other_npc.is_alive:
                    distance = self.physics_engine.calculate_distance(
                        npc.position, other_npc.position
                    )
                    if distance < 20:  # 20单位内的NPC会知道
                        memory = f"目睹了{npc.name}的死亡，感到悲伤和恐惧"
                        other_npc.memories.append(memory)
                        await self.memory_service.record_event(other_npc.id, "witness_death", memory)
                        if len(other_npc.memories) > 30:
                            other_npc.memories = other_npc.memories[-20:]
    
    def should_make_decision(self, npc: NPC2D, current_time: float) -> bool:
        """Check if NPC should make a new decision"""
        # 💬 对话中的NPC不能做新决策
        if npc.in_conversation:
            return False
        
        # 只有在idle状态才能开始新决策
        if npc.action_state != "idle":
            return False
        
        # Urgent situation
        if npc.needs_urgent_action():
            return True
        
        # Enough time has passed since last decision
        last_decision_time = self.npc_last_decision.get(npc.id, 0)
        if current_time - last_decision_time >= self.npc_decision_interval:
            return True
        
        return False
    
    async def process_npc_decision(self, npc: NPC2D, current_time: float):
        """Generate and execute NPC decision"""
        try:
            # Get memories from memory service
            memories = await self.memory_service.retrieve_relevant_memories(
                npc.id,
                f"current action: {npc.current_action}"
            )
            
            # 🔥 合并NPC模型中的记忆（包括上帝指令添加的记忆）
            # 将 npc.memories（字符串列表）转换为字典格式，并添加到memories中
            for memory_text in npc.memories[-10:]:  # 最近10条
                memories.append({
                    "type": "user_memory",
                    "description": memory_text,
                    "importance": 9  # 上帝指令的记忆重要性高
                })
            
            # Generate decision
            action = await self.ai_service.generate_npc_decision(
                npc,
                self.world_state,
                memories
            )
            
            # Execute action
            await self.execute_action(npc, action, current_time)
            
            # Record decision
            await self.memory_service.record_decision(npc.id, action.dict())
            
            # Update last decision time
            self.npc_last_decision[npc.id] = current_time
            
        except Exception as e:
            logger.error(f"Failed to process decision for {npc.name}: {e}")
            npc.current_action = "idle"
    
    def calculate_action_duration(self, npc: NPC2D, action) -> float:
        """计算行动真实持续时间"""
        # 基础时间（秒）
        base_times = {
            "gather": 12.0,   # 采集
            "flee": 3.0,      # 🏃 快速逃跑
            "share": 5.0,     # 🎁 分享物品
            "rest": 25.0,     # 休息
            "eat": 6.0,       # 进食
            "explore": 18.0,  # 探索
            "build": 999999.0,  # 🔧 建造：设置为极大值，由process_buildings控制完成时间
            "hunt": 30.0,     # 狩猎
        }
        
        duration = base_times.get(action.action, 10.0)
        
        # 根据资源类型调整（采集行动）
        if action.action == "gather" and action.target:
            resource = None
            for r in self.world_state.resources:
                if r.id == action.target:
                    resource = r
                    break
            
            if resource:
                # 根据资源类型调整时间
                type_multipliers = {
                    "wood": 1.2,    # 树木需要砍伐，稍慢
                    "stone": 1.5,   # 石头更难采集
                    "berry": 0.5,   # 浆果容易采集
                    "water": 0.6,   # 取水较快
                }
                duration *= type_multipliers.get(resource.type, 1.0)
                
                # 根据资源剩余量调整（资源少了更快采完）
                resource_factor = resource.quantity / resource.max_quantity
                duration *= (0.5 + 0.5 * resource_factor)  # 50%-100%
        
        # 根据NPC技能减少时间
        relevant_skills = {
            "gather": "gathering",
            "build": "construction",
            "hunt": "combat",
        }
        skill_name = relevant_skills.get(action.action)
        if skill_name:
            skill_level = npc.skills.get(skill_name, 0)
            # 每点技能减少0.5%时间，最多减少50%
            skill_reduction = min(0.5, skill_level * 0.005)
            duration *= (1.0 - skill_reduction)
        
        # 健康和体力影响
        if npc.attributes.stamina < 30:
            duration *= 1.3  # 体力低时变慢
        if npc.attributes.health < 50:
            duration *= 1.2  # 健康低时变慢
        
        # 最少5秒，最多120秒
        return max(5.0, min(120.0, duration))
    
    async def execute_action(self, npc: NPC2D, action, current_time: float):
        """Execute an NPC action"""
        npc.current_action = action.action
        npc.action_target = action.target
        npc.reasoning = action.reasoning
        
        # 计算真实的行动持续时间
        duration = self.calculate_action_duration(npc, action)
        npc.action_duration = duration
        npc.action_start_time = current_time
        npc.action_end_time = current_time + duration
        
        # 设置状态为executing
        npc.action_state = "executing"
        
        # 🔥 创建待办事项
        if action.action == "gather":
            npc.current_todo = f"采集{action.target}"
            npc.todo_steps = [
                "1. 寻找资源点",
                "2. 移动到资源点",
                "3. 采集资源",
                "4. 存入库存"
            ]
        elif action.action == "flee":
            npc.current_todo = "🏃 快速逃离危险"
            npc.todo_steps = ["1. 快速逃跑", "2. 到达安全距离"]
        elif action.action == "craft":
            # 🔧 制造工具
            item_name = action.target
            npc.current_todo = f"制造{item_name}"
            npc.todo_steps = ["1. 检查材料", "2. 开始制造", "3. 完成制造"]
            
            # 验证是否可以制造
            recipe = get_recipe(item_name)
            if recipe:
                can_craft_result, reason = can_craft(
                    item_name,
                    npc.inventory,
                    npc.skills.get("crafting", 0)
                )
                if not can_craft_result:
                    logger.warning(f"❌ {npc.name} 无法制造{item_name}: {reason}")
                    # 🔥 完整清理状态，避免卡住
                    npc.action_state = "idle"
                    npc.current_action = None
                    npc.action_target = None
                    npc.current_todo = None
                    npc.todo_steps = []
                    npc.reasoning = None
                    # 🎯 记录详细的失败结果反馈给AI
                    npc.last_action_result = f"❌ 制造{item_name}失败！原因: {reason}\n当前库存: {npc.inventory}\n需要材料: {recipe.required_materials}"
                    # 添加失败记忆
                    memory = f"想制造{item_name}但材料不足: {reason}"
                    npc.memories.append(memory)
                    await self.memory_service.record_event(npc.id, "craft_attempt_failed", memory)
                    if len(npc.memories) > 30:
                        npc.memories = npc.memories[-20:]
                    return
                else:
                    logger.info(f"🔧 {npc.name} 开始制造{item_name} (材料充足)")
            else:
                logger.warning(f"❌ {npc.name} 尝试制造未知物品: {item_name}")
                # 🔥 完整清理状态
                npc.action_state = "idle"
                npc.current_action = None
                npc.action_target = None
                npc.current_todo = None
                npc.todo_steps = []
                return
        elif action.action == "talk":
            # 💬 创建真正的对话会话（限制时间，避免一直聊天）
            npc.current_todo = "与附近的伙伴交流"
            npc.todo_steps = ["1. 发起对话", "2. 交流想法", "3. 结束对话回去干活"]
            
            # 对话持续30-45秒游戏时间（不要太长）
            conversation_duration = random.uniform(30, 45)
            
            # 找到附近的NPC创建对话
            await self.initiate_conversation(npc, current_time)
            
            # 设置对话结束时间
            npc.action_duration = conversation_duration
            npc.action_end_time = current_time + conversation_duration
            logger.info(f"💬 {npc.name} 开始对话，预计持续 {conversation_duration:.0f}秒")
            
        elif action.action == "share":
            # 🎁 分享物品给其他NPC
            target_npc_id = action.target
            npc.current_todo = f"分享物品给{target_npc_id}"
            npc.todo_steps = ["1. 找到目标NPC", "2. 递送物品"]
            logger.info(f"🎁 {npc.name} 准备分享物品给 {target_npc_id}")
        
        elif action.action == "cook":
            # 🍖 烹饪食物（需要篝火）
            npc.current_todo = "烹饪食物"
            npc.todo_steps = ["1. 找到篝火", "2. 烹饪生肉"]
            
            # 检查是否有生肉
            if npc.inventory.get("raw_meat", 0) <= 0:
                logger.warning(f"❌ {npc.name} 没有生肉可以烹饪")
                npc.action_state = "idle"
                npc.current_action = None
                npc.current_todo = None
                npc.todo_steps = []
                npc.last_action_result = "❌ 烹饪失败！没有生肉"
                return
            
            # 检查附近是否有完成的篝火
            nearest_campfire = None
            min_distance = float('inf')
            
            for building in self.world_state.buildings:
                if building.type == "campfire" and building.is_complete:
                    distance = self.physics_engine.calculate_distance(
                        npc.position, building.position
                    )
                    if distance < min_distance:
                        min_distance = distance
                        nearest_campfire = building
            
            if not nearest_campfire:
                logger.warning(f"❌ {npc.name} 附近没有篝火，无法烹饪")
                npc.action_state = "idle"
                npc.current_action = None
                npc.current_todo = None
                npc.todo_steps = []
                npc.last_action_result = "❌ 烹饪失败！附近没有篝火（需要先建造篝火）"
                return
            
            if min_distance > 10:
                # 篝火太远，移动过去
                npc.is_moving = True
                npc.move_target = Position2D(
                    x=nearest_campfire.position.x,
                    y=nearest_campfire.position.y
                )
                npc.action_target = nearest_campfire.id
                logger.info(f"🍖 {npc.name} 向篝火移动准备烹饪")
            else:
                # 在篝火附近，可以烹饪
                npc.action_target = nearest_campfire.id
                logger.info(f"🍖 {npc.name} 开始在篝火旁烹饪")
        
        elif action.action == "build":
            # 🏗️ 建造建筑
            building_type = action.target
            
            # 🔧 中文名称到英文type的映射
            building_name_map = {
                "篝火": "campfire",
                "简易棚屋": "lean_to",
                "庇护所": "lean_to",
                "棚屋": "lean_to",
                "木屋": "wooden_hut",
                "木质小屋": "wooden_hut",
                "储物棚": "storage_shed",
                "仓库": "storage_shed",
                "工作台": "workshop",
                "作坊": "workshop"
            }
            
            # 如果是中文名称，转换为英文type
            if building_type in building_name_map:
                building_type = building_name_map[building_type]
                logger.info(f"🔄 {npc.name} 建筑名称转换: {action.target} -> {building_type}")
            
            npc.current_todo = f"建造{building_type}"
            npc.todo_steps = ["1. 检查材料", "2. 选择位置", "3. 开始建造"]
            
            # 导入建筑模块
            from app.models.buildings import get_building_type, Building2D
            
            building_def = get_building_type(building_type)
            if not building_def:
                logger.warning(f"❌ {npc.name} 尝试建造未知建筑: {building_type}")
                npc.action_state = "idle"
                npc.current_action = None
                npc.current_todo = None
                npc.todo_steps = []
                npc.last_action_result = f"❌ 建造失败！未知建筑类型: {building_type}"
                return
            
            # 检查材料
            requirements = building_def.get("requirements", {})
            missing_materials = []
            for material, amount in requirements.items():
                if npc.inventory.get(material, 0) < amount:
                    missing_materials.append(f"{material}×{amount}(缺{amount - npc.inventory.get(material, 0)})")
            
            if missing_materials:
                logger.warning(f"❌ {npc.name} 材料不足，无法建造{building_type}: {', '.join(missing_materials)}")
                npc.action_state = "idle"
                npc.current_action = None
                npc.current_todo = None
                npc.todo_steps = []
                npc.last_action_result = f"❌ 建造{building_type}失败！材料不足: {', '.join(missing_materials)}\n当前库存: {npc.inventory}"
                memory = f"想建造{building_type}但材料不足: {', '.join(missing_materials)}"
                npc.memories.append(memory)
                await self.memory_service.record_event(npc.id, "build_attempt_failed", memory)
                if len(npc.memories) > 30:
                    npc.memories = npc.memories[-20:]
                return
            
            # 检查是否已有同类型建筑正在建造或已完成
            # 🔧 修复：对于基础建筑（campfire、lean_to、wooden_hut）进行全局唯一性检查
            # 对于可重复建筑（storage_shed、workshop）只检查附近
            unique_building_types = {"campfire", "lean_to", "wooden_hut"}  # 这些建筑全局唯一
            
            has_completed_building = False
            nearest_incomplete_building = None
            nearest_incomplete_distance = float('inf')
            
            for building in self.world_state.buildings:
                if building.type == building_type:
                    distance = self.physics_engine.calculate_distance(npc.position, building.position)
                    
                    if building.is_complete:
                        # 已有完成的同类型建筑
                        if building_type in unique_building_types:
                            # 🔧 基础建筑：全局唯一，无论距离
                            has_completed_building = True
                        elif distance < 20:
                            # 🔧 可重复建筑：只检查附近20单位内
                            has_completed_building = True
                    elif not building.is_complete and distance < 15:
                        # 附近有正在建造的建筑，记录最近的
                        if distance < nearest_incomplete_distance:
                            nearest_incomplete_distance = distance
                            nearest_incomplete_building = building
            
            # 🔧 如果已经有完成的同类型建筑，取消建造
            if has_completed_building:
                logger.warning(f"⚠️ {npc.name} 已有{building_type}，取消重复建造")
                npc.action_state = "idle"
                npc.current_action = None
                npc.current_todo = None
                npc.todo_steps = []
                npc.last_action_result = f"⚠️ 已有{building_type}，无需重复建造"
                return
            
            # 🔧 如果附近有正在建造的同类型建筑，加入帮忙
            if nearest_incomplete_building:
                logger.info(f"🏗️ {npc.name} 发现附近有{building_type}正在建造（进度{nearest_incomplete_building.construction_progress*100:.0f}%），决定加入帮忙")
                npc.action_target = nearest_incomplete_building.id
                npc.current_todo = f"帮助建造{building_type}"
                npc.todo_steps = [f"1. 前往建筑位置", f"2. 加入建造（当前{nearest_incomplete_building.construction_progress*100:.0f}%）", "3. 持续建造直到完成"]
                
                # 移动到建筑位置
                if nearest_incomplete_distance > 3:
                    npc.is_moving = True
                    npc.move_target = Position2D(
                        x=nearest_incomplete_building.position.x,
                        y=nearest_incomplete_building.position.y
                    )
                    logger.info(f"🚶 {npc.name} 正在前往建筑位置（距离{nearest_incomplete_distance:.1f}单位）")
                else:
                    # 已经在建筑附近，直接开始建造
                    logger.info(f"🏗️ {npc.name} 已在建筑附近，立即开始建造")
                
                # 🔧 关键：不要立即return，让后续逻辑继续执行
                # 建筑已经存在于world_state.buildings中，process_buildings会处理
                return
            
            # 创建新建筑
            building_id = f"building_{uuid.uuid4().hex[:8]}"
            # 在NPC附近选择建造位置
            build_pos = Position2D(
                x=npc.position.x + random.uniform(-2, 2),
                y=npc.position.y + random.uniform(-2, 2)
            )
            build_pos.x = max(5, min(95, build_pos.x))
            build_pos.y = max(5, min(95, build_pos.y))
            
            new_building = Building2D(
                id=building_id,
                type=building_type,
                name=building_def["name"],
                position=build_pos,
                size=Position2D(
                    x=building_def["size"]["x"],
                    y=building_def["size"]["y"]
                ),
                description=building_def["description"],
                sprite=building_def["sprite"],
                is_complete=False,
                construction_progress=0.0,
                build_time_total=building_def["build_time"],
                build_time_elapsed=0.0,
                builders=[npc.id],
                requires_cooperation=building_def.get("requires_cooperation", False),
                capacity=building_def.get("capacity", 0),
                storage_capacity=building_def.get("storage_capacity", 0),
                provides_shelter=building_def.get("provides_shelter", False),
                provides_warmth=building_def.get("provides_warmth", False),
                provides_cooking=building_def.get("provides_cooking", False),
                health_regen_bonus=building_def.get("health_regen_bonus", 0.0),
                stamina_regen_bonus=building_def.get("stamina_regen_bonus", 0.0),
                unlocks=building_def.get("unlocks", [])
            )
            
            # 消耗材料
            for material, amount in requirements.items():
                npc.inventory[material] = npc.inventory.get(material, 0) - amount
                if npc.inventory[material] <= 0:
                    del npc.inventory[material]
            
            self.world_state.buildings.append(new_building)
            npc.action_target = building_id
            
            logger.info(f"🏗️ {npc.name} 开始建造{building_type}在({build_pos.x:.1f}, {build_pos.y:.1f})，消耗材料: {requirements}")
            
            # 广播事件
            self.world_state.add_event(GameEvent(
                id=f"build_{uuid.uuid4().hex[:8]}",
                type="build_start",
                description=f"🏗️ {npc.name} 开始建造{building_def['name']}",
                related_npcs=[npc.id],
                importance="high"
            ))
            
        elif action.action == "rest":
            npc.current_todo = "休息恢复体力"
            npc.todo_steps = ["1. 找个安全地方", "2. 休息"]
        elif action.action == "explore":
            npc.current_todo = "探索周边环境"
            npc.todo_steps = ["1. 选择方向", "2. 移动探索", "3. 观察周围"]
        elif action.action in ["hunt", "defend"]:
            # 🎯 狩猎/战斗行动
            target_beast_id = action.target if action.target else None
            if target_beast_id:
                npc.current_todo = f"狩猎{target_beast_id}"
            else:
                npc.current_todo = "寻找猎物并攻击"
            npc.todo_steps = ["1. 寻找目标", "2. 接近目标", "3. 发起攻击"]
        else:
            npc.current_todo = action.action
            npc.todo_steps = ["1. 执行行动"]
        
        # 🔥 添加行动日志
        log_entry = f"[{self.world_state.time.format_time()}] 决策: {action.reasoning[:50]}..."
        npc.action_log.append(log_entry)
        if len(npc.action_log) > 20:  # 保持最近20条
            npc.action_log = npc.action_log[-20:]
        
        # 🔥 减少日志输出（前端已有显示）
        logger.debug(f"[行动] {npc.name}: {action.action} (持续{duration:.1f}秒) - {action.reasoning}")
        
        # Move NPC towards target if needed
        if action.action == "gather" and action.target:
            # 🔥 AI返回的是资源类型（如"wood"、"berry"），需要找到最近的该类型资源
            target_resource_type = action.target
            
            # 查找最近的该类型资源
            nearest_resource = None
            min_distance = float('inf')
            
            for resource in self.world_state.resources:
                # 匹配资源类型（不是ID）并且未被占用
                is_available = (
                    resource.type == target_resource_type and 
                    not resource.is_depleted and
                    (resource.occupied_by is None or resource.occupied_by == npc.id)  # 🎯 资源未被占用或被自己占用
                )
                
                if is_available:
                    dx = resource.position.x - npc.position.x
                    dy = resource.position.y - npc.position.y
                    distance = (dx**2 + dy**2)**0.5
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_resource = resource
            
            if nearest_resource:
                # 🎯 占用资源点
                nearest_resource.occupied_by = npc.id
                logger.info(f"🔒 {npc.name} 占用资源点 {nearest_resource.type}[{nearest_resource.id[:8]}]")
                
                # 更新action_target为实际的资源ID
                npc.action_target = nearest_resource.id
                
                # 计算距离
                distance = self.physics_engine.calculate_distance(npc.position, nearest_resource.position)
                logger.info(f"📍 {npc.name} 到资源点距离: {distance:.1f} 单位 (目标: {nearest_resource.type} ID:{nearest_resource.id[:8]})")
                
                # 🔥 设置移动目标（而不是瞬移）
                if distance > 2:  # 如果不在采集范围内
                    npc.is_moving = True
                    npc.move_target = Position2D(
                        x=nearest_resource.position.x,
                        y=nearest_resource.position.y
                    )
                    logger.info(f"🎯 {npc.name} 设置移动目标: ({npc.move_target.x:.1f}, {npc.move_target.y:.1f})")
                else:
                    logger.info(f"✅ {npc.name} 已在资源点附近，准备采集")
            else:
                # 找不到该类型的可用资源
                logger.warning(f"❌ {npc.name} 找不到可用的 {target_resource_type} 资源（可能全部被占用），取消行动")
                npc.action_state = "idle"
                npc.current_action = None
        
        elif action.action == "explore":
            # Random exploration movement
            old_x, old_y = npc.position.x, npc.position.y
            npc.position.x += random.uniform(-5, 5)  # 增加探索范围（从-3~3到-5~5）
            npc.position.y += random.uniform(-5, 5)
            # Keep within bounds
            npc.position.x = max(5, min(95, npc.position.x))
            npc.position.y = max(5, min(95, npc.position.y))
            logger.info(f"🚶 {npc.name} 探索: ({old_x:.1f},{old_y:.1f}) -> ({npc.position.x:.1f},{npc.position.y:.1f})")
        
        elif action.action in ["hunt", "defend"]:
            # 🎯 狩猎/战斗 - 找到目标野兽并移动到攻击范围
            target_beast = None
            
            # 如果有指定目标，尝试找到该野兽
            if action.target:
                for beast in self.world_state.beasts:
                    if beast.id == action.target or beast.type == action.target:
                        target_beast = beast
                        break
            
            # 如果没有找到指定目标，找最近的野兽
            if not target_beast:
                min_distance = float('inf')
                for beast in self.world_state.beasts:
                    distance = self.physics_engine.calculate_distance(npc.position, beast.position)
                    if distance < min_distance:
                        min_distance = distance
                        target_beast = beast
            
            if target_beast:
                # 更新action_target为实际的野兽ID
                npc.action_target = target_beast.id
                
                # 计算距离
                distance = self.physics_engine.calculate_distance(npc.position, target_beast.position)
                logger.info(f"🎯 {npc.name} 到猎物距离: {distance:.1f} 单位 (目标: {target_beast.type}[{target_beast.id[:8]}])")
                
                # 🔱 根据装备决定攻击距离
                attack_range = self.physics_engine.ATTACK_RANGE  # 基础2.5单位
                if "spear" in npc.equipment:
                    attack_range = 4.5  # 石矛攻击距离：4.5单位（比基础远80%）
                    logger.info(f"🔱 {npc.name} 装备石矛，攻击距离: {attack_range}单位")
                
                if distance > attack_range:
                    npc.is_moving = True
                    # 🔧 不要移动到野兽正中心，而是移动到攻击范围边缘，避免重叠
                    # 计算方向向量
                    dx = target_beast.position.x - npc.position.x
                    dy = target_beast.position.y - npc.position.y
                    # 归一化
                    if distance > 0:
                        dx /= distance
                        dy /= distance
                    # 目标位置：野兽位置 - (攻击范围 * 方向)
                    target_x = target_beast.position.x - dx * (attack_range * 0.8)  # 留出20%余量
                    target_y = target_beast.position.y - dy * (attack_range * 0.8)
                    npc.move_target = Position2D(x=target_x, y=target_y)
                    logger.info(f"🏹 {npc.name} 向猎物靠近（保持{attack_range:.1f}单位距离）: ({npc.move_target.x:.1f}, {npc.move_target.y:.1f})")
                else:
                    logger.info(f"✅ {npc.name} 已在攻击范围内，准备战斗")
            else:
                # 找不到可攻击的野兽
                logger.warning(f"❌ {npc.name} 找不到可攻击的目标，取消行动")
                npc.action_state = "idle"
                npc.current_action = None
        
        elif action.action == "flee":
            # 🏃 智能逃离危险 - 评估所有威胁，选择最安全的方向
            escape_result = self._calculate_smart_escape_direction(npc)
            
            old_x, old_y = npc.position.x, npc.position.y
            npc.position.x = escape_result['target_x']
            npc.position.y = escape_result['target_y']
            
            # Keep within bounds
            npc.position.x = max(5, min(95, npc.position.x))
            npc.position.y = max(5, min(95, npc.position.y))
            
            logger.info(f"🏃 {npc.name} {escape_result['description']}: ({old_x:.1f},{old_y:.1f}) -> ({npc.position.x:.1f},{npc.position.y:.1f})")
        
        # Add event with more details
        self.world_state.add_event(GameEvent(
            id=f"event_{uuid.uuid4().hex[:8]}",
            type="npc_action",
            description=f"💭 {npc.name}: {action.reasoning}",
            related_npcs=[npc.id],
            importance="low" if action.action == "rest" else "medium"
        ))
        
        # Broadcast NPC action with AI reasoning
        if self.broadcast_callback:
            await self.broadcast_callback('npc_action', {
                'npc_id': npc.id,
                'npc_name': npc.name,
                'action': action.action,
                'description': action.reasoning,
                'reasoning': action.reasoning,
                'position': {'x': npc.position.x, 'y': npc.position.y}
            })
    
    async def complete_npc_action(self, npc: NPC2D):
        """Complete an NPC action"""
        action_type = npc.current_action
        
        # 🔥 记录行动完成日志
        current_time = self.world_state.time.get_current_time()
        completion_log = f"[{self.world_state.time.format_time()}] 完成: {npc.current_todo or action_type}"
        npc.action_log.append(completion_log)
        if len(npc.action_log) > 20:
            npc.action_log = npc.action_log[-20:]
        
        # 🔥 改进记忆系统：记录多样化事件
        if action_type == "gather":
            result = await self.complete_gather_action(npc)
            if result:  # 采集成功
                # 不只记录库存，还记录位置和感受
                memory = f"在({npc.position.x:.0f},{npc.position.y:.0f})采集了{result['amount']}个{result['type']}"
                npc.memories.append(memory)
                await self.memory_service.record_event(npc.id, "gather", memory)
                # 🎯 记录采集成功结果
                npc.last_action_result = f"✅ 采集成功！获得{result['amount']}个{result['type']}\n当前库存: {npc.inventory}"
                # 记录观察
                await self._record_environmental_observation(npc)
            else:
                # 🎯 采集失败
                npc.last_action_result = f"❌ 采集失败！目标资源可能已枯竭或距离太远\n当前位置: ({npc.position.x:.0f},{npc.position.y:.0f})"
        elif action_type == "flee":
            # 🏃 记录逃跑事件
            memory = f"从危险中逃到了({npc.position.x:.0f},{npc.position.y:.0f})，暂时安全了"
            npc.memories.append(memory)
            await self.memory_service.record_event(npc.id, "flee", memory)
            # 🎯 记录逃跑结果
            npc.last_action_result = f"✅ 成功逃离危险！\n当前位置: ({npc.position.x:.0f},{npc.position.y:.0f})\n健康: {npc.attributes.health:.0f}/100"
            logger.info(f"✅ {npc.name} 成功逃离危险")
        elif action_type == "craft":
            # 🔧 完成制造工具
            result = self.complete_craft_action(npc)
            if result:
                memory = f"成功制造了{result['item_name']}！现在拥有这个工具了"
                npc.memories.append(memory)
                await self.memory_service.record_event(npc.id, "craft", memory)
                # 🎯 记录成功结果反馈
                npc.last_action_result = f"✅ 成功制造了{result['item_name']}！\n消耗材料: {result.get('materials_used', '未知')}\n当前装备: {list(npc.equipment.keys())}\n剩余库存: {npc.inventory}"
                logger.info(f"🔧 {npc.name} 成功制造了 {result['item_name']}")
            else:
                memory = f"尝试制造工具但失败了"
                npc.memories.append(memory)
                await self.memory_service.record_event(npc.id, "craft_failed", memory)
                # 🎯 记录失败结果反馈
                npc.last_action_result = f"❌ 制造{npc.action_target}失败！可能是材料在执行中被消耗或其他原因\n当前库存: {npc.inventory}"
        elif action_type == "talk":
            # 💬 完成对话 - 所有参与者共享记忆
            await self.complete_conversation(npc, current_time)
        elif action_type == "share":
            # 🎁 完成物品分享
            result = self.complete_share_action(npc)
            if result:
                memory = f"分享了{result['item_name']}给{result['target_name']}"
                npc.memories.append(memory)
                await self.memory_service.record_event(npc.id, "share", memory)
                logger.info(f"🎁 {npc.name} 成功分享物品")
        elif action_type == "build":
            # 🏗️ 完成建造（或建造进度推进）
            # 注意：build行动不是一次完成，而是持续推进建造进度
            # 这里的"完成"是指一个建造工作时段结束，建筑可能还未完工
            pass  # 建造逻辑在process_buildings中持续处理
        elif action_type == "cook":
            # 🍖 完成烹饪
            result = self.complete_cook_action(npc)
            if result:
                memory = f"烹饪了{result['amount']}份肉，香喷喷的"
                npc.memories.append(memory)
                await self.memory_service.record_event(npc.id, "cook", memory)
                npc.last_action_result = f"✅ 烹饪成功！制作了{result['amount']}份熟肉\n当前库存: {npc.inventory}"
                logger.info(f"🍖 {npc.name} 成功烹饪")
            else:
                npc.last_action_result = "❌ 烹饪失败！可能是距离篝火太远或没有生肉"
        elif action_type == "eat":
            self.complete_eat_action(npc)
            memory = f"吃掉了{npc.action_target or 'food'}，感觉饱多了"
            npc.memories.append(memory)
            await self.memory_service.record_event(npc.id, "eat", memory)
            # 🎯 记录进食结果
            satiety = 100 - npc.attributes.hunger
            npc.last_action_result = f"✅ 进食完成！\n饱食度: {satiety:.0f}/100\n剩余食物: {npc.inventory.get('berry', 0)}浆果, {npc.inventory.get('meat', 0)}肉"
        elif action_type == "rest":
            # Already handled in update_npc_attributes
            memory = f"休息了一会儿，感觉体力恢复了"
            npc.memories.append(memory)
            await self.memory_service.record_event(npc.id, "rest", memory)
            # 🎯 记录休息结果
            npc.last_action_result = f"✅ 休息完成！\n健康: {npc.attributes.health:.0f}/100\n体力: {npc.attributes.stamina:.0f}/100"
        elif action_type in ["hunt", "defend"]:
            # 🔥 处理狩猎/战斗行动
            result = self.complete_combat_action(npc)
            if result:
                memory = f"攻击了{result['beast_type']}，造成{result['damage']}伤害"
                if result.get('killed'):
                    memory += f"，成功击杀！"
                npc.memories.append(memory)
                await self.memory_service.record_event(npc.id, action_type, memory)
                # 🎯 记录战斗结果
                if result.get('killed'):
                    npc.last_action_result = f"✅ 成功击杀{result['beast_type']}！\n获得: {result.get('loot', '无战利品')}\n健康: {npc.attributes.health:.0f}/100"
                else:
                    npc.last_action_result = f"⚔️ 攻击{result['beast_type']}造成{result['damage']}伤害\n健康: {npc.attributes.health:.0f}/100"
            else:
                # 🎯 战斗失败或目标消失
                npc.last_action_result = f"❌ 战斗失败！目标野兽已消失或距离太远\n健康: {npc.attributes.health:.0f}/100"
        
        # 限制记忆数量
        if len(npc.memories) > 30:
            npc.memories = npc.memories[-20:]
        
        # 🔥 清除待办事项
        npc.current_todo = None
        npc.todo_steps = []
        
        # 进入冷却状态，2-5秒后才能开始新决策
        cooling_time = random.uniform(2.0, 5.0)
        npc.action_state = "cooling"
        npc.action_end_time = current_time + cooling_time
        npc.action_duration = cooling_time
        # 🔥 减少日志输出
        logger.debug(f"{npc.name} 行动完成，冷却 {cooling_time:.1f}秒")
    
    async def complete_gather_action(self, npc: NPC2D):
        """Complete a gather action"""
        if not npc.action_target:
            return None
        
        # Find resource
        resource = None
        for r in self.world_state.resources:
            if r.id == npc.action_target:
                resource = r
                break
        
        if not resource:
            logger.warning(f"{npc.name} 无法找到资源目标")
            return None
        
        # 🔥 距离检查：必须在采集范围内
        if not self.physics_engine.can_gather(npc.position, resource.position):
            distance = self.physics_engine.calculate_distance(npc.position, resource.position)
            logger.warning(f"❌ {npc.name} 距离资源点太远 ({distance:.1f} 单位)，无法采集")
            return
        
        # 检查资源是否枯竭
        if resource.is_depleted:
            logger.info(f"⚠️ {npc.name} 发现资源点已枯竭")
            return
        
        # 🔥 根据资源类型决定采集量
        gather_amounts = {
            "wood": 5,
            "stone": 3,
            "berry": 10,
            "water": 15,
        }
        gather_amount = gather_amounts.get(resource.type, 5)
        
        # 🔧 工具加成
        if resource.type == "wood" and "stone_axe" in npc.equipment:
            gather_amount = int(gather_amount * 1.5)  # 石斧提升50%效率
            logger.info(f"🔧 {npc.name} 使用石斧，采集效率+50%")
        elif resource.type == "stone" and "stone_pickaxe" in npc.equipment:
            gather_amount = int(gather_amount * 1.5)  # 石镐提升50%效率
            logger.info(f"🔧 {npc.name} 使用石镐，采集效率+50%")
        elif resource.type == "berry" and "basket" in npc.equipment:
            gather_amount = int(gather_amount * 1.3)  # 篮子提升30%效率
            logger.info(f"🔧 {npc.name} 使用篮子，采集效率+30%")
        elif resource.type == "water" and "water_container" in npc.equipment:
            gather_amount = int(gather_amount * 1.2)  # 水容器提升20%效率
            logger.info(f"🔧 {npc.name} 使用水容器，采集效率+20%")
        
        # 🔥 真实消耗资源
        actual_amount = resource.gather(gather_amount)
        
        # 检查资源是否枯竭
        if resource.is_depleted:
            current_time = self.world_state.time.get_current_time()
            resource.depleted_time = current_time
            logger.info(f"❌ 资源枯竭: {resource.type} at ({resource.position.x:.1f}, {resource.position.y:.1f})")
            
            # 添加事件
            self.world_state.add_event(GameEvent(
                id=f"event_{uuid.uuid4().hex[:8]}",
                type="resource_depleted",
                description=f"一处{resource.type}资源被采集完了",
                importance="medium"
            ))
        
        # 添加到NPC库存
        npc.inventory[resource.type] = npc.inventory.get(resource.type, 0) + actual_amount
        
        # 增加技能
        skill_map = {"wood": "woodcutting", "stone": "mining", "berry": "foraging"}
        if resource.type in skill_map:
            skill_name = skill_map[resource.type]
            npc.skills[skill_name] = min(100, npc.skills.get(skill_name, 0) + 1)
        
        logger.info(f"✅ {npc.name} 采集了 {actual_amount} {resource.type} (剩余: {resource.quantity}/{resource.max_quantity})")
        
        # 🎯 释放资源占用
        if resource.occupied_by == npc.id:
            resource.occupied_by = None
            logger.info(f"🔓 {npc.name} 释放资源点 {resource.type}[{resource.id[:8]}]")
        
        # 添加到全局资源
        self.world_state.global_resources[resource.type] = \
            self.world_state.global_resources.get(resource.type, 0) + actual_amount
        
        # 🔥 返回采集结果
        return {
            'amount': actual_amount,
            'type': resource.type
        }
    
    def complete_eat_action(self, npc: NPC2D):
        """Complete an eat action"""
        food_item = npc.action_target or "berry"
        
        if npc.inventory.get(food_item, 0) > 0:
            npc.inventory[food_item] -= 1
            
            # 🔥 不同食物提供不同的恢复效果
            food_effects = {
                "berry": {"hunger": -30, "health": 5, "stamina": 5},           # 浆果：减饥饿，少量恢复
                "water": {"hunger": -10, "health": 2, "stamina": 10},          # 水：恢复体力
                "raw_meat": {"hunger": -40, "health": 3, "stamina": 5},        # 生肉：减更多饥饿但不如熟肉
                "cooked_meat": {"hunger": -60, "health": 15, "stamina": 10},   # 熟肉：大幅恢复！
                "wood": {"hunger": 0, "health": 0, "stamina": 0},              # 木头不能吃
                "stone": {"hunger": 0, "health": 0, "stamina": 0},             # 石头不能吃
            }
            
            effects = food_effects.get(food_item, {"hunger": -20, "health": 3, "stamina": 3})
            
            # 应用效果
            npc.attributes.hunger = max(0, npc.attributes.hunger + effects["hunger"])
            npc.attributes.health = min(100, npc.attributes.health + effects["health"])
            npc.attributes.stamina = min(100, npc.attributes.stamina + effects["stamina"])
            
            logger.info(f"🍽️ {npc.name} 吃了 {food_item}: 饥饿{npc.attributes.hunger:.0f}, 生命{npc.attributes.health:.0f}, 体力{npc.attributes.stamina:.0f}")
        else:
            logger.warning(f"⚠️ {npc.name} 没有 {food_item} 可以吃")
    
    def complete_cook_action(self, npc: NPC2D):
        """Complete a cook action - cook raw meat to cooked meat"""
        if not npc.action_target:
            logger.warning(f"❌ {npc.name} cook行动没有目标")
            return None
        
        # 找到篝火
        campfire = None
        for building in self.world_state.buildings:
            if building.id == npc.action_target:
                campfire = building
                break
        
        if not campfire or not campfire.is_complete or campfire.type != "campfire":
            logger.warning(f"❌ {npc.name} 找不到可用的篝火")
            return None
        
        # 检查距离（必须在篝火附近）
        distance = self.physics_engine.calculate_distance(npc.position, campfire.position)
        if distance > 10:
            logger.warning(f"❌ {npc.name} 距离篝火太远 ({distance:.1f} 单位)，无法烹饪")
            return None
        
        # 检查是否有生肉
        raw_meat_count = npc.inventory.get("raw_meat", 0)
        if raw_meat_count <= 0:
            logger.warning(f"❌ {npc.name} 没有生肉可以烹饪")
            return None
        
        # 烹饪所有生肉
        cooked_amount = raw_meat_count
        npc.inventory["raw_meat"] = 0
        npc.inventory["cooked_meat"] = npc.inventory.get("cooked_meat", 0) + cooked_amount
        
        logger.info(f"🍖 {npc.name} 烹饪了{cooked_amount}份生肉 -> {cooked_amount}份熟肉")
        
        # 提升技能
        npc.skills["survival"] = min(100, npc.skills.get("survival", 0) + 1)
        
        # 添加事件
        self.world_state.add_event(GameEvent(
            id=f"cook_{uuid.uuid4().hex[:8]}",
            type="cook",
            description=f"🍖 {npc.name}烹饪了{cooked_amount}份肉",
            related_npcs=[npc.id],
            importance="low"
        ))
        
        return {
            "amount": cooked_amount
        }
    
    def complete_combat_action(self, npc: NPC2D):
        """Complete a combat/hunt action"""
        # 寻找最近的野兽
        nearest_beast = None
        min_distance = float('inf')
        
        for beast in self.world_state.beasts:
            distance = self.physics_engine.calculate_distance(
                npc.position, beast.position
            )
            if distance < min_distance:
                min_distance = distance
                nearest_beast = beast
        
        if not nearest_beast:
            logger.warning(f"⚠️ {npc.name} 找不到可攻击的野兽")
            return None
        
        # 🔱 根据装备决定攻击距离
        attack_range = self.physics_engine.ATTACK_RANGE  # 基础2.5单位
        if "spear" in npc.equipment:
            attack_range = 4.5  # 石矛攻击距离：4.5单位
        
        # 检查距离（必须在攻击范围内）
        if min_distance > attack_range + 1:  # 稍微宽松一点
            logger.warning(f"⚠️ {npc.name} 距离野兽太远 ({min_distance:.1f} 单位 > {attack_range + 1:.1f})，无法攻击")
            return None
        
        # 计算伤害
        base_damage = 15  # 从10提升到15，让NPC更有战斗力
        combat_skill = npc.skills.get("combat", 0)
        skill_bonus = combat_skill * 0.8  # 从0.5提升到0.8，每点技能+0.8伤害
        
        # 体力影响
        stamina_factor = max(0.7, npc.attributes.stamina / 100)  # 最低70%效率
        
        # 健康影响
        health_factor = max(0.6, npc.attributes.health / 100)  # 最低60%效率
        
        # 🔧 武器/工具加成
        weapon_bonus = 0
        if "spear" in npc.equipment:
            weapon_bonus = 40  # 长矛增加40点伤害（从30提升）
        elif npc.inventory.get("stone", 0) > 0:
            weapon_bonus = 8  # 石头可以作为武器（从5提升到8）
        
        total_damage = (base_damage + skill_bonus + weapon_bonus) * stamina_factor * health_factor
        
        # 造成伤害
        beast_killed = nearest_beast.take_damage(total_damage)
        
        # 消耗体力
        npc.attributes.stamina = max(0, npc.attributes.stamina - 10)
        
        # 增加战斗技能
        npc.skills["combat"] = min(100, npc.skills.get("combat", 0) + 2)
        
        logger.info(f"⚔️ {npc.name} 攻击 {nearest_beast.type}，造成{total_damage:.1f}伤害")
        
        result = {
            'beast_type': nearest_beast.type,
            'damage': int(total_damage),
            'killed': beast_killed
        }
        
        if beast_killed:
            # 野兽被击杀
            self.world_state.beasts.remove(nearest_beast)
            logger.info(f"🎉 {npc.name} 击杀了 {nearest_beast.type}！")
            
            # 🍖 掉落生肉
            meat_amounts = {
                "rabbit": 2,  # 兔子掉落2肉
                "wolf": 3,    # 狼掉落3肉
                "bear": 5,    # 熊掉落5肉
                "deer": 4,    # 鹿掉落4肉
            }
            meat_amount = meat_amounts.get(nearest_beast.type, 2)
            npc.inventory["raw_meat"] = npc.inventory.get("raw_meat", 0) + meat_amount
            result['loot'] = f"{meat_amount}生肉"
            logger.info(f"🍖 {npc.name} 获得{meat_amount}生肉")
            
            # 添加事件
            self.world_state.add_event(GameEvent(
                id=f"hunt_{uuid.uuid4().hex[:8]}",
                type="beast_killed",
                description=f"⚔️ {npc.name}击杀了{nearest_beast.type}，获得{meat_amount}生肉！",
                related_npcs=[npc.id],
                importance="high"
            ))
        else:
            # 野兽反击
            if nearest_beast.is_aggressive():
                counter_damage = nearest_beast.damage * 0.5  # 反击伤害减半
                npc.attributes.health = max(0, npc.attributes.health - counter_damage)
                logger.warning(f"💢 {nearest_beast.type} 反击了 {npc.name}，造成{counter_damage:.1f}伤害")
        
        return result
    
    def complete_craft_action(self, npc: NPC2D):
        """Complete a craft action - create tool/item"""
        if not npc.action_target:
            logger.warning(f"❌ {npc.name} craft行动没有目标")
            return None
        
        item_name = npc.action_target
        recipe = get_recipe(item_name)
        
        if not recipe:
            logger.warning(f"❌ {npc.name} 尝试制造未知物品: {item_name}")
            return None
        
        # 再次检查材料（防止中途被消耗）
        can_craft_result, reason = can_craft(
            item_name,
            npc.inventory,
            npc.skills.get("crafting", 0)
        )
        
        if not can_craft_result:
            logger.warning(f"❌ {npc.name} 无法完成制造{item_name}: {reason}")
            return None
        
        # 消耗材料
        npc.inventory = consume_materials(npc.inventory, recipe)
        
        # 创建工具/装备
        current_time = self.world_state.time.get_current_time()
        npc.equipment[item_name] = {
            "durability": recipe.durability,
            "quality": 100,  # 初始质量100%
            "crafted_at": current_time,
            "type": recipe.tool_type,
            "description": recipe.description
        }
        
        # 提升制造技能
        npc.skills["crafting"] = min(100, npc.skills.get("crafting", 0) + 2)
        
        logger.info(f"🔧 {npc.name} 成功制造了 {item_name}！材料消耗: {recipe.required_materials}")
        
        # 广播事件
        self.world_state.add_event(GameEvent(
            id=f"event_{uuid.uuid4().hex[:8]}",
            type="craft",
            description=f"🔧 {npc.name} 制造了 {item_name}",
            related_npcs=[npc.id],
            importance="medium"
        ))
        
        # 返回结果信息（包含消耗的材料）
        return {
            "item_name": item_name,
            "materials_used": recipe.required_materials
        }
    
    def complete_share_action(self, giver: NPC2D):
        """Complete a share action - transfer items between NPCs"""
        if not giver.action_target:
            logger.warning(f"❌ {giver.name} share行动没有目标")
            return None
        
        # 找到接收者NPC（可能是NPC名字或ID）
        target_identifier = giver.action_target
        receiver = None
        
        for npc in self.world_state.npcs:
            if npc.id == target_identifier or npc.name == target_identifier:
                receiver = npc
                break
        
        if not receiver:
            logger.warning(f"❌ {giver.name} 找不到目标NPC: {target_identifier}")
            return None
        
        # 检查距离
        distance = self.physics_engine.calculate_distance(giver.position, receiver.position)
        if distance > self.physics_engine.SOCIAL_RANGE:
            logger.warning(f"❌ {giver.name} 距离{receiver.name}太远 ({distance:.1f} 单位)，无法分享")
            return None
        
        # 决定分享什么物品（优先分享对方缺少的）
        item_to_share = None
        item_amount = 1
        
        # 检查receiver的需求
        if receiver.attributes.hunger > 50 and not receiver.in_conversation:
            # 对方饥饿，分享食物
            if giver.inventory.get("berry", 0) >= 3:
                item_to_share = "berry"
                item_amount = 3
            elif giver.inventory.get("water", 0) >= 2:
                item_to_share = "water"
                item_amount = 2
        
        # 如果对方缺少工具，分享工具
        if not item_to_share and not receiver.equipment:
            # 检查giver是否有多余的资源可以分享用于制造工具
            if giver.inventory.get("wood", 0) >= 3:
                item_to_share = "wood"
                item_amount = 2
            elif giver.inventory.get("stone", 0) >= 3:
                item_to_share = "stone"
                item_amount = 2
        
        # 默认分享一些资源
        if not item_to_share:
            for item, count in giver.inventory.items():
                if count >= 3:
                    item_to_share = item
                    item_amount = 2
                    break
        
        if not item_to_share:
            logger.warning(f"❌ {giver.name} 没有可以分享的物品")
            return None
        
        # 转移物品
        giver.inventory[item_to_share] = giver.inventory.get(item_to_share, 0) - item_amount
        if giver.inventory[item_to_share] <= 0:
            del giver.inventory[item_to_share]
        
        receiver.inventory[item_to_share] = receiver.inventory.get(item_to_share, 0) + item_amount
        
        # 给接收者添加记忆
        receiver.memories.append(f"{giver.name}分享了{item_amount}个{item_to_share}给我，真是个好伙伴！")
        if len(receiver.memories) > 30:
            receiver.memories = receiver.memories[-20:]
        
        # 提升双方的社交技能和好感度
        giver.skills["social"] = min(100, giver.skills.get("social", 0) + 2)
        receiver.skills["social"] = min(100, receiver.skills.get("social", 0) + 1)
        
        # 增加好感度
        giver.relationships[receiver.id] = min(100, giver.relationships.get(receiver.id, 0) + 10)
        receiver.relationships[giver.id] = min(100, receiver.relationships.get(giver.id, 0) + 15)
        
        logger.info(f"🎁 {giver.name} 分享了{item_amount}个{item_to_share}给{receiver.name}")
        
        # 添加事件
        self.world_state.add_event(GameEvent(
            id=f"event_{uuid.uuid4().hex[:8]}",
            type="share",
            description=f"🎁 {giver.name} 分享了{item_amount}个{item_to_share}给{receiver.name}",
            related_npcs=[giver.id, receiver.id],
            importance="medium"
        ))
        
        return {
            "item_name": f"{item_amount}个{item_to_share}",
            "target_name": receiver.name
        }
    
    async def process_beasts(self):
        """Process beast AI and movement"""
        if not self.world_state:
            return
        
        delta_time = 1.0  # 1 second per tick
        current_game_time = self.world_state.time.get_current_time()
        
        for beast in self.world_state.beasts:
            # 🐺 野兽AI决策（和NPC同频率：每30游戏秒）
            beast_last_decision = self.beast_last_decision.get(beast.id, 0)
            time_since_last_decision = current_game_time - beast_last_decision
            
            if time_since_last_decision >= self.beast_decision_interval:
                self._decide_beast_behavior(beast)
                self.beast_last_decision[beast.id] = current_game_time
            
            # 🔥 执行移动
            if beast.state == "wandering":
                self._move_beast_wander(beast, delta_time)
            elif beast.state == "chasing" and beast.target_npc:
                await self._move_beast_chase(beast, delta_time)
            elif beast.state == "fleeing":
                self._move_beast_flee(beast, delta_time)
            elif beast.state == "idle":
                # idle状态也有小概率移动
                if random.random() < 0.1:
                    beast.state = "wandering"
            
            # 🔥 野兽也会饥饿，饥饿时更积极追逐
            if hasattr(beast, 'hunger'):
                beast.hunger = min(100, getattr(beast, 'hunger', 0) + 0.02)  # 缓慢饥饿
                if beast.hunger > 70 and beast.is_aggressive():
                    # 饥饿时提高追逐距离
                    if beast.state == "wandering":
                        self._decide_beast_behavior(beast)  # 更频繁地寻找猎物
    
    def _decide_beast_behavior(self, beast):
        """决定野兽行为"""
        old_state = beast.state
        
        # 🛡️ 攻击性野兽也会感知危险
        # 如果生命值低于30%，逃离战场
        if beast.is_aggressive() and beast.health < beast.max_health * 0.3:
            if old_state != "fleeing":
                beast.state = "fleeing"
                logger.info(f"💔 {beast.type}[{beast.id[:8]}] 受伤严重（生命{beast.health:.0f}/{beast.max_health}），逃离战场！")
            else:
                beast.state = "fleeing"
            return
        
        # 🛡️ 检查周围是否有多个NPC且有武器，避免被围攻
        if beast.is_aggressive():
            nearby_armed_npcs = []
            for npc in self.world_state.npcs:
                if not npc.is_alive:
                    continue
                distance = self.physics_engine.calculate_distance(beast.position, npc.position)
                if distance < 10:  # 10单位内
                    # 检查NPC是否有武器
                    has_weapon = "spear" in npc.equipment or npc.inventory.get("stone", 0) > 0
                    if has_weapon and npc.attributes.health > 50:
                        nearby_armed_npcs.append((npc, distance))
            
            # 如果附近有2个以上武装NPC，逃离
            if len(nearby_armed_npcs) >= 2:
                if old_state != "fleeing":
                    beast.state = "fleeing"
                    logger.info(f"⚠️ {beast.type}[{beast.id[:8]}] 感知到危险（{len(nearby_armed_npcs)}个武装NPC），战略撤退！")
                else:
                    beast.state = "fleeing"
                return
        
        # 攻击性野兽：寻找NPC攻击
        if beast.is_aggressive():
            # 寻找最近的NPC
            nearest_npc = None
            min_distance = float('inf')
            
            for npc in self.world_state.npcs:
                if not npc.is_alive:  # 忽略死亡的NPC
                    continue
                distance = self.physics_engine.calculate_distance(
                    beast.position, npc.position
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_npc = npc
            
            # 🔥 群体狩猎：检查附近是否有同类在追逐
            pack_hunting = False
            if beast.type == "wolf" and nearest_npc:
                for other_beast in self.world_state.beasts:
                    if other_beast.id != beast.id and other_beast.type == "wolf" and other_beast.state == "chasing":
                        # 检查是否在追逐同一个NPC
                        if other_beast.target_npc == nearest_npc.id:
                            pack_distance = self.physics_engine.calculate_distance(
                                beast.position, other_beast.position
                            )
                            if pack_distance < 20:  # 狼群协作范围
                                pack_hunting = True
                                if old_state != "chasing":
                                    logger.info(f"🐺 {beast.type}[{beast.id[:8]}] 加入狼群协同狩猎{nearest_npc.name}！")
                                break
            
            # 🔥 根据情况决定追逐距离
            chase_range = 15
            if pack_hunting:
                chase_range = 20  # 群体狩猎时追逐距离更远
            if hasattr(beast, 'hunger') and getattr(beast, 'hunger', 0) > 70:
                chase_range = 18  # 饥饿时追逐距离更远
            
            # 如果NPC在范围内，开始追逐
            if nearest_npc and min_distance < chase_range:
                beast.state = "chasing"
                beast.target_npc = nearest_npc.id
                if old_state != "chasing":  # 状态改变时才记录
                    logger.info(f"🐺 {beast.type}[{beast.id[:8]}] 在({beast.position.x:.1f},{beast.position.y:.1f})发现{nearest_npc.name}，开始追逐（距离{min_distance:.1f}）{'[狼群协作]' if pack_hunting else ''}")
            else:
                beast.state = "wandering"
                if old_state == "chasing":
                    logger.info(f"🐺 {beast.type}[{beast.id[:8]}] 失去目标，继续游荡")
        else:
            # 温和动物：检查是否需要逃离
            nearest_npc_distance = float('inf')
            for npc in self.world_state.npcs:
                if not npc.is_alive:
                    continue
                distance = self.physics_engine.calculate_distance(
                    beast.position, npc.position
                )
                nearest_npc_distance = min(nearest_npc_distance, distance)
            
            # 如果NPC太近，逃离
            if nearest_npc_distance < 8:
                if old_state != "fleeing":
                    beast.state = "fleeing"
                    logger.info(f"🐰 {beast.type}[{beast.id[:8]}] 在({beast.position.x:.1f},{beast.position.y:.1f})发现威胁，开始逃离")
                else:
                    beast.state = "fleeing"
            else:
                beast.state = "wandering"
    
    def _move_beast_wander(self, beast, delta_time: float):
        """野兽随机游荡 - 平滑移动版本"""
        # 🎬 如果有移动目标，平滑移动到目标
        if beast.is_moving and beast.move_target:
            dx = beast.move_target.x - beast.position.x
            dy = beast.move_target.y - beast.position.y
            distance = (dx**2 + dy**2)**0.5
            
            if distance < 0.5:  # 到达目标
                beast.is_moving = False
                beast.move_target = None
            else:
                # 平滑移动
                move_distance = beast.speed * delta_time * 0.5  # 游荡速度减半
                ratio = min(move_distance / distance, 1.0)
                beast.position.x += dx * ratio
                beast.position.y += dy * ratio
        else:
            # 🔥 20%概率设置新的游荡目标
            if random.random() < 0.2:
                # 在附近随机选择目标点
                angle = random.uniform(0, 2 * 3.14159)
                wander_distance = random.uniform(2, 5)  # 2-5单位的游荡距离
                
                target_x = beast.position.x + wander_distance * math.cos(angle)
                target_y = beast.position.y + wander_distance * math.sin(angle)
                
                # 边界检查
                target_x = max(0, min(100, target_x))
                target_y = max(0, min(100, target_y))
                
                beast.is_moving = True
                beast.move_target = Position2D(x=target_x, y=target_y)
                
                # 🔥 记录移动（每10次记录一次，避免日志过多）
                if random.random() < 0.1:
                    logger.info(f"🦌 {beast.type}[{beast.id[:8]}] 设置游荡目标: ({beast.position.x:.1f},{beast.position.y:.1f}) -> ({target_x:.1f},{target_y:.1f})")
    
    async def _move_beast_chase(self, beast, delta_time: float):
        """野兽追逐目标"""
        # 找到目标NPC
        target_npc = None
        for npc in self.world_state.npcs:
            if npc.id == beast.target_npc:
                target_npc = npc
                break
        
        if not target_npc:
            beast.state = "wandering"
            beast.target_npc = None
            return
        
        # 检查距离
        distance = self.physics_engine.calculate_distance(
            beast.position, target_npc.position
        )
        
        # 如果太远，放弃追逐
        if distance > 25:
            beast.state = "wandering"
            beast.target_npc = None
            logger.info(f"🐺 {beast.type}[{beast.id[:8]}] 放弃追逐（距离{distance:.1f}）")
            return
        
        # 如果进入攻击范围，攻击（检查冷却时间）
        current_time = self.world_state.time.get_current_time()
        attack_range = self.physics_engine.ATTACK_RANGE  # 使用基础攻击距离2.5，避免重叠
        if distance < attack_range:
            # ⏰ 检查攻击冷却
            time_since_last_attack = current_time - beast.last_attack_time
            if time_since_last_attack >= beast.attack_cooldown:
                beast.last_attack_time = current_time
                await self._beast_attack_npc(beast, target_npc)
            return
        
        # 🎬 平滑追逐移动（但不要移动到攻击范围内，避免重叠）
        dx = target_npc.position.x - beast.position.x
        dy = target_npc.position.y - beast.position.y
        
        if distance > attack_range:  # 只在超出攻击范围时移动
            # 计算移动距离，但确保不会越过攻击范围
            move_distance = beast.speed * delta_time
            # 🔧 限制：移动后的距离不应小于攻击范围
            max_move = distance - attack_range  # 最多移动到攻击范围边缘
            move_distance = min(move_distance, max_move)
            
            if move_distance > 0:
                ratio = move_distance / distance
                beast.position.x += dx * ratio
                beast.position.y += dy * ratio
        
        # 🔥 记录追逐移动（每5次记录一次）
        if random.random() < 0.2:
            logger.info(f"🐺 {beast.type}[{beast.id[:8]}] 追逐{target_npc.name}: 距离{distance:.1f}")
    
    def _calculate_smart_escape_direction(self, npc: NPC2D) -> dict:
        """
        🧠 智能计算逃跑方向
        
        真实的逃跑逻辑：
        1. 评估所有周围的威胁（不只是最近的一只）
        2. 计算综合的"危险向量场"（所有威胁的合力）
        3. 寻找安全区域（有建筑、有队友的地方）
        4. 避免地图边界和死角
        5. 选择威胁密度最低的方向
        """
        # 📍 第一步：收集所有威胁信息
        threats = []
        for beast in self.world_state.beasts:
            if not beast.is_aggressive():
                continue
            
            dx = beast.position.x - npc.position.x
            dy = beast.position.y - npc.position.y
            distance = (dx**2 + dy**2)**0.5
            
            # 只考虑附近的威胁（40单位内）
            if distance < 40 and distance > 0:
                threats.append({
                    'beast': beast,
                    'dx': dx,
                    'dy': dy,
                    'distance': distance,
                    'threat_level': 1.0 / distance  # 距离越近，威胁越大
                })
        
        if not threats:
            # 没有威胁，随机移动到安全位置
            return {
                'target_x': npc.position.x + random.uniform(-10, 10),
                'target_y': npc.position.y + random.uniform(-10, 10),
                'description': '逃离（未发现明确威胁）'
            }
        
        # 📊 第二步：计算综合危险向量场
        # 所有威胁的合力方向（加权平均）
        danger_vector_x = 0
        danger_vector_y = 0
        total_threat = 0
        
        for threat in threats:
            # 威胁向量指向威胁源
            weight = threat['threat_level']
            danger_vector_x += (threat['dx'] / threat['distance']) * weight
            danger_vector_y += (threat['dy'] / threat['distance']) * weight
            total_threat += weight
        
        if total_threat > 0:
            danger_vector_x /= total_threat
            danger_vector_y /= total_threat
        
        # 安全方向：与危险向量相反
        safe_direction_x = -danger_vector_x
        safe_direction_y = -danger_vector_y
        
        # 标准化安全方向
        safe_magnitude = (safe_direction_x**2 + safe_direction_y**2)**0.5
        if safe_magnitude > 0:
            safe_direction_x /= safe_magnitude
            safe_direction_y /= safe_magnitude
        
        # 🏘️ 第三步：寻找安全区域加成
        # 检查是否有建筑物可以逃向
        best_building_bonus_x = 0
        best_building_bonus_y = 0
        
        for building in self.world_state.buildings:
            if not building.is_completed:
                continue
                
            building_dx = building.position.x - npc.position.x
            building_dy = building.position.y - npc.position.y
            building_dist = (building_dx**2 + building_dy**2)**0.5
            
            if building_dist > 0 and building_dist < 30:
                # 检查建筑物附近是否安全（没有太多威胁）
                threats_near_building = 0
                for threat in threats:
                    threat_to_building = ((threat['beast'].position.x - building.position.x)**2 + 
                                         (threat['beast'].position.y - building.position.y)**2)**0.5
                    if threat_to_building < 15:
                        threats_near_building += 1
                
                # 如果建筑物附近相对安全，增加向建筑逃跑的倾向
                if threats_near_building == 0:
                    building_bonus = 0.3 / building_dist  # 距离越近，加成越大
                    best_building_bonus_x = (building_dx / building_dist) * building_bonus
                    best_building_bonus_y = (building_dy / building_dist) * building_bonus
        
        # 👥 第四步：考虑队友位置（队友多的地方可能更安全）
        ally_bonus_x = 0
        ally_bonus_y = 0
        
        for other_npc in self.world_state.npcs:
            if other_npc.id == npc.id or not other_npc.is_alive:
                continue
            
            ally_dx = other_npc.position.x - npc.position.x
            ally_dy = other_npc.position.y - npc.position.y
            ally_dist = (ally_dx**2 + ally_dy**2)**0.5
            
            if ally_dist > 0 and ally_dist < 25:
                # 检查队友是否有武器（更安全）
                has_weapon = "spear" in other_npc.equipment
                if has_weapon and other_npc.attributes.health > 50:
                    ally_bonus = 0.2 / ally_dist
                    ally_bonus_x += (ally_dx / ally_dist) * ally_bonus
                    ally_bonus_y += (ally_dy / ally_dist) * ally_bonus
        
        # 🗺️ 第五步：避免地图边界
        boundary_penalty_x = 0
        boundary_penalty_y = 0
        
        # 如果靠近边界，增加远离边界的倾向
        if npc.position.x < 15:
            boundary_penalty_x = 0.3  # 向右
        elif npc.position.x > 85:
            boundary_penalty_x = -0.3  # 向左
        
        if npc.position.y < 15:
            boundary_penalty_y = 0.3  # 向下
        elif npc.position.y > 85:
            boundary_penalty_y = -0.3  # 向上
        
        # 🎯 第六步：综合所有因素计算最终逃跑方向
        final_direction_x = (safe_direction_x * 1.0 +      # 主要因素：远离威胁
                            best_building_bonus_x * 0.5 +   # 次要因素：靠近建筑
                            ally_bonus_x * 0.3 +             # 次要因素：靠近武装队友
                            boundary_penalty_x * 0.8)        # 重要因素：避免边界
        
        final_direction_y = (safe_direction_y * 1.0 +
                            best_building_bonus_y * 0.5 +
                            ally_bonus_y * 0.3 +
                            boundary_penalty_y * 0.8)
        
        # 标准化最终方向
        final_magnitude = (final_direction_x**2 + final_direction_y**2)**0.5
        if final_magnitude > 0:
            final_direction_x /= final_magnitude
            final_direction_y /= final_magnitude
        
        # 🎲 第七步：多方向采样，选择最安全的路径
        # 在主方向附近采样多个可能的逃跑方向，选择威胁最少的
        best_escape_x = npc.position.x + final_direction_x * 15
        best_escape_y = npc.position.y + final_direction_y * 15
        min_total_threat_at_destination = float('inf')
        
        # 采样5个方向（主方向 + 左右偏移）
        for angle_offset in [-30, -15, 0, 15, 30]:
            angle_rad = math.atan2(final_direction_y, final_direction_x) + math.radians(angle_offset)
            test_x = npc.position.x + math.cos(angle_rad) * 15
            test_y = npc.position.y + math.sin(angle_rad) * 15
            
            # 边界检查
            test_x = max(10, min(90, test_x))
            test_y = max(10, min(90, test_y))
            
            # 计算该位置的总威胁值
            threat_at_destination = 0
            for threat in threats:
                dx_to_dest = threat['beast'].position.x - test_x
                dy_to_dest = threat['beast'].position.y - test_y
                dist_to_dest = (dx_to_dest**2 + dy_to_dest**2)**0.5
                if dist_to_dest < 20:  # 如果逃跑目标点离威胁太近，增加惩罚
                    threat_at_destination += 10.0 / (dist_to_dest + 0.1)
            
            # 选择威胁最小的方向
            if threat_at_destination < min_total_threat_at_destination:
                min_total_threat_at_destination = threat_at_destination
                best_escape_x = test_x
                best_escape_y = test_y
        
        # 📝 生成描述性信息
        threat_count = len(threats)
        closest_threat = min(threats, key=lambda t: t['distance'])
        
        description = f"智能逃离{threat_count}个威胁（最近的{closest_threat['beast'].type}距离{closest_threat['distance']:.1f}单位）"
        
        return {
            'target_x': best_escape_x,
            'target_y': best_escape_y,
            'description': description,
            'threat_count': threat_count,
            'closest_distance': closest_threat['distance']
        }
    
    def _move_beast_flee(self, beast, delta_time: float):
        """野兽逃离 - 平滑移动版本"""
        # 找到最近的NPC
        nearest_npc = None
        min_distance = float('inf')
        
        for npc in self.world_state.npcs:
            distance = self.physics_engine.calculate_distance(
                beast.position, npc.position
            )
            if distance < min_distance:
                min_distance = distance
                nearest_npc = npc
        
        if not nearest_npc or min_distance > 15:
            # 安全了，回到游荡
            beast.state = "wandering"
            beast.is_moving = False
            beast.move_target = None
            return
        
        # 🎬 平滑逃离移动
        # 远离NPC的方向
        dx = beast.position.x - nearest_npc.position.x
        dy = beast.position.y - nearest_npc.position.y
        distance = (dx**2 + dy**2)**0.5
        
        if distance > 0:
            # 标准化方向
            dx /= distance
            dy /= distance
            
            # 逃跑速度更快（1.5倍）
            move_distance = beast.speed * delta_time * 1.5
            beast.position.x += dx * move_distance
            beast.position.y += dy * move_distance
            
            # 边界检查
            beast.position.x = max(0, min(100, beast.position.x))
            beast.position.y = max(0, min(100, beast.position.y))
    
    async def _beast_attack_npc(self, beast, npc: NPC2D):
        """野兽攻击NPC"""
        # 造成伤害
        npc.attributes.health = max(0, npc.attributes.health - beast.damage)
        
        # ⚔️ NPC自动反击机制
        counter_attack_success = False
        if npc.is_alive and npc.attributes.health > 20:
            # 反击条件：
            # 1. 有武器或石头
            # 2. 勇敢度 > 40 或 健康 > 60
            # 3. 体力 > 20
            has_weapon = "spear" in npc.equipment or npc.inventory.get("stone", 0) > 0
            brave_enough = npc.personality.bravery > 40
            healthy_enough = npc.attributes.health > 60
            has_stamina = npc.attributes.stamina > 20
            
            if has_weapon and (brave_enough or healthy_enough) and has_stamina:
                # 计算反击伤害（简化版本）
                counter_damage = 10 + npc.skills.get("combat", 0) * 0.5
                if "spear" in npc.equipment:
                    counter_damage += 15
                elif npc.inventory.get("stone", 0) > 0:
                    counter_damage += 5
                
                # 造成反击伤害
                beast_killed = beast.take_damage(counter_damage)
                npc.attributes.stamina = max(0, npc.attributes.stamina - 8)
                npc.skills["combat"] = min(100, npc.skills.get("combat", 0) + 1)
                
                counter_attack_success = True
                logger.info(f"⚔️ {npc.name} 英勇反击{beast.type}，造成{counter_damage:.1f}伤害！")
                
                if beast_killed:
                    self.world_state.beasts.remove(beast)
                    logger.info(f"🎉 {npc.name} 反击击杀了{beast.type}！")
                    
                    # 掉落生肉
                    meat_amounts = {"rabbit": 2, "wolf": 3, "bear": 5, "deer": 4}
                    meat_amount = meat_amounts.get(beast.type, 2)
                    npc.inventory["raw_meat"] = npc.inventory.get("raw_meat", 0) + meat_amount
                    
                    self.world_state.add_event(GameEvent(
                        id=f"counter_kill_{uuid.uuid4().hex[:8]}",
                        type="beast_killed",
                        description=f"⚔️ {npc.name}在反击中击杀了{beast.type}！获得{meat_amount}生肉",
                        related_npcs=[npc.id],
                        importance="high"
                    ))
        
        # 🔥 记录NPC的记忆
        if counter_attack_success:
            memory = f"在({npc.position.x:.0f},{npc.position.y:.0f})遭到{beast.type}攻击，英勇反击！"
        else:
            memory = f"在({npc.position.x:.0f},{npc.position.y:.0f})遭到{beast.type}[ID:{beast.id[:8]}]的攻击！受伤了，感到害怕"
        
        npc.memories.append(memory)
        await self.memory_service.record_event(npc.id, "beast_attack", memory)
        if len(npc.memories) > 30:
            npc.memories = npc.memories[-20:]
        
        # 🔥 记录更详细的事件
        self.world_state.add_event(GameEvent(
            id=f"attack_{uuid.uuid4().hex[:8]}",
            type="beast_attack",
            description=f"⚔️ {beast.type}[{beast.id[:8]}]在({beast.position.x:.1f},{beast.position.y:.1f})攻击了{npc.name}！造成{beast.damage:.0f}点伤害（生命{npc.attributes.health:.0f}/100）",
            related_npcs=[npc.id],
            importance="high"
        ))
        
        # 🔥 更详细的日志
        logger.warning(f"⚔️ {beast.type}[{beast.id[:8]}] 在({beast.position.x:.1f},{beast.position.y:.1f})攻击{npc.name}，造成{beast.damage:.0f}伤害 → 生命{npc.attributes.health:.0f}/100")
        
        # 🚨 关键修复：被攻击时立即中断当前行动，进入逃跑状态
        if not counter_attack_success and npc.is_alive:
            # 检查是否应该逃跑（生命值低或没有武器）
            should_flee = (
                npc.attributes.health < 50 or  # 生命值低于50
                ("spear" not in npc.equipment and npc.inventory.get("stone", 0) == 0)  # 没有武器
            )
            
            if should_flee:
                # 🎯 释放资源占用
                self.release_resource_occupation(npc)
                
                # 立即中断当前行动
                npc.current_action = None
                npc.action_target = None
                npc.action_state = "idle"
                npc.action_end_time = None
                npc.is_moving = False
                npc.move_target = None
                
                # 强制进入紧急状态，下次process_npcs会让AI决策flee
                npc.last_action_result = f"❗ 紧急！被{beast.type}攻击受伤！生命{npc.attributes.health:.0f}/100，必须立即逃跑！"
                
                logger.warning(f"🚨 {npc.name} 被攻击，中断当前行动，准备逃跑！")
        
        # 🚨 通知附近的NPC立即响应（团队支援）
        for other_npc in self.world_state.npcs:
            if other_npc.id != npc.id and other_npc.is_alive:
                distance = self.physics_engine.calculate_distance(
                    npc.position, other_npc.position
                )
                if distance < 15:  # 15单位内的NPC会看到攻击
                    witness_memory = f"看到{npc.name}被{beast.type}攻击，需要帮助！"
                    other_npc.memories.append(witness_memory)
                    await self.memory_service.record_event(other_npc.id, "witness_attack", witness_memory)
                    if len(other_npc.memories) > 30:
                        other_npc.memories = other_npc.memories[-20:]
                    
                    # 🚨 立即中断当前行动，触发支援响应
                    # 只有健康>50且有武器的NPC才考虑支援
                    has_weapon = "spear" in other_npc.equipment or other_npc.inventory.get("stone", 0) > 0
                    can_help = other_npc.attributes.health > 50 and has_weapon
                    
                    if can_help and other_npc.personality.bravery > 30:  # 勇敢度>30才会支援
                        # 🎯 释放资源占用
                        self.release_resource_occupation(other_npc)
                        
                        # 中断当前行动
                        other_npc.current_action = None
                        other_npc.action_target = None
                        other_npc.action_state = "idle"
                        other_npc.action_end_time = None
                        
                        other_npc.last_action_result = f"⚠️ 看到{npc.name}被{beast.type}攻击！需要支援！"
                        logger.info(f"🤝 {other_npc.name} 看到{npc.name}被攻击，准备支援！")
                    else:
                        # 没有能力支援，但至少提醒自己小心
                        if not can_help:
                            other_npc.last_action_result = f"⚠️ 看到{npc.name}被攻击，但我{('没有武器' if not has_weapon else '健康太低')}，小心野兽！"
        
        # 攻击后短暂停留
        beast.state = "idle"
    
    async def _record_environmental_observation(self, npc: NPC2D):
        """记录NPC对环境的观察"""
        # 观察附近的资源
        nearby_resources = []
        for resource in self.world_state.resources:
            if not resource.is_depleted:
                distance = self.physics_engine.calculate_distance(
                    npc.position, resource.position
                )
                if distance < 10:  # 10单位内
                    nearby_resources.append((resource.type, distance))
        
        if nearby_resources and random.random() < 0.3:  # 30%概率记录
            # 按距离排序，记录最近的
            nearby_resources.sort(key=lambda x: x[1])
            resource_type, distance = nearby_resources[0]
            memory = f"注意到附近有{resource_type}资源"
            npc.memories.append(memory)
            await self.memory_service.record_event(npc.id, "observation", memory)
        
        # 观察附近的野兽
        nearby_beasts = []
        for beast in self.world_state.beasts:
            distance = self.physics_engine.calculate_distance(
                npc.position, beast.position
            )
            if distance < 12:  # 12单位内
                nearby_beasts.append((beast.type, beast.is_aggressive(), distance))
        
        if nearby_beasts and random.random() < 0.4:  # 40%概率记录野兽
            beast_type, is_aggressive, distance = nearby_beasts[0]
            if is_aggressive:
                memory = f"看到危险的{beast_type}在附近游荡，保持警惕"
            else:
                memory = f"看到{beast_type}在附近活动"
            npc.memories.append(memory)
            await self.memory_service.record_event(npc.id, "observation", memory)
        
        # 观察附近的NPC
        nearby_npcs = []
        for other_npc in self.world_state.npcs:
            if other_npc.id != npc.id:
                distance = self.physics_engine.calculate_distance(
                    npc.position, other_npc.position
                )
                if distance < 8:  # 8单位内
                    nearby_npcs.append((other_npc.name, distance))
        
        if nearby_npcs and random.random() < 0.25:  # 25%概率记录
            other_name, distance = nearby_npcs[0]
            memory = f"遇到了{other_name}，他/她看起来在忙着"
            npc.memories.append(memory)
            await self.memory_service.record_event(npc.id, "observation", memory)
    
    def process_resources(self):
        """Process resource regeneration"""
        if not self.world_state:
            return
        
        current_time = self.world_state.time.get_current_time()
        
        # 🔥 资源再生配置（游戏时间-秒）
        # 2天游戏时间 = 2 * 24 * 60 * 60 = 172800秒
        DAY_IN_SECONDS = 24 * 60 * 60  # 1天 = 86400秒
        regeneration_time = {
            "wood": 2 * DAY_IN_SECONDS,    # 树木再生：2天
            "stone": 3 * DAY_IN_SECONDS,   # 石头再生：3天
            "berry": 1.5 * DAY_IN_SECONDS, # 浆果再生：1.5天
            "water": 1 * DAY_IN_SECONDS,   # 水源再生：1天
        }
        
        for resource in self.world_state.resources:
            if resource.is_depleted:
                # 🔥 检查枯竭资源的再生
                regen_time = regeneration_time.get(resource.type, 2 * DAY_IN_SECONDS)
                time_since_depleted = current_time - resource.depleted_time
                
                if time_since_depleted >= regen_time:
                    # 再生
                    resource.quantity = resource.max_quantity
                    resource.is_depleted = False
                    resource.depleted_time = 0.0
                    logger.info(f"✨ 资源再生: {resource.type} at ({resource.position.x:.1f}, {resource.position.y:.1f})")
                    
                    # 添加事件
                    self.world_state.add_event(GameEvent(
                        id=f"event_{uuid.uuid4().hex[:8]}",
                        type="resource_regenerated",
                        description=f"一处{resource.type}资源重新生长了",
                        importance="low"
                    ))
            
            # 🔥 修复：只有枯竭的资源才再生，避免NPC一直在原地采集
            # 删除了未枯竭资源的自动恢复逻辑，鼓励NPC探索新资源
    
    def process_buildings(self):
        """Process building construction progress"""
        if not self.world_state:
            return
        
        current_time = self.world_state.time.get_current_time()
        delta_time = 1.0  # 1 second per tick
        
        for building in self.world_state.buildings:
            if building.is_complete:
                continue  # Skip completed buildings
            
            # 找到所有正在建造此建筑的NPC
            active_builders = []
            for npc in self.world_state.npcs:
                if (npc.current_action == "build" and 
                    npc.action_target == building.id and
                    npc.is_alive):
                    # 检查距离（必须在建筑附近）
                    distance = self.physics_engine.calculate_distance(
                        npc.position, building.position
                    )
                    if distance < 5:  # 5单位内才能建造
                        active_builders.append(npc)
            
            # 更新建造者列表
            building.builders = [npc.id for npc in active_builders]
            
            if not active_builders:
                continue  # 没有建造者，跳过
            
            # 计算建造进度
            # 基础进度：1个NPC每秒推进 delta_time / build_time_total
            # 多NPC合作：每多一个NPC增加50%效率
            base_progress_rate = delta_time / building.build_time_total
            cooperation_bonus = 1.0 + (len(active_builders) - 1) * 0.5
            progress_delta = base_progress_rate * cooperation_bonus
            
            building.build_time_elapsed += delta_time
            building.construction_progress += progress_delta
            
            # 限制进度在0-1之间
            building.construction_progress = min(1.0, building.construction_progress)
            
            # 检查是否完成
            if building.construction_progress >= 1.0:
                building.is_complete = True
                building.construction_progress = 1.0
                
                logger.info(f"🎉 建筑完成！{building.name} 由 {', '.join([npc.name for npc in active_builders])} 建造")
                
                # 添加完成事件
                self.world_state.add_event(GameEvent(
                    id=f"build_complete_{uuid.uuid4().hex[:8]}",
                    type="build_complete",
                    description=f"🎉 {building.name}建造完成！由{', '.join([npc.name for npc in active_builders])}完成",
                    related_npcs=[npc.id for npc in active_builders],
                    importance="high"
                ))
                
                # 为所有参与建造的NPC添加记忆和奖励
                for npc in active_builders:
                    # 添加记忆
                    memory = f"与{'、'.join([b.name for b in active_builders if b.id != npc.id])}一起完成了{building.name}的建造"
                    npc.memories.append(memory)
                    if len(npc.memories) > 30:
                        npc.memories = npc.memories[-20:]
                    
                    # 提升建造技能
                    npc.skills["construction"] = min(100, npc.skills.get("construction", 0) + 5)
                    
                    # 设置最后行动结果
                    npc.last_action_result = f"✅ 成功建造{building.name}！\n建造技能+5\n当前位置: ({building.position.x:.1f}, {building.position.y:.1f})"
                    
                    # 结束build行动
                    npc.action_state = "cooling"
                    npc.action_end_time = current_time + 3.0  # 3秒冷却
                    npc.current_action = None
                    npc.action_target = None
                    npc.current_todo = None
                    npc.todo_steps = []
            else:
                # 建造中，记录进度
                if random.random() < 0.1:  # 10%概率记录（避免日志过多）
                    logger.info(f"🏗️ 建造中... {building.name} 进度: {building.construction_progress*100:.1f}% (建造者: {', '.join([npc.name for npc in active_builders])})")
            
            # 如果需要合作但只有一个人，减速
            if building.requires_cooperation and len(active_builders) == 1:
                logger.warning(f"⚠️ {building.name}需要多人合作，单人建造效率低下！")
                # 已经在cooperation_bonus中体现了（单人时bonus=1.0）
    
    async def initiate_conversation(self, initiator: NPC2D, current_time: float):
        """Initiate a conversation with nearby NPCs - 使用AI生成真实对话"""
        # 找到附近所有可以对话的NPC
        nearby_npcs = []
        for other_npc in self.world_state.npcs:
            if other_npc.id == initiator.id:
                continue
            if other_npc.in_conversation:  # 已经在对话中
                continue
            if not other_npc.is_alive:
                continue
            
            distance = self.physics_engine.calculate_distance(
                initiator.position, other_npc.position
            )
            
            # 在社交范围内（5单位）
            if distance <= self.physics_engine.SOCIAL_RANGE:
                nearby_npcs.append((other_npc, distance))
        
        if not nearby_npcs:
            logger.info(f"💬 {initiator.name} 想要交流但附近没有其他人")
            # 取消talk行动
            initiator.action_state = "idle"
            initiator.current_action = None
            return
        
        # 选择最近的1-2个NPC加入对话（支持多人对话）
        nearby_npcs.sort(key=lambda x: x[1])  # 按距离排序
        conversation_partners = [npc for npc, _ in nearby_npcs[:1]]  # 先支持1对1对话
        
        # 🎯 使用AI生成真实对话内容和类型
        dialogue_result = await self.ai_service.generate_conversation_dialogue(
            initiator, 
            conversation_partners, 
            self.world_state
        )
        
        # 创建对话会话
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        all_participants = [initiator] + conversation_partners
        participant_ids = [npc.id for npc in all_participants]
        participant_names = [npc.name for npc in all_participants]
        
        # 导入对话类型枚举
        from app.models.conversation import Conversation, ConversationType
        
        # 转换对话类型字符串为枚举
        conv_type_str = dialogue_result.get("conversation_type", "small_talk")
        conv_type = ConversationType(conv_type_str) if conv_type_str in ConversationType.__members__.values() else ConversationType.SMALL_TALK
        
        conversation = Conversation(
            id=conversation_id,
            participants=participant_ids,
            participant_names=participant_names,
            started_at=current_time,
            location={"x": initiator.position.x, "y": initiator.position.y},
            conversation_type=conv_type,
            topic=dialogue_result.get("topic", "聊天"),
            triggers_action=dialogue_result.get("triggers_action", False),
            planned_action=dialogue_result.get("planned_action")
        )
        
        # 添加AI生成的对话消息
        for msg in dialogue_result.get("messages", []):
            conversation.add_message(
                speaker_id="",  # 这里speaker_id可以从名字映射
                speaker_name=msg["speaker"],
                content=msg["content"],
                timestamp=current_time
            )
        
        # 将所有参与者标记为对话中
        for npc in all_participants:
            npc.in_conversation = True
            npc.conversation_id = conversation_id
            npc.conversation_partners = [p for p in participant_ids if p != npc.id]
        
        # 添加到活跃对话列表和world_state
        self.active_conversations[conversation_id] = conversation
        self.world_state.conversations.append(conversation)
        
        logger.info(f"💬 对话开始: {', '.join(participant_names)} (类型: {conv_type}, 话题: {conversation.topic})")
        if conversation.triggers_action:
            logger.info(f"   🎯 此对话将触发后续行动: {conversation.planned_action}")
        
        # 添加事件
        self.world_state.add_event(GameEvent(
            id=f"event_{conversation_id}",
            type="conversation_start",
            description=f"💬 {', '.join(participant_names)} 开始了{conv_type}对话（{conversation.topic}）",
            related_npcs=participant_ids,
            importance="medium"
        ))
        
        # 广播对话事件（包含完整消息）
        if self.broadcast_callback:
            await self.broadcast_callback('conversation_start', {
                'conversation_id': conversation_id,
                'participants': participant_names,
                'topic': conversation.topic,
                'conversation_type': conv_type,
                'messages': [{"speaker": msg.speaker_name, "content": msg.content} for msg in conversation.messages],
                'location': conversation.location,
                'triggers_action': conversation.triggers_action
            })
    
    async def complete_conversation(self, npc: NPC2D, current_time: float):
        """Complete a conversation and share memories among all participants"""
        if not npc.in_conversation or not npc.conversation_id:
            logger.warning(f"⚠️ {npc.name} 不在对话中")
            return
        
        conversation_id = npc.conversation_id
        conversation = self.active_conversations.get(conversation_id)
        
        if not conversation:
            logger.warning(f"⚠️ 对话{conversation_id}不存在")
            return
        
        # 结束对话
        conversation.end_conversation(current_time)
        
        # 🔥 使用AI生成具体对话内容和有用信息
        conversation_details = await self._generate_conversation_content(conversation)
        
        # 为所有参与者添加具体的记忆
        for i, participant_id in enumerate(conversation.participants):
            participant_npc = next((n for n in self.world_state.npcs if n.id == participant_id), None)
            if participant_npc:
                participant_name = conversation.participant_names[i]
                
                # 为每个参与者生成个性化的记忆（从自己的角度）
                # 先尝试通过名字获取，如果没有则使用默认
                personal_memory = conversation_details.get(participant_name, 
                    f"与{', '.join([n for n in conversation.participant_names if n != participant_name])}讨论了{conversation.topic}"
                )
                
                # 如果personal_memory是字符串，直接使用；如果是dict，提取memory字段
                if isinstance(personal_memory, dict):
                    personal_memory = personal_memory.get('memory', personal_memory)
                
                # 添加记忆
                participant_npc.memories.append(personal_memory)
                await self.memory_service.record_event(participant_id, "conversation", personal_memory, importance=6)
                if len(participant_npc.memories) > 30:
                    participant_npc.memories = participant_npc.memories[-20:]
                
                # 清除对话状态
                participant_npc.in_conversation = False
                participant_npc.conversation_id = None
                participant_npc.conversation_partners = []
                
                # 提升社交技能
                participant_npc.skills["social"] = min(100, participant_npc.skills.get("social", 0) + 1)
        
        summary = conversation_details.get('summary', f"关于{conversation.topic}的对话")
        logger.info(f"💬 对话结束: {', '.join(conversation.participant_names)} - {summary}")
        
        # 🎯 如果对话触发后续行动，为参与者安排行动
        if conversation.triggers_action and conversation.planned_action:
            logger.info(f"🎯 对话触发后续行动: {conversation.planned_action}")
            planned = conversation.planned_action
            
            # 导入NPCAction
            from app.models.actions import NPCAction
            
            # 为所有参与者分配行动（或根据行动类型分配给发起者）
            for participant_id in conversation.participants:
                participant_npc = next((n for n in self.world_state.npcs if n.id == participant_id), None)
                if participant_npc and participant_npc.is_alive:
                    # 创建行动
                    action = NPCAction(
                        action=planned.get("action", "build"),
                        target=planned.get("target", ""),
                        reasoning=f"对话后决定: {planned.get('reason', '执行计划')}",
                        duration=planned.get("duration", 60),
                        priority="high"
                    )
                    
                    # 只有当NPC是idle状态时才分配新行动
                    if participant_npc.action_state == "idle":
                        await self.execute_action(participant_npc, action, current_time)
                        logger.info(f"   🎯 为{participant_npc.name}分配行动: {action.action} {action.target}")
                    else:
                        logger.info(f"   ⏸️ {participant_npc.name}正忙，将在下次空闲时考虑此行动")
        
        # 添加结束事件
        self.world_state.add_event(GameEvent(
            id=f"event_{conversation_id}_end",
            type="conversation_end",
            description=f"💬 {', '.join(conversation.participant_names)} 结束了对话: {summary}",
            related_npcs=conversation.participants,
            importance="low"
        ))
        
        # 广播对话结束
        if self.broadcast_callback:
            await self.broadcast_callback('conversation_end', {
                'conversation_id': conversation_id,
                'participants': conversation.participant_names,
                'topic': conversation.topic,
                'summary': summary,
                'triggers_action': conversation.triggers_action
            })
        
        # 从活跃对话列表中移除
        del self.active_conversations[conversation_id]
    
    async def _generate_conversation_content(self, conversation: 'Conversation') -> Dict:
        """使用AI生成具体的对话内容和有用信息"""
        try:
            # 获取所有参与者的NPC对象
            participants_npcs = []
            for pid in conversation.participants:
                npc = next((n for n in self.world_state.npcs if n.id == pid), None)
                if npc:
                    participants_npcs.append(npc)
            
            if not participants_npcs:
                return {}
            
            # 构建参与者信息
            participants_info = []
            for npc in participants_npcs:
                info = f"{npc.name}: 健康{npc.attributes.health:.0f}, 饱食度{100-npc.attributes.hunger:.0f}, "
                info += f"库存{dict(npc.inventory)}, 装备{list(npc.equipment.keys())}"
                participants_info.append(info)
            
            # 让AI生成对话内容
            result = await self.ai_service.generate_conversation_summary(
                participant_names=conversation.participant_names,
                participants_info=participants_info,
                topic=conversation.topic,
                duration=conversation.ended_at - conversation.started_at if conversation.ended_at else 30
            )
            
            return result
            
        except Exception as e:
            logger.error(f"生成对话内容失败: {e}")
            return {}
    
    def _determine_conversation_topic(self, participants: List[NPC2D]) -> str:
        """Determine conversation topic based on participants' states"""
        # 检查是否有紧急话题
        avg_hunger = sum(npc.attributes.hunger for npc in participants) / len(participants)
        if avg_hunger > 70:
            return "食物短缺"
        
        # 检查是否有危险
        for beast in self.world_state.beasts:
            if beast.is_aggressive():
                min_dist = min(
                    self.physics_engine.calculate_distance(npc.position, beast.position)
                    for npc in participants
                )
                if min_dist < 20:
                    return "附近危险"
        
        # 检查是否有人有工具
        has_equipment = any(npc.equipment for npc in participants)
        if has_equipment:
            return "工具制造与使用"
        
        # 检查资源
        has_resources = any(npc.inventory for npc in participants)
        if has_resources:
            return "资源采集经验"
        
        # 默认话题
        return random.choice(["生存技巧", "建造计划", "探索发现", "日常闲聊"])
    
    async def cleanup_npc_memories(self, npc: NPC2D):
        """清理NPC的记忆
        
        让AI评估记忆重要性并清理不重要的记忆
        """
        try:
            # 获取所有记忆
            all_memories = self.memory_service.get_all_memories(npc.id)
            
            if len(all_memories) < 30:
                return  # 记忆太少，不需要清理
            
            logger.info(f"🧠 {npc.name} 开始整理记忆（当前{len(all_memories)}条）")
            
            # 让AI评估记忆重要性
            evaluation = await self.ai_service.evaluate_memory_importance(npc, all_memories)
            
            if evaluation:
                # 执行清理
                await self.memory_service.cleanup_memories(npc.id, evaluation)
                
                # 同步更新NPC对象的memories（与memory_service保持一致）
                npc.memories = [m.get('description', '') for m in self.memory_service.get_all_memories(npc.id)]
                
                # 添加事件
                self.world_state.add_event(GameEvent(
                    id=f"memory_cleanup_{uuid.uuid4().hex[:8]}",
                    type="memory_cleanup",
                    description=f"🧹 {npc.name} 整理了记忆，清除了不重要的内容",
                    related_npcs=[npc.id],
                    importance="low"
                ))
            
        except Exception as e:
            logger.error(f"清理{npc.name}的记忆失败: {e}")
    
    async def process_social_interactions(self, current_time: float):
        """Process social interactions between NPCs"""
        if len(self.world_state.npcs) < 2:
            return
        
        # 🔥 使用物理引擎检测距离，只有足够近才能交流
        for i, npc1 in enumerate(self.world_state.npcs):
            # 只有idle状态的NPC才会交流
            if npc1.action_state != "idle":
                continue
            
            for npc2 in self.world_state.npcs[i+1:]:
                if npc2.action_state != "idle":
                    continue
                
                # 🔥 使用物理引擎的社交范围（5单位）
                distance = self.physics_engine.calculate_distance(
                    npc1.position, npc2.position
                )
                
                # 只有在社交范围内才能交流
                if distance <= self.physics_engine.SOCIAL_RANGE:
                    if random.random() < 0.05:  # 降低交流频率到5%
                        await self.create_social_interaction(npc1, npc2, current_time, distance)
                        return  # Only one interaction per update
    
    async def create_social_interaction(self, npc1: NPC2D, npc2: NPC2D, current_time: float, distance: float):
        """Create a social interaction between two NPCs"""
        # 🔥 根据NPC状态生成更真实的交流话题
        topics = []
        
        # 根据饥饿状态
        if npc1.attributes.hunger > 60 or npc2.attributes.hunger > 60:
            topics.append(("food", "讨论食物短缺的问题"))
        
        # 根据库存
        if npc1.inventory or npc2.inventory:
            topics.append(("resources", "交流资源采集经验"))
        
        # 根据附近的危险
        nearby_danger = False
        for beast in self.world_state.beasts:
            if beast.is_aggressive():
                dist = self.physics_engine.calculate_distance(
                    npc1.position, beast.position
                )
                if dist < 20:
                    nearby_danger = True
                    break
        
        if nearby_danger:
            topics.append(("danger", "警告彼此附近有危险的野兽"))
        
        # 默认话题
        topics.extend([
            ("cooperation", "商量合作建设"),
            ("exploration", "分享探索发现"),
            ("daily", "闲聊日常生活")
        ])
        
        # 随机选择话题
        topic, topic_desc = random.choice(topics)
        
        # 生成交流描述
        conversation_templates = {
            "food": f"💬 {npc1.name}和{npc2.name}讨论食物储备，决定多采集浆果",
            "resources": f"💬 {npc1.name}向{npc2.name}分享了附近资源点的位置",
            "danger": f"💬 {npc1.name}警告{npc2.name}附近有危险的野兽出没",
            "cooperation": f"💬 {npc1.name}和{npc2.name}商量一起建造避难所",
            "exploration": f"💬 {npc1.name}向{npc2.name}描述了远处看到的景象",
            "daily": f"💬 {npc1.name}和{npc2.name}交流生存心得"
        }
        
        description = conversation_templates.get(topic, f"💬 {npc1.name}和{npc2.name}进行了交流")
        
        # 🔥 记录交流到两个NPC的记忆中
        memory1 = f"与{npc2.name}交流，{topic_desc}"
        memory2 = f"与{npc1.name}交流，{topic_desc}"
        
        npc1.memories.append(memory1)
        npc2.memories.append(memory2)
        
        if len(npc1.memories) > 30:
            npc1.memories = npc1.memories[-20:]
        if len(npc2.memories) > 30:
            npc2.memories = npc2.memories[-20:]
        
        # Add event
        self.world_state.add_event(GameEvent(
            id=f"social_{uuid.uuid4().hex[:8]}",
            type="social_interaction",
            description=description,
            related_npcs=[npc1.id, npc2.id],
            importance="medium" if topic in ["danger"] else "low"
        ))
        
        logger.info(f"[社交] {description}（距离{distance:.1f}单位）")
        
        # Broadcast social interaction
        if self.broadcast_callback:
            await self.broadcast_callback('social_interaction', {
                'npc1_id': npc1.id,
                'npc1_name': npc1.name,
                'npc2_id': npc2.id,
                'npc2_name': npc2.name,
                'description': description,
                'topic': topic
            })
    
    async def broadcast_world_state(self):
        """Broadcast complete world state"""
        if self.broadcast_callback and self.world_state:
            world_dict = self.world_state.model_dump(mode='json')
            await self.broadcast_callback('world_state', world_dict)
    
    async def broadcast_world_update(self):
        """Broadcast world update"""
        if self.broadcast_callback and self.world_state:
            # Send a lighter update with proper JSON serialization
            update = {
                "time": self.world_state.time.model_dump(mode='json'),
                "weather": self.world_state.weather,  # 🌦️ 天气数据
                "npcs": [npc.model_dump(mode='json') for npc in self.world_state.npcs],
                "buildings": [building.model_dump(mode='json') for building in self.world_state.buildings],  # 🏗️ 建筑数据
                "resources": [resource.model_dump(mode='json') for resource in self.world_state.resources],  # 📍 资源点数据
                "beasts": [beast.model_dump(mode='json') for beast in self.world_state.beasts],
                "events": [e.model_dump(mode='json') for e in self.world_state.events[-10:]],  # Last 10 events
                "global_resources": self.world_state.global_resources
            }
            await self.broadcast_callback('world_update', update)
    
    def stop(self):
        """Stop the game loop"""
        self.is_running = False
        logger.info("Game loop stopped")

