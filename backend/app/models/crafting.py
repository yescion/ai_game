"""Crafting system models and recipes"""
from typing import Dict, List
from pydantic import BaseModel, Field


class CraftingRecipe(BaseModel):
    """Recipe for crafting an item"""
    item_name: str
    required_materials: Dict[str, int]  # material -> amount
    crafting_time: float = 10.0  # seconds
    skill_required: str = "crafting"
    skill_level: float = 0.0
    tool_type: str = "tool"  # tool, weapon, building_material
    durability: int = 100  # How long the tool lasts
    description: str = ""


# 🔧 工具配方库
CRAFTING_RECIPES = {
    "stone_axe": CraftingRecipe(
        item_name="stone_axe",
        required_materials={"stone": 3, "wood": 2},
        crafting_time=15.0,
        skill_required="crafting",
        skill_level=0,
        tool_type="tool",
        durability=100,
        description="石斧 - 提高采集木材效率50%"
    ),
    "stone_pickaxe": CraftingRecipe(
        item_name="stone_pickaxe",
        required_materials={"stone": 4, "wood": 2},
        crafting_time=15.0,
        skill_required="crafting",
        skill_level=5,
        tool_type="tool",
        durability=100,
        description="石镐 - 提高采集石头效率50%"
    ),
    "spear": CraftingRecipe(
        item_name="spear",
        required_materials={"stone": 2, "wood": 3},
        crafting_time=12.0,
        skill_required="crafting",
        skill_level=0,
        tool_type="weapon",
        durability=80,
        description="长矛 - 增加战斗伤害30%"
    ),
    "basket": CraftingRecipe(
        item_name="basket",
        required_materials={"wood": 5},
        crafting_time=10.0,
        skill_required="crafting",
        skill_level=0,
        tool_type="tool",
        durability=60,
        description="篮子 - 增加采集浆果效率30%"
    ),
    "water_container": CraftingRecipe(
        item_name="water_container",
        required_materials={"wood": 3},
        crafting_time=8.0,
        skill_required="crafting",
        skill_level=0,
        tool_type="tool",
        durability=50,
        description="水容器 - 可以储存更多水"
    ),
}


def get_recipe(item_name: str) -> CraftingRecipe:
    """Get crafting recipe by item name"""
    return CRAFTING_RECIPES.get(item_name)


def get_all_craftable_items() -> List[str]:
    """Get list of all craftable items"""
    return list(CRAFTING_RECIPES.keys())


def can_craft(item_name: str, inventory: Dict[str, int], skill_level: float = 0) -> tuple[bool, str]:
    """Check if NPC can craft an item"""
    recipe = get_recipe(item_name)
    if not recipe:
        return False, f"未知物品: {item_name}"
    
    # Check skill level
    if skill_level < recipe.skill_level:
        return False, f"技能等级不足: 需要{recipe.skill_level}，当前{skill_level}"
    
    # Check materials
    for material, amount in recipe.required_materials.items():
        if inventory.get(material, 0) < amount:
            return False, f"材料不足: 需要{amount}个{material}，当前{inventory.get(material, 0)}个"
    
    return True, "可以制造"


def consume_materials(inventory: Dict[str, int], recipe: CraftingRecipe) -> Dict[str, int]:
    """Consume materials from inventory and return updated inventory"""
    new_inventory = inventory.copy()
    for material, amount in recipe.required_materials.items():
        new_inventory[material] = new_inventory.get(material, 0) - amount
        if new_inventory[material] <= 0:
            del new_inventory[material]
    return new_inventory

