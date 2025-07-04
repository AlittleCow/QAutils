"""
Pen Utilities Module

This module contains utility functions for pen creation and manipulation.
"""

from typing import List, Optional, TYPE_CHECKING
from ..fractal import Fractal, FractalType, get_kbars_between_fractals
from .pentypes import ChanPen, PenDirection

if TYPE_CHECKING:
    from ..chan import Kbar
    from ..context import ChanContext


def create_pen(start_fractal: Fractal, end_fractal: Fractal, 
               context: Optional['ChanContext'] = None) -> Optional[ChanPen]:
    """
    Create a pen from two fractals
    
    This function creates a basic pen structure without validation.
    Validation should be performed separately using PenProcessor.validate_pen().
    
    Args:
        start_fractal: Starting fractal
        end_fractal: Ending fractal
        context: Optional ChanContext for getting raw kbars
        
    Returns:
        ChanPen object with basic properties set, or None if fractals are invalid
    """
    # Validate fractal types are different
    if start_fractal.fractal_type == end_fractal.fractal_type:
        return None
    
    # Determine pen direction
    if start_fractal.fractal_type == FractalType.BOTTOM:
        direction = PenDirection.UP
    else:
        direction = PenDirection.DOWN
    
    # Get raw kbars for this pen
    pen_kbars = get_kbars_between_fractals(start_fractal, end_fractal, context)
    
    # Calculate pen length
    length = abs(end_fractal.price - start_fractal.price)
    
    # Create pen with basic properties
    pen = ChanPen(
        start_fractal=start_fractal,
        end_fractal=end_fractal,
        direction=direction,
        high=0.0,  # Will be calculated in __post_init__
        low=0.0,   # Will be calculated in __post_init__
        length=length,
        raw_kbars=pen_kbars,
        confirmed=False,  # Will be set based on validation
        merged_kbars=[]  # Initialize as empty list - to be populated later
    )
    
    return pen
