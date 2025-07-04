"""
Fractal Identification Module for Chan Algorithm

This module handles the identification of fractals (分型) from merged kbars.
A fractal is formed by three consecutive merged kbars where the middle one
forms either a top or bottom pattern.
"""

import logging
from typing import List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from ..mergekbar import MergedKbar

if TYPE_CHECKING:
    from ..context import ChanContext


class FractalType(Enum):
    """Fractal type enumeration"""
    TOP = 1      # Top fractal (顶分型)
    BOTTOM = -1  # Bottom fractal (底分型)
    NONE = 0     # No fractal


@dataclass
class Fractal:
    """Fractal data structure"""
    index: int  # Index in the merged kbar sequence
    timestamp: str
    price: float
    fractal_type: FractalType
    merged_kbar: MergedKbar
    left_kbar: MergedKbar
    right_kbar: MergedKbar
    confirmed: bool = False
    strength: float = 0.0  # Strength of the fractal pattern
    
    def __post_init__(self):
        """Calculate fractal strength after initialization"""
        self.strength = self._calculate_strength()
    
    def __repr__(self) -> str:
        """
        String representation of the fractal
        
        Returns:
            Formatted string with fractal details
        """
        fractal_name = "TOP   " if self.fractal_type == FractalType.TOP else "BOTTOM"
        
        return (f"Fractal({fractal_name} @ {self.merged_kbar.timestamp_end} {self.price:.4f}, "
                f"start: {self.left_kbar.timestamp_end}, "
                f"end: {self.right_kbar.timestamp_end}, "
                f"strength: {self.strength:.4f})")
    
    def _calculate_strength(self) -> float:
        """
        Calculate the strength of the fractal pattern
        
        Returns:
            Strength value (higher is stronger)
        """
        if self.fractal_type == FractalType.TOP:
            left_diff = self.price - self.left_kbar.high
            right_diff = self.price - self.right_kbar.high
            return (left_diff + right_diff) / 2
        elif self.fractal_type == FractalType.BOTTOM:
            left_diff = self.left_kbar.low - self.price
            right_diff = self.right_kbar.low - self.price
            return (left_diff + right_diff) / 2
        else:
            return 0.0


class FractalIdentifier:
    """
    Fractal Identifier Class
    
    Identifies fractals from merged kbar sequences according to Chan algorithm rules.
    A fractal requires three consecutive merged kbars with specific high/low relationships.
    """
    
    def __init__(self, strict_mode: bool = True, context: Optional['ChanContext'] = None):
        """
        Initialize Fractal Identifier
        
        Args:
            strict_mode: If True, use strict fractal identification rules
            context: Optional ChanContext for state management
        """
        self.logger = logging.getLogger(f"{__name__}")
        self.strict_mode = strict_mode
        self.context = context
        self.fractals: List[Fractal] = []
        self.min_fractal_strength = 0.0  # Minimum strength for valid fractal
    
    def set_context(self, context: 'ChanContext'):
        """
        Set the ChanContext for the fractal identifier
        
        Args:
            context: ChanContext instance
        """
        self.context = context
        self.logger.debug("ChanContext set for fractal identifier")
    
    def is_top_fractal(self, left: MergedKbar, middle: MergedKbar, right: MergedKbar) -> bool:
        """
        Check if three merged kbars form a top fractal
        
        Args:
            left: Left merged kbar
            middle: Middle merged kbar  
            right: Right merged kbar
            
        Returns:
            True if forms a top fractal, False otherwise
        """
        if self.strict_mode:
            # Strict mode: middle high must be strictly higher than both sides
            # and middle low must be >= both sides low
            return (middle.high > left.high and middle.high > right.high and
                    middle.low >= left.low and middle.low >= right.low)
        else:
            # Relaxed mode: allow equal highs
            return (middle.high >= left.high and middle.high >= right.high and
                    middle.low >= left.low and middle.low >= right.low and
                    (middle.high > left.high or middle.high > right.high))
    
    def is_bottom_fractal(self, left: MergedKbar, middle: MergedKbar, right: MergedKbar) -> bool:
        """
        Check if three merged kbars form a bottom fractal
        
        Args:
            left: Left merged kbar
            middle: Middle merged kbar
            right: Right merged kbar
            
        Returns:
            True if forms a bottom fractal, False otherwise
        """
        if self.strict_mode:
            # Strict mode: middle low must be strictly lower than both sides
            # and middle high must be <= both sides high
            return (middle.low < left.low and middle.low < right.low and
                    middle.high <= left.high and middle.high <= right.high)
        else:
            # Relaxed mode: allow equal lows
            return (middle.low <= left.low and middle.low <= right.low and
                    middle.high <= left.high and middle.high <= right.high and
                    (middle.low < left.low or middle.low < right.low))
    
    def identify_fractal(self, left: MergedKbar, middle: MergedKbar, right: MergedKbar, 
                        index: int) -> Optional[Fractal]:
        """
        Identify fractal from three consecutive merged kbars
        
        Args:
            left: Left merged kbar
            middle: Middle merged kbar
            right: Right merged kbar
            index: Index of the middle kbar in the sequence
            
        Returns:
            Fractal object if found, None otherwise
        """
        if self.is_top_fractal(left, middle, right):
            fractal = Fractal(
                index=index,
                timestamp=middle.timestamp_end,
                price=middle.high,
                fractal_type=FractalType.TOP,
                merged_kbar=middle,
                left_kbar=left,
                right_kbar=right,
                confirmed=True
            )
            
            # Check if fractal meets minimum strength requirement
            if fractal.strength >= self.min_fractal_strength:
                return fractal
        
        elif self.is_bottom_fractal(left, middle, right):
            fractal = Fractal(
                index=index,
                timestamp=middle.timestamp_end,
                price=middle.low,
                fractal_type=FractalType.BOTTOM,
                merged_kbar=middle,
                left_kbar=left,
                right_kbar=right,
                confirmed=True
            )
            
            # Check if fractal meets minimum strength requirement
            if fractal.strength >= self.min_fractal_strength:
                return fractal
        
        return None
    
    def process_merged_kbars(self, merged_kbars: List[MergedKbar]) -> List[Fractal]:
        """
        Process a sequence of merged kbars to identify all fractals
        
        Args:
            merged_kbars: List of merged kbars in chronological order
            
        Returns:
            List of identified fractals
        """
        if len(merged_kbars) < 3:
            return []
        
        fractals = []
        
        for i in range(1, len(merged_kbars) - 1):
            left = merged_kbars[i - 1]
            middle = merged_kbars[i]
            right = merged_kbars[i + 1]
            
            fractal = self.identify_fractal(left, middle, right, i)
            if fractal:
                fractals.append(fractal)
                self.logger.debug(f"Fractal: {fractal}")
                
        
        self.fractals = fractals
        self.logger.info(f"Identified {len(fractals)} fractals from {len(merged_kbars)} merged kbars")
        
        return fractals
    
    def get_fractal_pairs(self) -> List[Tuple[Fractal, Fractal]]:
        """
        Get consecutive fractal pairs for pen formation
        
        Returns:
            List of fractal pairs (start_fractal, end_fractal)
        """
        if len(self.fractals) < 2:
            return []
        
        pairs = []
        for i in range(len(self.fractals) - 1):
            current = self.fractals[i]
            next_fractal = self.fractals[i + 1]
            
            # Only pair fractals of different types
            if current.fractal_type != next_fractal.fractal_type:
                pairs.append((current, next_fractal))
        
        return pairs
    
    def get_top_fractals(self) -> List[Fractal]:
        """Get all top fractals"""
        return [f for f in self.fractals if f.fractal_type == FractalType.TOP]
    
    def get_bottom_fractals(self) -> List[Fractal]:
        """Get all bottom fractals"""  
        return [f for f in self.fractals if f.fractal_type == FractalType.BOTTOM]
    
    def filter_fractals_by_strength(self, min_strength: float) -> List[Fractal]:
        """
        Filter fractals by minimum strength
        
        Args:
            min_strength: Minimum strength threshold
            
        Returns:
            List of fractals meeting the strength requirement
        """
        return [f for f in self.fractals if f.strength >= min_strength]
    
    def get_latest_fractal(self) -> Optional[Fractal]:
        """Get the most recent fractal"""
        return self.fractals[-1] if self.fractals else None
    
    def get_fractal_at_index(self, index: int) -> Optional[Fractal]:
        """
        Get fractal at specific merged kbar index
        
        Args:
            index: Merged kbar index
            
        Returns:
            Fractal at the index, or None if not found
        """
        for fractal in self.fractals:
            if fractal.index == index:
                return fractal
        return None
    
    def validate_fractal_sequence(self) -> bool:
        """
        Validate that fractals alternate between top and bottom types
        
        Returns:
            True if sequence is valid, False otherwise
        """
        if len(self.fractals) < 2:
            return True
        
        for i in range(len(self.fractals) - 1):
            if self.fractals[i].fractal_type == self.fractals[i + 1].fractal_type:
                return False
        
        return True
    
    def set_minimum_strength(self, min_strength: float):
        """
        Set minimum fractal strength requirement
        
        Args:
            min_strength: Minimum strength value
        """
        self.min_fractal_strength = min_strength
        self.logger.info(f"Set minimum fractal strength to {min_strength}")
    
    def clear(self):
        """Clear all fractals"""
        self.fractals.clear()
        self.logger.debug("Cleared all fractals")
    
    def get_fractals(self) -> List[Fractal]:
        """Get copy of all fractals"""
        return self.fractals.copy()
    
    def get_fractal_summary(self) -> dict:
        """
        Get summary statistics of identified fractals
        
        Returns:
            Dictionary with fractal statistics
        """
        if not self.fractals:
            return {
                'total_fractals': 0,
                'top_fractals': 0,
                'bottom_fractals': 0,
                'average_strength': 0.0,
                'max_strength': 0.0,
                'min_strength': 0.0
            }
        
        top_count = len(self.get_top_fractals())
        bottom_count = len(self.get_bottom_fractals())
        strengths = [f.strength for f in self.fractals]
        
        return {
            'total_fractals': len(self.fractals),
            'top_fractals': top_count,
            'bottom_fractals': bottom_count,
            'average_strength': sum(strengths) / len(strengths),
            'max_strength': max(strengths),
            'min_strength': min(strengths)
        } 