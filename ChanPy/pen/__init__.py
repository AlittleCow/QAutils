"""
Pen Processing Module for Chan Algorithm

This module contains classes and functions for processing pens in the Chan algorithm.
"""

from .pen import PenProcessor
from .pentypes import ChanPen, PenDirection, PenBreakType
from .penrelationship import PenRelationshipHandler, PenRelationshipResult, get_three_pens_relationship
from .penrules import PenRuleValidator

__all__ = [
    'PenProcessor',
    'ChanPen',
    'PenDirection', 
    'PenBreakType',
    'PenRelationshipHandler',
    'PenRelationshipResult',
    'get_three_pens_relationship',
    'PenRuleValidator'
] 