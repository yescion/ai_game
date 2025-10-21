"""World generator service"""
import random
import logging
from typing import List
import uuid

from app.models.world import WorldState2D, TimeSystem
from app.models.base import Position2D
from app.models.resources import ResourceNode
from app.models.beasts import Beast
from app.models.npc import NPC2D, NPCPersonality

logger = logging.getLogger(__name__)


class WorldGenerator:
    """Generate a procedural world"""
    
    # 🎭 性格模板
    PERSONALITY_TEMPLATES = {
        "勇敢型": NPCPersonality(
            personality_type="勇敢型",
            description="勇敢无畏，喜欢冒险和战斗，不怕危险",
            bravery=85,
            sociability=55,
            cautiousness=25,
            curiosity=70,
            cooperation=60,
            ambition=75
        ),
        "谨慎型": NPCPersonality(
            personality_type="谨慎型",
            description="小心谨慎，注重安全，避免风险",
            bravery=30,
            sociability=45,
            cautiousness=85,
            curiosity=40,
            cooperation=70,
            ambition=50
        ),
        "社交型": NPCPersonality(
            personality_type="社交型",
            description="善于交际，喜欢与人交流，团队意识强",
            bravery=50,
            sociability=90,
            cautiousness=50,
            curiosity=60,
            cooperation=85,
            ambition=55
        ),
        "探索型": NPCPersonality(
            personality_type="探索型",
            description="充满好奇心，喜欢探索未知，追求新发现",
            bravery=65,
            sociability=45,
            cautiousness=35,
            curiosity=95,
            cooperation=50,
            ambition=70
        ),
        "务实型": NPCPersonality(
            personality_type="务实型",
            description="脚踏实地，专注于生存和建设，注重实际",
            bravery=50,
            sociability=55,
            cautiousness=65,
            curiosity=45,
            cooperation=75,
            ambition=80
        ),
        "独立型": NPCPersonality(
            personality_type="独立型",
            description="独立自主，喜欢单独行动，自给自足",
            bravery=60,
            sociability=30,
            cautiousness=60,
            curiosity=55,
            cooperation=35,
            ambition=65
        )
    }
    
    def generate_world(self, width: int = 100, height: int = 100) -> WorldState2D:
        """Generate a complete world"""
        logger.info(f"Generating world {width}x{height}")
        
        world = WorldState2D(
            width=width,
            height=height,
            time=TimeSystem(day=1, hour=8, minute=0, season="spring"),
            weather="clear"
        )
        
        # Generate resources
        world.resources = self._generate_resources(width, height)
        logger.info(f"Generated {len(world.resources)} resource nodes")
        
        # Generate beasts
        world.beasts = self._generate_beasts(width, height)
        logger.info(f"Generated {len(world.beasts)} beasts")
        
        # Set spawn point (center of map)
        world.spawn_point = (width // 2, height // 2)
        
        return world
    
    def _generate_resources(self, width: int, height: int) -> List[ResourceNode]:
        """Generate resource nodes"""
        resources = []
        
        # Wood (trees) - 15 clusters
        for i in range(15):
            cluster_x = random.randint(5, width - 5)
            cluster_y = random.randint(5, height - 5)
            
            # Generate 3-5 trees per cluster
            for _ in range(random.randint(3, 5)):
                x = cluster_x + random.randint(-3, 3)
                y = cluster_y + random.randint(-3, 3)
                x = max(0, min(width - 1, x))
                y = max(0, min(height - 1, y))
                
                resources.append(ResourceNode(
                    id=f"wood_{uuid.uuid4().hex[:8]}",
                    type="wood",
                    position=Position2D(x=x, y=y),
                    quantity=random.randint(50, 150),
                    max_quantity=150,
                    regeneration_rate=2.0,
                    quality=random.randint(2, 5)
                ))
        
        # Stone - 10 clusters
        for i in range(10):
            cluster_x = random.randint(5, width - 5)
            cluster_y = random.randint(5, height - 5)
            
            for _ in range(random.randint(2, 4)):
                x = cluster_x + random.randint(-2, 2)
                y = cluster_y + random.randint(-2, 2)
                x = max(0, min(width - 1, x))
                y = max(0, min(height - 1, y))
                
                resources.append(ResourceNode(
                    id=f"stone_{uuid.uuid4().hex[:8]}",
                    type="stone",
                    position=Position2D(x=x, y=y),
                    quantity=random.randint(30, 100),
                    max_quantity=100,
                    regeneration_rate=1.0,
                    quality=random.randint(2, 4)
                ))
        
        # Berry bushes - 20 clusters
        for i in range(20):
            cluster_x = random.randint(5, width - 5)
            cluster_y = random.randint(5, height - 5)
            
            for _ in range(random.randint(2, 6)):
                x = cluster_x + random.randint(-4, 4)
                y = cluster_y + random.randint(-4, 4)
                x = max(0, min(width - 1, x))
                y = max(0, min(height - 1, y))
                
                resources.append(ResourceNode(
                    id=f"berry_{uuid.uuid4().hex[:8]}",
                    type="berry",
                    position=Position2D(x=x, y=y),
                    quantity=random.randint(20, 50),
                    max_quantity=50,
                    regeneration_rate=3.0,
                    quality=random.randint(1, 3)
                ))
        
        # Water sources - 5 locations
        for i in range(5):
            x = random.randint(10, width - 10)
            y = random.randint(10, height - 10)
            
            resources.append(ResourceNode(
                id=f"water_{uuid.uuid4().hex[:8]}",
                type="water",
                position=Position2D(x=x, y=y),
                quantity=9999,  # Infinite water
                max_quantity=9999,
                regeneration_rate=0,
                quality=5
            ))
        
        return resources
    
    def _generate_outer_position(self, width: int, height: int) -> tuple:
        """
        生成外围位置（远离中心）
        中心区域定义为：30-70, 30-70
        外围区域：边缘30单位内
        """
        center_x, center_y = width // 2, height // 2
        
        # 随机选择一个边缘区域
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        
        if edge == 'top':
            x = random.randint(10, width - 10)
            y = random.randint(5, 25)  # 上边缘
        elif edge == 'bottom':
            x = random.randint(10, width - 10)
            y = random.randint(height - 25, height - 5)  # 下边缘
        elif edge == 'left':
            x = random.randint(5, 25)  # 左边缘
            y = random.randint(10, height - 10)
        else:  # right
            x = random.randint(width - 25, width - 5)  # 右边缘
            y = random.randint(10, height - 10)
        
        return x, y
    
    def _generate_beasts(self, width: int, height: int) -> List[Beast]:
        """Generate beasts (分布在地图外围)"""
        beasts = []
        
        # 🔥 Wolves - 3 packs (狼群分布在外围)
        for i in range(3):
            pack_x, pack_y = self._generate_outer_position(width, height)
            pack_size = random.randint(2, 4)
            
            for j in range(pack_size):
                x = pack_x + random.randint(-5, 5)
                y = pack_y + random.randint(-5, 5)
                x = max(0, min(width - 1, x))
                y = max(0, min(height - 1, y))
                
                beasts.append(Beast(
                    id=f"wolf_{uuid.uuid4().hex[:8]}",
                    type="wolf",
                    position=Position2D(x=x, y=y),
                    health=50,
                    max_health=50,
                    aggression=0.7,
                    speed=3,
                    damage=8,  # 从15降低到8
                    sprite="wolf"
                ))
        
        # 🔥 Bears - 2 solitary (熊分布在外围)
        for i in range(2):
            x, y = self._generate_outer_position(width, height)
            
            beasts.append(Beast(
                id=f"bear_{uuid.uuid4().hex[:8]}",
                type="bear",
                position=Position2D(x=x, y=y),
                health=100,
                max_health=100,
                aggression=0.9,
                speed=2,
                damage=15,  # 从30降低到15
                sprite="bear"
            ))
        
        # 🔥 Rabbits - 10 scattered (兔子可以在中心区域，提供食物来源)
        for i in range(10):
            # 兔子分布在整个地图，但偏向中心
            if random.random() < 0.7:  # 70%在中心区域
                x = random.randint(30, 70)
                y = random.randint(30, 70)
            else:  # 30%在外围
                x, y = self._generate_outer_position(width, height)
            
            beasts.append(Beast(
                id=f"rabbit_{uuid.uuid4().hex[:8]}",
                type="rabbit",
                position=Position2D(x=x, y=y),
                health=10,
                max_health=10,
                aggression=0.0,
                speed=5,
                damage=0,
                sprite="rabbit"
            ))
        
        return beasts
    
    def generate_npc(self, name: str, position: Position2D = None, personality_type: str = None) -> NPC2D:
        """Generate a single NPC with personality
        
        Args:
            name: NPC名字
            position: 出生位置
            personality_type: 性格类型，如果为None则随机分配
        """
        if position is None:
            position = Position2D(x=50, y=50)
        
        # 分配性格
        if personality_type is None or personality_type not in self.PERSONALITY_TEMPLATES:
            # 随机选择一个性格
            personality_type = random.choice(list(self.PERSONALITY_TEMPLATES.keys()))
        
        personality = self.PERSONALITY_TEMPLATES[personality_type]
        
        logger.info(f"🎭 生成NPC {name}，性格: {personality_type}")
        
        return NPC2D(
            id=f"npc_{uuid.uuid4().hex[:8]}",
            name=name,
            position=position,
            personality=personality
        )

