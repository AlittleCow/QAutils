"""
Line Utilities Module for Chan Algorithm

This module contains utility functions for line operations and processing.
These utilities are designed to be standalone and avoid circular imports.
"""

import logging
from typing import Optional
from ..pen import ChanPen, PenDirection
from .linetypes import (
    LineDirection, LineBreakType, LineStatus, 
    ChanLine
)


def create_line_from_pen(pen: ChanPen) -> Optional[ChanLine]:
    """
    Create a line from a single pen
    
    This helper function creates a line from a single pen by treating it as both
    the start and end pen. This is used in special cases where the first
    pen should be treated as a line.
    
    Args:
        pen: The pen to create a line from
        
    Returns:
        ChanLine object if successful, None otherwise
    """
    logger = logging.getLogger(__name__)
    
    if not pen or not pen.is_valid:
        logger.warning("Cannot create line from invalid pen")
        return None
    
    # Create a line with the pen as both start and end
    line = ChanLine(
        start_pen=pen,
        end_pen=pen,
        pens=[pen],
        direction=LineDirection.UP if pen.direction == PenDirection.UP else LineDirection.DOWN,
        status=LineStatus.FORMING, # it should be FORMING, not COMPLETED
        break_type=LineBreakType.NONE,
        is_global=True,  # Mark as global line
        confirmed=True
    )
    
    # Add specific history entry for single pen creation
    line.history.add_entry(
        event_type='single_pen_creation',
        reason=f"Line created from single pen with direction {pen.direction.name}",
        details={
            'creation_method': 'single_pen',
            'pen_direction': pen.direction.name,
            'pen_high': pen.high,
            'pen_low': pen.low,
            'pen_length': pen.high - pen.low,
            'marked_as_global': True
        },
        pen_involved=pen,
        price_level=pen.start_price
    )
    
    logger.info(f"Created line from single pen {line}")
    
    return line 