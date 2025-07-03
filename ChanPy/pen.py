"""
Pen Processing Module for Chan Algorithm

This module handles the formation and validation of pens (笔) from fractals.
A pen connects two fractals of different types and must satisfy specific
validation criteria based on the raw kbars between the fractals.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from .fractal import Fractal, FractalType
from .mergekbar import MergedKbar

if TYPE_CHECKING:
    from .chan import Kbar


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
    merged_kbars: Optional[List[MergedKbar]] = None  # Merged kbars in the pen
    
    def __post_init__(self):
        """Calculate pen properties after initialization"""
        if self.merged_kbars is None:
            self.merged_kbars = []
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
        return (f"ChanPen(direction={direction_str}, "
                f"start={self.start_time}, "
                f"end={self.end_time}, "
                f"raw_kbars={self.kbar_count:2d}, "
                f"merged_kbars={self.merged_kbar_count:2d}, "
                f"length={self.length:8.4f})")


class PenProcessor:
    """
    Pen Processor Class
    
    Processes fractals to form valid pens according to Chan algorithm rules.
    Validates pens against raw kbar data and handles pen breaking analysis.
    """
    
    def __init__(self, min_pen_length: float = 0.0, min_kbar_count: int = 5):
        """
        Initialize Pen Processor
        
        Args:
            min_pen_length: Minimum pen length for validation
            min_kbar_count: Minimum number of kbars for a valid pen
        """
        self.logger = logging.getLogger(f"{__name__}")
        self.min_pen_length = min_pen_length
        self.min_kbar_count = min_kbar_count
        self.pens: List[ChanPen] = []
        self.raw_kbars: List['Kbar'] = []
    
    def set_raw_kbars(self, kbars: List['Kbar']):
        """
        Set the raw kbar data for pen validation
        
        Args:
            kbars: List of raw kbars in chronological order
        """
        self.raw_kbars = kbars
        self.logger.debug(f"Set {len(kbars)} raw kbars for pen validation")
    
    def validate_pen_with_raw_kbars(self, start_fractal: Fractal, end_fractal: Fractal) -> bool:
        """
        Validate a potential pen using raw kbar data
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            
        Returns:
            True if pen is valid according to raw kbar analysis
        """
        if not self.raw_kbars:
            self.logger.warning("No raw kbars available for pen validation")
            return True  # Allow pen if no raw data available
        
        # Find raw kbars between the two fractals
        pen_kbars = self._get_kbars_between_fractals(start_fractal, end_fractal)
        
        if len(pen_kbars) < self.min_kbar_count:
            return False
        
        # Validate pen direction consistency
        if start_fractal.fractal_type == FractalType.BOTTOM:
            # Should be an upward pen
            return self._validate_upward_pen(start_fractal, end_fractal, pen_kbars)
        else:
            # Should be a downward pen
            return self._validate_downward_pen(start_fractal, end_fractal, pen_kbars)
    
    def _get_kbars_between_fractals(self, start_fractal: Fractal, end_fractal: Fractal) -> List['Kbar']:
        """
        Get raw kbars between two fractals
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            
        Returns:
            List of kbars between the fractals
        """
        # This is a simplified implementation
        # In practice, you would need to match fractals to kbar timestamps
        start_time = start_fractal.timestamp
        end_time = end_fractal.timestamp
        
        # Find kbars within the time range
        pen_kbars = []
        for kbar in self.raw_kbars:
            if start_time <= kbar.timestamp <= end_time:
                pen_kbars.append(kbar)
        
        return pen_kbars
    
    def _validate_upward_pen(self, start_fractal: Fractal, end_fractal: Fractal, 
                           pen_kbars: List['Kbar']) -> bool:
        """
        Validate an upward pen against raw kbars
        
        Args:
            start_fractal: Bottom fractal (start)
            end_fractal: Top fractal (end)
            pen_kbars: Raw kbars in the pen
            
        Returns:
            True if pen is valid
        """
        if not pen_kbars:
            return False
        
        # Check that the pen maintains upward trend
        # No kbar low should break below the start fractal low
        start_low = start_fractal.price
        
        for kbar in pen_kbars:
            if kbar.low < start_low:
                return False
        
        # Check that we reach the end fractal high
        max_high = max(kbar.high for kbar in pen_kbars)
        return abs(max_high - end_fractal.price) < 0.001  # Allow small tolerance
    
    def _validate_downward_pen(self, start_fractal: Fractal, end_fractal: Fractal,
                             pen_kbars: List['Kbar']) -> bool:
        """
        Validate a downward pen against raw kbars
        
        Args:
            start_fractal: Top fractal (start)
            end_fractal: Bottom fractal (end)
            pen_kbars: Raw kbars in the pen
            
        Returns:
            True if pen is valid
        """
        if not pen_kbars:
            return False
        
        # Check that the pen maintains downward trend
        # No kbar high should break above the start fractal high
        start_high = start_fractal.price
        
        for kbar in pen_kbars:
            if kbar.high > start_high:
                return False
        
        # Check that we reach the end fractal low
        min_low = min(kbar.low for kbar in pen_kbars)
        return abs(min_low - end_fractal.price) < 0.001  # Allow small tolerance
    
    def create_pen(self, start_fractal: Fractal, end_fractal: Fractal) -> Optional[ChanPen]:
        """
        Create a pen from two fractals
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            
        Returns:
            ChanPen object if valid, None otherwise
        """
        # Validate fractal types are different
        if start_fractal.fractal_type == end_fractal.fractal_type:
            return None
        
        # Validate with raw kbars
        if not self.validate_pen_with_raw_kbars(start_fractal, end_fractal):
            return None
        
        # Determine pen direction
        if start_fractal.fractal_type == FractalType.BOTTOM:
            direction = PenDirection.UP
        else:
            direction = PenDirection.DOWN
        
        # Get raw kbars for this pen
        pen_kbars = self._get_kbars_between_fractals(start_fractal, end_fractal)
        
        # Calculate pen length
        length = abs(end_fractal.price - start_fractal.price)
        
        # Check minimum length requirement
        if length < self.min_pen_length:
            return None
        
        pen = ChanPen(
            start_fractal=start_fractal,
            end_fractal=end_fractal,
            direction=direction,
            high=0.0,  # Will be calculated in __post_init__
            low=0.0,   # Will be calculated in __post_init__
            length=length,
            raw_kbars=pen_kbars,
            confirmed=True,
            merged_kbars=[]  # Initialize as empty list - to be populated later
        )
        
        return pen
    
    def process_fractals(self, fractals: List[Fractal]) -> List[ChanPen]:
        """
        Process a list of fractals to create pens
        
        Args:
            fractals: List of fractals in chronological order
            
        Returns:
            List of valid pens
        """
        if len(fractals) < 2:
            return []
        
        pens = []
        
        for i in range(len(fractals) - 1):
            start_fractal = fractals[i]
            end_fractal = fractals[i + 1]
            
            pen = self.create_pen(start_fractal, end_fractal)
            if pen:
                pens.append(pen)
                self.logger.debug(f"Pen: {pen}")
        
        self.pens = pens
        self.logger.info(f"Created {len(pens)} valid pens from {len(fractals)} fractals")
        
        return pens
    
    def analyze_pen_breaking(self, pen: ChanPen, current_price: float) -> PenBreakType:
        """
        Analyze if a pen is being broken by current price
        
        Args:
            pen: The pen to analyze
            current_price: Current market price
            
        Returns:
            Type of pen breaking
        """
        if pen.direction == PenDirection.UP:
            # For upward pen, breaking means price goes below the start (low)
            if current_price < pen.low:
                # Check if it's a full break (significantly below)
                break_threshold = pen.low * 0.99  # 1% below
                if current_price < break_threshold:
                    pen.break_type = PenBreakType.FULL_BREAK
                else:
                    pen.break_type = PenBreakType.PARTIAL_BREAK
                pen.break_price = current_price
                return pen.break_type
        else:
            # For downward pen, breaking means price goes above the start (high)
            if current_price > pen.high:
                # Check if it's a full break (significantly above)
                break_threshold = pen.high * 1.01  # 1% above
                if current_price > break_threshold:
                    pen.break_type = PenBreakType.FULL_BREAK
                else:
                    pen.break_type = PenBreakType.PARTIAL_BREAK
                pen.break_price = current_price
                return pen.break_type
        
        pen.break_type = PenBreakType.NONE
        pen.break_price = None
        return PenBreakType.NONE
    
    def get_upward_pens(self) -> List[ChanPen]:
        """Get all upward pens"""
        return [pen for pen in self.pens if pen.direction == PenDirection.UP]
    
    def get_downward_pens(self) -> List[ChanPen]:
        """Get all downward pens"""
        return [pen for pen in self.pens if pen.direction == PenDirection.DOWN]
    
    def get_latest_pen(self) -> Optional[ChanPen]:
        """Get the most recent pen"""
        return self.pens[-1] if self.pens else None
    
    def get_broken_pens(self) -> List[ChanPen]:
        """Get all pens that have been broken"""
        return [pen for pen in self.pens if pen.break_type != PenBreakType.NONE]
    
    def get_pen_sequence_validity(self) -> bool:
        """
        Check if the pen sequence is valid (alternating directions)
        
        Returns:
            True if sequence is valid
        """
        if len(self.pens) < 2:
            return True
        
        for i in range(len(self.pens) - 1):
            if self.pens[i].direction == self.pens[i + 1].direction:
                return False
        
        return True
    
    def filter_pens_by_length(self, min_length: float) -> List[ChanPen]:
        """
        Filter pens by minimum length
        
        Args:
            min_length: Minimum pen length
            
        Returns:
            List of pens meeting the length requirement
        """
        return [pen for pen in self.pens if pen.length >= min_length]
    
    def get_pen_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the pens
        
        Returns:
            Dictionary with pen statistics
        """
        if not self.pens:
            return {
                'total_pens': 0,
                'upward_pens': 0,
                'downward_pens': 0,
                'average_length': 0.0,
                'max_length': 0.0,
                'min_length': 0.0,
                'broken_pens': 0
            }
        
        upward_count = len(self.get_upward_pens())
        downward_count = len(self.get_downward_pens())
        lengths = [pen.length for pen in self.pens]
        broken_count = len(self.get_broken_pens())
        
        return {
            'total_pens': len(self.pens),
            'upward_pens': upward_count,
            'downward_pens': downward_count,
            'average_length': sum(lengths) / len(lengths),
            'max_length': max(lengths),
            'min_length': min(lengths),
            'broken_pens': broken_count
        }
    
    def clear(self):
        """Clear all pens"""
        self.pens.clear()
        self.logger.debug("Cleared all pens")
    
    def get_pens(self) -> List[ChanPen]:
        """Get copy of all pens"""
        return self.pens.copy()
    
    def set_parameters(self, min_pen_length: Optional[float] = None, 
                      min_kbar_count: Optional[int] = None):
        """
        Set pen processing parameters
        
        Args:
            min_pen_length: Minimum pen length
            min_kbar_count: Minimum kbar count
        """
        if min_pen_length is not None:
            self.min_pen_length = min_pen_length
        if min_kbar_count is not None:
            self.min_kbar_count = min_kbar_count
        
        self.logger.info(f"Updated parameters: min_length={self.min_pen_length}, "
                        f"min_kbar_count={self.min_kbar_count}") 