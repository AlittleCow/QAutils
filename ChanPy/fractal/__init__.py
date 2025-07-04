"""
Fractal module for Chan Algorithm

This module provides fractal identification functionality and utilities.
"""

from .fractal import Fractal, FractalType, FractalIdentifier
from .fractalutils import (
    get_kbars_between_fractals,
    get_kbars_for_fractal_range,
    validate_fractal_kbar_alignment,
    get_fractal_context_info
)

__all__ = [
    'Fractal', 
    'FractalType', 
    'FractalIdentifier',
    'get_kbars_between_fractals',
    'get_kbars_for_fractal_range',
    'validate_fractal_kbar_alignment',
    'get_fractal_context_info'
] 