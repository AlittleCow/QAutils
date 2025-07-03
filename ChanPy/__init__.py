"""
ChanPy - Chan Algorithm Implementation

A modular implementation of the Chan Algorithm for technical analysis
following the four-step process:
1. Merge kbar process for consecutive kbars
2. Check consecutive merged kbars for fractals  
3. Process raw kbars from fractal to fractal to identify chanpen
4. Process chanpen breaking and chanline formation
"""

__version__ = "1.0.0"
__author__ = "ChanPy Team"

# Import main classes for easy access
from .chan import Kbar, Pen, Direction, PenType
from .chan_processor import ChanProcessor
from .mergekbar import KbarMerger, MergedKbar, ChanMergeKbarDirection
from .fractal import FractalIdentifier, Fractal, FractalType
from .pen import PenProcessor, ChanPen, PenDirection
from .line import LineProcessor, ChanLine, LineDirection

__all__ = [
    'Kbar', 'Pen', 'Direction', 'PenType',
    'MergedKbar', 'ChanMergeKbarDirection', 'Fractal', 'FractalType', 'ChanPen', 'PenDirection', 'ChanLine', 'LineDirection',
    'ChanProcessor', 'KbarMerger', 'FractalIdentifier', 
    'PenProcessor', 'LineProcessor'
] 