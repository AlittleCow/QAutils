"""
Pen Types Module for Chan Algorithm

This module contains shared types, enums, and data structures used by
both pen processing and pen validation modules. This separation helps
avoid circular import issues.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from ..fractal import Fractal

if TYPE_CHECKING:
    from ..chan import Kbar
    from ..mergekbar import MergedKbar


class PenDirection(Enum):
    """Pen direction enumeration"""
    UP = 1      # Upward pen (向上笔)
    DOWN = -1   # Downward pen (向下笔)


class PenBreakType(Enum):
    """Pen breaking type enumeration"""
    NONE = 0           # No breaking
    PARTIAL_BREAK = 1  # Partial breaking
    FULL_BREAK = 2     # Full breaking


@dataclass
class ChanPen:
    """Chan Pen data structure"""
    start_fractal: Fractal
    end_fractal: Fractal
    direction: PenDirection
    high: float
    low: float
    length: float
    raw_kbars: List['Kbar']  # Raw kbars between fractals
    confirmed: bool = False
    break_type: PenBreakType = PenBreakType.NONE
    break_price: Optional[float] = None
    merged_kbars: Optional[List['MergedKbar']] = None  # Merged kbars in the pen
    # Validation result fields
    is_valid: bool = False
    failed_rules: Optional[List[str]] = None
    validation_details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Calculate pen properties after initialization"""
        if self.merged_kbars is None:
            self.merged_kbars = []
        if self.failed_rules is None:
            self.failed_rules = []
        if self.validation_details is None:
            self.validation_details = {}
        self._calculate_properties()
    
    def _calculate_properties(self):
        """Calculate pen high, low, and length"""
        if self.direction == PenDirection.UP:
            self.high = self.end_fractal.price
            self.low = self.start_fractal.price
            self.length = self.high - self.low
        else:
            self.high = self.start_fractal.price
            self.low = self.end_fractal.price
            self.length = self.high - self.low
    
    @property
    def start_price(self) -> float:
        """Get pen start price"""
        return self.start_fractal.price
    
    @property
    def end_price(self) -> float:
        """Get pen end price"""
        return self.end_fractal.price
    
    @property
    def start_time(self) -> str:
        """Get pen start time"""
        return self.start_fractal.timestamp
    
    @property
    def end_time(self) -> str:
        """Get pen end time"""  
        return self.end_fractal.timestamp
    
    @property
    def kbar_count(self) -> int:
        """Get number of raw kbars in this pen"""
        return len(self.raw_kbars)
    
    @property
    def merged_kbar_count(self) -> int:
        """Get number of merged kbars in this pen"""
        return len(self.merged_kbars) if self.merged_kbars else 0
    
    def __repr__(self) -> str:
        """String representation of the pen"""
        direction_str = "UP  " if self.direction == PenDirection.UP else "DOWN"
        valid_str = "VALID" if self.is_valid else "INVALID"
        return (f"ChanPen(direction={direction_str}, "
                f"start={self.start_time}, "
                f"end={self.end_time}, "
                f"raw_kbars={self.kbar_count:2d}, "
                f"merged_kbars={self.merged_kbar_count:2d}, "
                f"length={self.length:8.4f}, "
                f"status={valid_str})") 