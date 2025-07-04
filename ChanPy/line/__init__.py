"""
Line module for Chan Algorithm

This module provides line processing functionality including:
- Line formation from pens
- Line breaking analysis
- Line history tracking
- Global line management
"""

from .linetypes import (
    LineDirection, LineBreakType, LineStatus, LineHistoryEntry,
    LineEventType, LineFormationMethod, BreakAnalysisConstants,
    LineHistory, ChanLine
)
from .line import LineProcessor
from .lineutils import create_line_from_pen

__all__ = [
    # Types and enums
    'LineDirection', 'LineBreakType', 'LineStatus', 'LineHistoryEntry',
    'LineEventType', 'LineFormationMethod', 'BreakAnalysisConstants',
    'LineHistory',
    
    # Main classes
    'ChanLine', 'LineProcessor',
    
    # Utility functions
    'create_line_from_pen'
] 