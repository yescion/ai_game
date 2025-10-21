"""Base models"""
from pydantic import BaseModel


class Position2D(BaseModel):
    """2D position in the world"""
    x: float
    y: float
    
    def distance_to(self, other: 'Position2D') -> float:
        """Calculate distance to another position"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def __str__(self) -> str:
        return f"({self.x:.1f}, {self.y:.1f})"

