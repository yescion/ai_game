"""
游戏物理引擎
负责距离计算、范围检测、视野系统、移动处理等物理相关功能
"""
import math
import logging
from typing import List, Optional, Tuple
from app.models.base import Position2D
from app.models.npc import NPC2D
from app.models.resources import ResourceNode
from app.models.beasts import Beast

logger = logging.getLogger(__name__)


class PhysicsEngine:
    """游戏物理引擎"""
    
    # 物理参数
    VISION_RANGE = 15.0  # NPC视野范围：15单位
    GATHER_RANGE = 2.0   # 采集范围：2单位（必须在资源点附近）
    ATTACK_RANGE = 2.5   # 攻击范围：2.5单位（确保不会重叠碰撞，避免抖动）
    SOCIAL_RANGE = 5.0   # 社交范围：5单位
    
    # 实体半径（逻辑单位）
    ENTITY_RADIUS = 1.0  # NPC和野兽的逻辑半径：1单位
    # 说明：两个实体的半径之和为2单位，攻击距离2.5单位确保不需要重叠
    
    @staticmethod
    def calculate_distance(pos1: Position2D, pos2: Position2D) -> float:
        """
        计算两点间的欧几里得距离
        
        Args:
            pos1: 第一个位置
            pos2: 第二个位置
            
        Returns:
            距离值
        """
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        return math.sqrt(dx * dx + dy * dy)
    
    @staticmethod
    def is_in_range(pos1: Position2D, pos2: Position2D, range_value: float) -> bool:
        """
        检测两点是否在指定范围内
        
        Args:
            pos1: 第一个位置
            pos2: 第二个位置
            range_value: 范围阈值
            
        Returns:
            是否在范围内
        """
        distance = PhysicsEngine.calculate_distance(pos1, pos2)
        return distance <= range_value
    
    @staticmethod
    def can_gather(npc_pos: Position2D, resource_pos: Position2D) -> bool:
        """
        检查NPC是否可以采集资源（距离检查）
        
        Args:
            npc_pos: NPC位置
            resource_pos: 资源位置
            
        Returns:
            是否可以采集
        """
        return PhysicsEngine.is_in_range(npc_pos, resource_pos, PhysicsEngine.GATHER_RANGE)
    
    @staticmethod
    def can_attack(attacker_pos: Position2D, target_pos: Position2D) -> bool:
        """
        检查是否可以攻击（距离检查）
        
        Args:
            attacker_pos: 攻击者位置
            target_pos: 目标位置
            
        Returns:
            是否可以攻击
        """
        return PhysicsEngine.is_in_range(attacker_pos, target_pos, PhysicsEngine.ATTACK_RANGE)
    
    @staticmethod
    def can_see(from_pos: Position2D, to_pos: Position2D, vision_range: float = None) -> bool:
        """
        检查是否在视野内
        
        Args:
            from_pos: 观察者位置
            to_pos: 目标位置
            vision_range: 视野范围（默认使用VISION_RANGE）
            
        Returns:
            是否可见
        """
        if vision_range is None:
            vision_range = PhysicsEngine.VISION_RANGE
        return PhysicsEngine.is_in_range(from_pos, to_pos, vision_range)


class VisionSystem:
    """视野系统"""
    
    def __init__(self, physics_engine: PhysicsEngine):
        self.physics = physics_engine
    
    def get_visible_resources(
        self,
        npc: NPC2D,
        all_resources: List[ResourceNode]
    ) -> List[ResourceNode]:
        """
        获取NPC可见的资源
        
        Args:
            npc: NPC对象
            all_resources: 所有资源列表
            
        Returns:
            可见的资源列表
        """
        visible = []
        for resource in all_resources:
            # 跳过已枯竭的资源
            if hasattr(resource, 'is_depleted') and resource.is_depleted:
                continue
            
            if self.physics.can_see(npc.position, resource.position):
                visible.append(resource)
        
        return visible
    
    def get_visible_npcs(
        self,
        npc: NPC2D,
        all_npcs: List[NPC2D]
    ) -> List[NPC2D]:
        """
        获取NPC可见的其他NPC
        
        Args:
            npc: 当前NPC
            all_npcs: 所有NPC列表
            
        Returns:
            可见的其他NPC列表
        """
        visible = []
        for other in all_npcs:
            if other.id != npc.id and self.physics.can_see(npc.position, other.position):
                visible.append(other)
        
        return visible
    
    def get_visible_beasts(
        self,
        npc: NPC2D,
        all_beasts: List[Beast]
    ) -> List[Beast]:
        """
        获取NPC可见的野兽
        
        Args:
            npc: NPC对象
            all_beasts: 所有野兽列表
            
        Returns:
            可见的野兽列表
        """
        visible = []
        for beast in all_beasts:
            if self.physics.can_see(npc.position, beast.position):
                visible.append(beast)
        
        return visible
    
    def find_nearest_resource(
        self,
        npc: NPC2D,
        resources: List[ResourceNode],
        resource_type: Optional[str] = None
    ) -> Optional[Tuple[ResourceNode, float]]:
        """
        查找最近的资源
        
        Args:
            npc: NPC对象
            resources: 可见的资源列表
            resource_type: 资源类型过滤（可选）
            
        Returns:
            (最近的资源, 距离) 或 None
        """
        if not resources:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for resource in resources:
            # 类型过滤
            if resource_type and resource.type != resource_type:
                continue
            
            # 跳过已枯竭的资源
            if hasattr(resource, 'is_depleted') and resource.is_depleted:
                continue
            
            distance = self.physics.calculate_distance(npc.position, resource.position)
            if distance < min_distance:
                min_distance = distance
                nearest = resource
        
        return (nearest, min_distance) if nearest else None
    
    def find_nearest_threat(
        self,
        npc: NPC2D,
        beasts: List[Beast]
    ) -> Optional[Tuple[Beast, float]]:
        """
        查找最近的威胁（攻击性野兽）
        
        Args:
            npc: NPC对象
            beasts: 可见的野兽列表
            
        Returns:
            (最近的威胁, 距离) 或 None
        """
        if not beasts:
            return None
        
        nearest_threat = None
        min_distance = float('inf')
        
        for beast in beasts:
            # 只关注攻击性野兽
            if not beast.is_aggressive:
                continue
            
            distance = self.physics.calculate_distance(npc.position, beast.position)
            if distance < min_distance:
                min_distance = distance
                nearest_threat = beast
        
        return (nearest_threat, min_distance) if nearest_threat else None


class MovementSystem:
    """移动系统"""
    
    def __init__(self, physics_engine: PhysicsEngine):
        self.physics = physics_engine
    
    # 移动速度配置
    BASE_SPEED = 2.0  # 基础速度：2单位/秒
    
    def move_towards_target(
        self,
        entity_pos: Position2D,
        target_pos: Position2D,
        speed: float,
        delta_time: float
    ) -> Tuple[bool, Position2D]:
        """
        向目标移动
        
        Args:
            entity_pos: 实体当前位置
            target_pos: 目标位置
            speed: 移动速度（单位/秒）
            delta_time: 时间间隔（秒）
            
        Returns:
            (是否到达, 新位置)
        """
        # 计算方向
        dx = target_pos.x - entity_pos.x
        dy = target_pos.y - entity_pos.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # 已到达
        if distance < 0.1:
            return (True, entity_pos)
        
        # 归一化方向
        dx /= distance
        dy /= distance
        
        # 计算本帧移动距离
        move_distance = speed * delta_time
        
        # 如果本帧可以到达，直接到达
        if move_distance >= distance:
            return (True, Position2D(x=target_pos.x, y=target_pos.y))
        
        # 否则向目标移动
        new_x = entity_pos.x + dx * move_distance
        new_y = entity_pos.y + dy * move_distance
        
        # 边界检查
        new_x = max(0, min(100, new_x))
        new_y = max(0, min(100, new_y))
        
        return (False, Position2D(x=new_x, y=new_y))
    
    def get_npc_speed(self, npc: NPC2D) -> float:
        """
        获取NPC的移动速度（考虑体力等因素）
        
        Args:
            npc: NPC对象
            
        Returns:
            移动速度
        """
        base_speed = self.BASE_SPEED
        speed_multiplier = 1.0
        
        # 体力影响速度
        if npc.attributes.stamina < 30:
            speed_multiplier = 0.7  # 体力低，速度减30%
        elif npc.attributes.stamina > 70:
            speed_multiplier = 1.2  # 体力充足，速度加20%
        
        # 健康影响速度
        if npc.attributes.health < 50:
            speed_multiplier *= 0.8  # 受伤，速度减20%
        
        return base_speed * speed_multiplier
    
    def calculate_move_duration(
        self,
        from_pos: Position2D,
        to_pos: Position2D,
        speed: float
    ) -> float:
        """
        计算移动所需时间
        
        Args:
            from_pos: 起点
            to_pos: 终点
            speed: 移动速度
            
        Returns:
            所需时间（秒）
        """
        distance = self.physics.calculate_distance(from_pos, to_pos)
        if speed <= 0:
            return float('inf')
        return distance / speed


class SpatialGrid:
    """
    空间分区系统（用于性能优化）
    将世界划分为网格，加速空间查询
    """
    
    def __init__(self, width: int = 100, height: int = 100, cell_size: int = 10):
        """
        初始化空间分区
        
        Args:
            width: 世界宽度
            height: 世界高度
            cell_size: 格子大小
        """
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.physics = PhysicsEngine()
    
    def get_cell(self, pos: Position2D) -> Tuple[int, int]:
        """获取位置所在的格子坐标"""
        cell_x = int(pos.x // self.cell_size)
        cell_y = int(pos.y // self.cell_size)
        return (cell_x, cell_y)
    
    def get_nearby_cells(self, pos: Position2D, range_value: float) -> List[Tuple[int, int]]:
        """
        获取范围内的所有格子
        
        Args:
            pos: 中心位置
            range_value: 范围
            
        Returns:
            格子坐标列表
        """
        cell_x, cell_y = self.get_cell(pos)
        cell_range = int(math.ceil(range_value / self.cell_size))
        
        cells = []
        for dx in range(-cell_range, cell_range + 1):
            for dy in range(-cell_range, cell_range + 1):
                cells.append((cell_x + dx, cell_y + dy))
        
        return cells


# 导出
__all__ = [
    'PhysicsEngine',
    'VisionSystem',
    'MovementSystem',
    'SpatialGrid'
]

