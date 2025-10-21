"""Prompt templates for NPC decision making"""
from typing import List, Dict
from app.models.npc import NPC2D
from app.models.world import WorldState2D
from app.models.crafting import CRAFTING_RECIPES


def format_skills(skills: Dict[str, float]) -> str:
    """Format skills for display"""
    return "\n".join([f"  - {skill}: {level:.0f}" for skill, level in skills.items() if level > 0])


def format_inventory(inventory: Dict[str, int]) -> str:
    """Format inventory for display"""
    if not inventory:
        return "  空"
    return "\n".join([f"  - {item}: {count}" for item, count in inventory.items()])


def format_equipment(equipment: Dict[str, Dict]) -> str:
    """Format equipment/tools for display"""
    if not equipment:
        return "  无"
    formatted = []
    for tool_name, tool_data in equipment.items():
        durability = tool_data.get("durability", 100)
        description = tool_data.get("description", "")
        formatted.append(f"  - {tool_name} (耐久: {durability}%) - {description}")
    return "\n".join(formatted)


def format_nearby_resources(npc: NPC2D, world_state: WorldState2D) -> str:
    """Format nearby resources"""
    nearby = []
    for resource in world_state.resources:
        distance = npc.position.distance_to(resource.position)
        if distance < 20:  # Within 20 units
            nearby.append(f"{resource.type} (距离: {distance:.1f})")
    
    return ", ".join(nearby) if nearby else "无"


def format_nearby_npcs(npc: NPC2D, world_state: WorldState2D) -> str:
    """Format nearby NPCs"""
    nearby = []
    for other_npc in world_state.npcs:
        if other_npc.id == npc.id:
            continue
        distance = npc.position.distance_to(other_npc.position)
        if distance < 15:  # Within 15 units
            nearby.append(f"{other_npc.name} (距离: {distance:.1f})")
    
    return ", ".join(nearby) if nearby else "无"


def format_nearby_buildings(npc: NPC2D, world_state: WorldState2D) -> str:
    """Format nearby buildings"""
    nearby = []
    for building in world_state.buildings:
        distance = npc.position.distance_to(building.position)
        if distance < 25:  # Within 25 units
            if building.is_complete:
                status = "✅已完成"
            else:
                # 🔧 显示详细的建造进度
                progress_pct = int(building.construction_progress * 100)
                builder_count = len(building.builders)
                
                if builder_count > 0:
                    status = f"🔨建造中({progress_pct}%, {builder_count}人正在建造)"
                else:
                    status = f"⏸️暂停建造({progress_pct}%, ⚠️需要继续建造!)"
                    
                # 标记是否需要合作
                if building.requires_cooperation and builder_count < 2:
                    status += " [需要合作]"
            
            nearby.append(f"{building.name} ({status}, 距离: {distance:.1f})")
    
    return ", ".join(nearby) if nearby else "无"


def format_nearby_beasts(npc: NPC2D, world_state: WorldState2D) -> str:
    """Format nearby beasts"""
    nearby = []
    for beast in world_state.beasts:
        distance = npc.position.distance_to(beast.position)
        if distance < 20:  # Within 20 units
            threat = "⚠️危险" if beast.is_aggressive() else "温和"
            nearby.append(f"{beast.type} ({threat}, 距离: {distance:.1f})")
    
    return ", ".join(nearby) if nearby else "无"


def format_memories(memories: List[Dict]) -> str:
    """Format memories"""
    if not memories:
        return "  无相关记忆"
    
    formatted = []
    
    # 🔥 优先显示上帝指令的记忆（重要性高）
    user_memories = [m for m in memories if m.get('type') == 'user_memory']
    other_memories = [m for m in memories if m.get('type') != 'user_memory']
    
    # 显示上帝指令的记忆（最多3条）
    if user_memories:
        formatted.append("【⭐ 重要记忆】")
        for memory in user_memories[-3:]:
            formatted.append(f"  • {memory.get('description', '未知记忆')}")
        formatted.append("")
    
    # 显示其他记忆（最多5条）
    if other_memories:
        if user_memories:
            formatted.append("【其他记忆】")
        for i, memory in enumerate(other_memories[-5:], 1):
            formatted.append(f"  {i}. {memory.get('description', '未知记忆')}")
    
    return "\n".join(formatted) if formatted else "  无相关记忆"


def format_action_log(action_log: List[str]) -> str:
    """Format recent action log"""
    if not action_log:
        return "无"
    
    # 获取最近3条，并格式化
    recent = action_log[-3:]
    return "\n  ".join(recent)


def generate_npc_decision_prompt(
    npc: NPC2D,
    world_state: WorldState2D,
    memories: List[Dict]
) -> str:
    """Generate the complete decision prompt for an NPC"""
    
    # 🔥 将hunger转换为satiety（饱食度），语义更清晰
    # hunger: 0=不饿, 100=很饿
    # satiety: 0=很饿, 100=很饱
    satiety = 100 - npc.attributes.hunger
    
    # Health warning
    health_warning = ""
    if npc.attributes.health < 30:
        health_warning = " ⚠️ 危险！"
    
    # Satiety warning (饱食度低时警告)
    satiety_warning = ""
    if satiety < 20:  # 相当于 hunger > 80
        satiety_warning = " 🍖 非常饥饿！"
    elif satiety < 30:  # 相当于 hunger > 70
        satiety_warning = " 🍖 有点饿"
    
    # Time of day
    time_warning = ""
    if world_state.time.is_night():
        time_warning = " 🌙 夜晚很危险"
    
    # 🎭 生成性格描述
    personality_desc = f"""
【你的性格】
- 类型: {npc.personality.personality_type}
- 特点: {npc.personality.description}
- 勇敢度: {npc.personality.bravery}/100 {'(你很勇敢，不怕危险)' if npc.personality.bravery >= 70 else '(你比较谨慎，会避开危险)' if npc.personality.bravery <= 40 else ''}
- 社交性: {npc.personality.sociability}/100 {'(你喜欢与人交流)' if npc.personality.sociability >= 70 else '(你更喜欢独处)' if npc.personality.sociability <= 40 else ''}
- 好奇心: {npc.personality.curiosity}/100 {'(你充满探索欲)' if npc.personality.curiosity >= 70 else ''}
- 合作性: {npc.personality.cooperation}/100 {'(你喜欢团队协作)' if npc.personality.cooperation >= 70 else '(你偏好独立行动)' if npc.personality.cooperation <= 40 else ''}
"""
    
    prompt = f"""
你是 {npc.name}，一个在原始平原上求生的NPC。你有自己的想法和个性。

{personality_desc}

【当前状态】
- 位置: ({npc.position.x:.1f}, {npc.position.y:.1f})
- 健康: {npc.attributes.health:.0f}/100{health_warning}
- 饱食度: {satiety:.0f}/100{satiety_warning}
- 体力: {npc.attributes.stamina:.0f}/100
- 时间: {world_state.time}{time_warning}
- 天气: {world_state.weather}

【你的技能】
{format_skills(npc.skills) or "  还未掌握任何技能"}

【背包物品】
{format_inventory(npc.inventory)}

【装备/工具】
{format_equipment(npc.equipment)}

【当前计划】
- 待办事项: {npc.current_todo or "无"}
- 最近行动:
  {format_action_log(npc.action_log)}

【⚠️ 上次行动结果】
{npc.last_action_result or "无（首次决策）"}

【视野范围内】
- 资源: {format_nearby_resources(npc, world_state)}
- 其他NPC: {format_nearby_npcs(npc, world_state)}
- 建筑: {format_nearby_buildings(npc, world_state)}
- 野兽: {format_nearby_beasts(npc, world_state)}

【相关记忆】
{format_memories(memories)}
⚠️ 【重要】如果【⭐ 重要记忆】中有上帝的指示，这是最高优先级的任务！必须尽快执行！

【可用行动】
1. move - 移动到目标位置
2. flee - 🏃 快速逃跑（远离危险，速度更快）
3. gather - 采集资源 (木材/石头/浆果/水)
4. hunt - 狩猎野兽
5. craft - 🔧 制作工具/物品
   【制造配方-所需材料】：
   • stone_axe(石斧) = 需要3个stone + 2个wood
   • stone_pickaxe(石镐) = 需要4个stone + 2个wood  
   • spear(长矛) = 需要2个stone + 3个wood
   • basket(篮子) = 需要5个wood
   • water_container(水容器) = 需要3个wood
   ⚠️ 必须检查【背包物品】确认有足够材料！没有材料就不能craft！
   ⚠️⚠️ 【重要】先看【装备/工具】！！！
   - 如果已经有stone_axe，就不要再craft stone_axe！
   - 如果已经有stone_pickaxe，就不要再craft stone_pickaxe！
   - 如果已经有spear，就不要再craft spear！
   - 已有的工具不需要重复制造！浪费材料！
6. share - 🎁 分享物品给附近的NPC（食物/工具/资源）
7. build - 🏗️ 建造建筑（目标是建立城镇！）
   【建造配方-所需材料】：
   • campfire(篝火) = 需要5个wood [单人可建] - 提供温暖和烹饪能力
   • lean_to(简易棚屋) = 需要10个wood + 5个stone [单人可建] - 庇护所，rest时额外恢复50%健康
   • wooden_hut(木屋) = 需要30个wood + 15个stone [需要合作] - 高级住所，rest时额外恢复100%健康+50%体力
   • storage_shed(储物棚) = 需要20个wood [单人可建] - 存储资源，团队共享
   • workshop(工作台) = 需要15个wood + 10个stone [需要合作] - 解锁高级制作配方
   ⚠️ 【重要】先看【建筑】！如果附近已有相同建筑，就不要重复建造！
   ⚠️ 【合作建造】标记"需要合作"的建筑，单人建造效率很低，多人合作速度更快！
   ⚠️ 检查【背包物品】确认有足够材料！没有材料先去采集！
8. eat - 进食 (恢复饱食度)
9. rest - 休息 (恢复体力和健康，在庇护所附近休息效果更好！)
10. talk - 与其他NPC交流（可以商量合作建造）
11. explore - 探索未知区域
12. defend - 防御/战斗

【集体目标】
整个社群的目标是：在这片原始平原上生存并建立城镇。

【决策要求】
根据当前状况做出合理决策，用第一人称思考：
- ⭐ 【最高优先级】查看【⭐ 重要记忆】！如果有上帝的指示（如"建立庇护所"），这是最重要的任务！
- 🎯 【关键】先看【上次行动结果】！如果上次失败了，必须调整策略！
- 🎯 如果上次craft/build失败（材料不足），这次必须先gather采集材料，不要再craft/build！
- 🎯 如果上次已经成功craft了某工具，不要重复制造！
- ⚠️ 生存第一！健康<30必须立即休息，饱食度<20必须立即进食
- 健康<50或饱食度<30时，优先满足生存需求
- ⚔️ 【战斗策略】如果有武器（spear或stone）且健康>50，遇到野兽时可以选择：
  * 有spear（长矛）：勇敢hunt狩猎或defend战斗！长矛威力强大（+40伤害）
  * 有stone（石头）：可以尝试hunt弱小野兽（兔子/鹿）或defend防御（+8伤害）
  * 多人在场：团队defend战斗更安全！
  * 无武器或健康<50：使用flee逃跑
- 🏃 遇到危险野兽（熊/狼）且无武器或健康<50时，使用flee行动快速逃跑！
- 🔧 想要craft制造工具？先看【背包物品】！必须有足够材料才能craft！
- 🔧 查看【装备/工具】！如果已经有某工具，不要重复制造
- 🔧 材料不足时，先去gather采集，不要盲目craft
- 🏗️ 【建造城镇】生存需求满足后，优先考虑建造建筑！
- 🏗️ 想要build建造？先看【背包物品】！必须有足够材料才能build！
- 🏗️ 【重要】查看【建筑】列表！如果已经有"✅已完成"的同类型建筑，绝对不要重复建造！
- 🏗️ 【重要】如果看到某建筑显示"⏸️暂停建造(X%, ⚠️需要继续建造!)"，优先继续建造它！不要让建筑半途而废！
- 🏗️ 【持续建造】如果你正在build建造某建筑，除非生存紧急（健康<30或饱食度<20），否则坚持建造直到完成！
- 🏗️ 建造顺序建议：篝火（温暖+烹饪）→ 简易棚屋（庇护）→ 储物棚（共享资源）→ 木屋/工作台（需要合作）
- 🏗️ 如果附近有"🔨建造中"的建筑，可以加入帮忙（多人合作速度更快！特别是标记"[需要合作]"的建筑）
- 🎁 看到附近同伴缺少工具或食物时，可以使用share行动分享物品
- 🤝 团队协作精神！如果记忆中有同伴被攻击，且自己状态良好（健康>60），考虑去帮助
- 🤝 看到附近有多个同伴时，可以一起对抗野兽（defend行动）
- 🤝 与附近的NPC分享资源信息和危险警告
- 🤝 可以talk与同伴商量合作建造大型建筑（木屋、工作台需要合作）
- 📋 查看【当前计划】避免重复同样的行动！如果刚完成talk，就做点别的
- 📋 查看【相关记忆】！如果记忆里有"材料不足"，说明你需要先采集材料！

🎭 根据你的性格做决策：
- 勇敢型(勇敢度高)：更愿意hunt狩猎、defend战斗、explore探索危险区域
- 谨慎型(谨慎度高)：优先gather采集安全资源、避免冒险、多准备后备计划
- 社交型(社交性高)：多使用talk交流、share分享、参与团队活动
- 探索型(好奇心高)：多explore探索、尝试新区域、发现新资源
- 务实型(进取心高)：专注craft制造、build建造、提升技能
- 独立型(合作性低)：独自gather采集、craft制造，少依赖团队

- 基本需求满足后，为集体贡献（采集、建造、探索）

以JSON格式回复:
{{
    "action": "行动类型",
    "target": "目标ID或null",
    "reasoning": "简短描述你的想法，10-20字。例如：'肚子饿了去采浆果'、'继续建造庇护所'",
    "duration": 5到15（秒），
    "priority": "high/medium/low"
}}
"""
    
    return prompt

