"""
Fractal Utilities Module for Chan Algorithm

This module provides utility functions for working with fractals and related operations.
"""

import logging
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..chan import Kbar
    from ..context import ChanContext
    from .fractal import Fractal


def get_kbars_between_fractals(start_fractal: 'Fractal', end_fractal: 'Fractal', 
                              context: Optional['ChanContext'] = None,
                              symbol: Optional[str] = None,
                              exchange: Optional[str] = None,
                              period: Optional[str] = None) -> List['Kbar']:
    """
    Get raw kbars between two fractals using context
    
    Args:
        start_fractal: Starting fractal
        end_fractal: Ending fractal
        context: ChanContext instance for accessing kbar data
        symbol: Stock symbol (optional if context has current context set)
        exchange: Exchange code (optional if context has current context set)
        period: Time period (optional if context has current context set)
        
    Returns:
        List of kbars between the fractals
    """
    logger = logging.getLogger(__name__)
    
    if not context:
        logger.warning("No context provided, cannot load kbars between fractals")
        return []
    
    try:
        # Get the current state from context
        if symbol and exchange and period:
            state = context.get_state(symbol, exchange, period)
        else:
            state = context.get_current_state()
            
        if not state or not state.current_kbars:
            logger.warning("No kbars available in context")
            return []
        
        # Get time range from fractals
        start_time = start_fractal.timestamp
        end_time = end_fractal.timestamp
        
        # Find kbars within the time range
        pen_kbars = []
        for kbar in state.current_kbars:
            if start_time <= kbar.timestamp <= end_time:
                pen_kbars.append(kbar)
        
        logger.debug(f"Found {len(pen_kbars)} kbars between fractals "
                    f"from {start_time} to {end_time}")
        
        return pen_kbars
        
    except Exception as e:
        logger.error(f"Error getting kbars between fractals: {e}")
        return []


def get_kbars_for_fractal_range(fractals: List['Fractal'], 
                               context: Optional['ChanContext'] = None,
                               symbol: Optional[str] = None,
                               exchange: Optional[str] = None,
                               period: Optional[str] = None) -> List['Kbar']:
    """
    Get raw kbars for a range of fractals using context
    
    Args:
        fractals: List of fractals to get kbars for
        context: ChanContext instance for accessing kbar data
        symbol: Stock symbol (optional if context has current context set)
        exchange: Exchange code (optional if context has current context set)
        period: Time period (optional if context has current context set)
        
    Returns:
        List of kbars covering the fractal range
    """
    logger = logging.getLogger(__name__)
    
    if not fractals:
        return []
        
    if not context:
        logger.warning("No context provided, cannot load kbars for fractal range")
        return []
    
    try:
        # Get the current state from context
        if symbol and exchange and period:
            state = context.get_state(symbol, exchange, period)
        else:
            state = context.get_current_state()
            
        if not state or not state.current_kbars:
            logger.warning("No kbars available in context")
            return []
        
        # Get time range from first and last fractals
        start_time = fractals[0].timestamp
        end_time = fractals[-1].timestamp
        
        # Find kbars within the time range
        range_kbars = []
        for kbar in state.current_kbars:
            if start_time <= kbar.timestamp <= end_time:
                range_kbars.append(kbar)
        
        logger.debug(f"Found {len(range_kbars)} kbars for fractal range "
                    f"from {start_time} to {end_time} ({len(fractals)} fractals)")
        
        return range_kbars
        
    except Exception as e:
        logger.error(f"Error getting kbars for fractal range: {e}")
        return []


def validate_fractal_kbar_alignment(fractal: 'Fractal', 
                                   context: Optional['ChanContext'] = None,
                                   symbol: Optional[str] = None,
                                   exchange: Optional[str] = None,
                                   period: Optional[str] = None) -> bool:
    """
    Validate that a fractal aligns with available kbar data
    
    Args:
        fractal: Fractal to validate
        context: ChanContext instance for accessing kbar data
        symbol: Stock symbol (optional if context has current context set)
        exchange: Exchange code (optional if context has current context set)
        period: Time period (optional if context has current context set)
        
    Returns:
        True if fractal aligns with kbar data, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    if not context:
        logger.warning("No context provided, cannot validate fractal alignment")
        return False
    
    try:
        # Get the current state from context
        if symbol and exchange and period:
            state = context.get_state(symbol, exchange, period)
        else:
            state = context.get_current_state()
            
        if not state or not state.current_kbars:
            logger.warning("No kbars available in context for validation")
            return False
        
        # Check if fractal timestamp exists in kbar data
        fractal_time = fractal.timestamp
        for kbar in state.current_kbars:
            if kbar.timestamp == fractal_time:
                logger.debug(f"Fractal at {fractal_time} aligns with kbar data")
                return True
        
        logger.warning(f"Fractal at {fractal_time} does not align with available kbar data")
        return False
        
    except Exception as e:
        logger.error(f"Error validating fractal alignment: {e}")
        return False


def get_fractal_context_info(fractal: 'Fractal',
                            context: Optional['ChanContext'] = None,
                            symbol: Optional[str] = None,
                            exchange: Optional[str] = None,
                            period: Optional[str] = None) -> dict:
    """
    Get context information for a fractal
    
    Args:
        fractal: Fractal to get context info for
        context: ChanContext instance for accessing data
        symbol: Stock symbol (optional if context has current context set)
        exchange: Exchange code (optional if context has current context set)
        period: Time period (optional if context has current context set)
        
    Returns:
        Dictionary with fractal context information
    """
    logger = logging.getLogger(__name__)
    
    if not context:
        return {'error': 'No context provided'}
    
    try:
        # Get the current state from context
        if symbol and exchange and period:
            state = context.get_state(symbol, exchange, period)
        else:
            state = context.get_current_state()
            
        if not state:
            return {'error': 'No state available in context'}
        
        # Find surrounding kbars
        fractal_time = fractal.timestamp
        surrounding_kbars = []
        
        if state.current_kbars:
            for i, kbar in enumerate(state.current_kbars):
                if kbar.timestamp == fractal_time:
                    # Get surrounding kbars (2 before and 2 after)
                    start_idx = max(0, i - 2)
                    end_idx = min(len(state.current_kbars), i + 3)
                    surrounding_kbars = state.current_kbars[start_idx:end_idx]
                    break
        
        return {
            'fractal_type': fractal.fractal_type.name,
            'fractal_price': fractal.price,
            'fractal_timestamp': fractal.timestamp,
            'fractal_strength': fractal.strength,
            'surrounding_kbars_count': len(surrounding_kbars),
            'total_kbars_in_context': len(state.current_kbars) if state.current_kbars else 0,
            'total_fractals_in_context': len(state.current_fractals) if state.current_fractals else 0,
            'alignment_valid': validate_fractal_kbar_alignment(fractal, context, symbol, exchange, period)
        }
        
    except Exception as e:
        logger.error(f"Error getting fractal context info: {e}")
        return {'error': f'Error getting context info: {str(e)}'} 