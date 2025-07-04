"""
ChanPy - Chan Algorithm Implementation in Python

A comprehensive implementation of the Chan algorithm for technical analysis.
"""

from .chan import ChanIndicator
from .fractal import Fractal, FractalType, FractalIdentifier
from .mergekbar import MergedKbar, KbarMerger, ChanMergeKbarDirection
from .chantypes import (
    KBarRelationship, 
    Kbar,
    Direction,
    PenType,
    BodySizeCategory,
    KbarShape
)
from .context import ChanContext, ChanState
from .chan_processor import ChanProcessor
from .pen import PenProcessor, ChanPen, PenDirection
from .line import LineProcessor, ChanLine, LineDirection

__version__ = "1.0.0"

__all__ = [
    'ChanIndicator',
    'Fractal', 'FractalType', 'FractalIdentifier', 
    'MergedKbar', 'KbarMerger', 'ChanMergeKbarDirection',
    'KBarRelationship', 'Kbar', 'Direction', 'PenType', 'BodySizeCategory', 'KbarShape',
    'ChanContext', 'ChanState', 'ChanProcessor',
    'PenProcessor', 'ChanPen', 'PenDirection',
    'LineProcessor', 'ChanLine', 'LineDirection'
] 