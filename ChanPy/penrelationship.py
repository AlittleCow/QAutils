"""
Pen Relationship Handler Module for Chan Algorithm

This module handles the special considerations for each KBarRelationship case
when analyzing pen relationships. It provides specialized processing for
different types of relationships between pens.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING, Callable
from dataclasses import dataclass
from enum import Enum
from .chantypes import KBarRelationship

if TYPE_CHECKING:
    from .pen import ChanPen
    from .fractal import Fractal
    from .chan import Kbar
    from .context import ChanContext


@dataclass
class PenRelationshipResult:
    """Result of pen relationship analysis"""
    relationship: KBarRelationship
    can_merge: bool
    merge_recommendation: str
    special_considerations: List[str]
    confidence_score: float  # 0.0 to 1.0
    analysis_details: Dict[str, Any]


class PenRelationshipHandler:
    """
    Pen Relationship Handler Class
    
    Handles special considerations for each KBarRelationship case when analyzing
    pen relationships. Provides specialized processing and recommendations for
    different types of relationships between pens.
    """
    
    def __init__(self, context: Optional['ChanContext'] = None):
        """
        Initialize the pen relationship handler
        
        Args:
            context: ChanContext instance for accessing Chan structures and state
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.context = context
        self.handlers = self._initialize_handlers()
    
    def _initialize_handlers(self) -> Dict[KBarRelationship, Callable]:
        """
        Initialize the mapping of relationship types to handler functions
        
        Returns:
            Dictionary mapping KBarRelationship to handler functions
        """
        return {
            KBarRelationship.K1_CONTAINS_K2: self._handle_k1_contains_k2,
            KBarRelationship.K2_CONTAINS_K1: self._handle_k2_contains_k1,
            KBarRelationship.IDENTICAL: self._handle_identical,
            KBarRelationship.K1_ABOVE_K2: self._handle_k1_above_k2,
            KBarRelationship.K1_BELOW_K2: self._handle_k1_below_k2,
            KBarRelationship.UP_OVERLAP: self._handle_up_overlap,
            KBarRelationship.DOWN_OVERLAP: self._handle_down_overlap,
            KBarRelationship.SAME_LOW_K1_HIGHER: self._handle_same_low_k1_higher,
            KBarRelationship.SAME_LOW_K2_HIGHER: self._handle_same_low_k2_higher,
            KBarRelationship.SAME_HIGH_K1_LOWER: self._handle_same_high_k1_lower,
            KBarRelationship.SAME_HIGH_K2_LOWER: self._handle_same_high_k2_lower
        }
    
    def set_context(self, context: 'ChanContext'):
        """
        Set the ChanContext for accessing Chan structures and state
        
        Args:
            context: ChanContext instance
        """
        self.context = context
        self.logger.debug("ChanContext set for pen relationship handler")
    
    def get_context_info(self) -> Dict[str, Any]:
        """
        Get information about the current context
        
        Returns:
            Dictionary with context information
        """
        if not self.context:
            return {"context_available": False}
        
        return {
            "context_available": True,
            "current_symbol": self.context.current_symbol,
            "current_exchange": self.context.current_exchange,
            "current_period": self.context.current_period,
            "has_global_line": self.context.get_global_line() is not None,
            "latest_pen_available": self.context.get_latest_pen() is not None,
            "latest_fractal_available": self.context.get_latest_fractal() is not None
        }
    
    def analyze_pen_relationship(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                                pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Analyze the relationship between three consecutive pens with special considerations
        
        Args:
            pen1: First pen (treated as kbar1)
            pen2: Second pen (for context)
            pen3: Third pen (treated as kbar2)
            relationship: The KBarRelationship between pen1 and pen3
            
        Returns:
            PenRelationshipResult with analysis and recommendations
        """
        handler = self.handlers.get(relationship)
        if not handler:
            self.logger.warning(f"No handler found for relationship: {relationship}")
            return self._create_default_result(relationship)
        
        self.logger.debug(f"Processing pen relationship: {relationship.value}")
        
        # Log context information if available
        if self.context:
            context_info = self.get_context_info()
            self.logger.debug(f"Context info: {context_info}")
        
        return handler(pen1, pen2, pen3, relationship)
    
    def _create_default_result(self, relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Create a default result for unhandled relationships
        
        Args:
            relationship: The KBarRelationship type
            
        Returns:
            Default PenRelationshipResult
        """
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=False,
            merge_recommendation="No specific handler available",
            special_considerations=["Unknown relationship type"],
            confidence_score=0.0,
            analysis_details={"status": "unhandled"}
        )
    
    def _get_context_enhanced_analysis(self, pen1: 'ChanPen', pen2: 'ChanPen', pen3: 'ChanPen') -> Dict[str, Any]:
        """
        Get enhanced analysis using context information
        
        Args:
            pen1: First pen
            pen2: Second pen  
            pen3: Third pen
            
        Returns:
            Dictionary with enhanced analysis from context
        """
        enhanced_analysis = {}
        
        if not self.context:
            return enhanced_analysis
        
        try:
            # Get global line information
            global_line = self.context.get_global_line()
            if global_line:
                enhanced_analysis['global_line_direction'] = global_line.direction.name
                enhanced_analysis['global_line_status'] = global_line.status.name
            
            # Get latest pen information
            latest_pen = self.context.get_latest_pen()
            if latest_pen:
                enhanced_analysis['latest_pen_direction'] = latest_pen.direction.name
                enhanced_analysis['latest_pen_length'] = latest_pen.length
                enhanced_analysis['latest_pen_valid'] = latest_pen.is_valid
            
            # Get latest fractal information
            latest_fractal = self.context.get_latest_fractal()
            if latest_fractal:
                enhanced_analysis['latest_fractal_type'] = latest_fractal.fractal_type.name
                enhanced_analysis['latest_fractal_price'] = latest_fractal.price
            
            # Add context summary
            context_summary = self.context.get_context_summary()
            enhanced_analysis['context_summary'] = context_summary
            
        except Exception as e:
            self.logger.warning(f"Error getting context enhanced analysis: {e}")
            enhanced_analysis['context_error'] = str(e)
        
        return enhanced_analysis
    
    # ==================== Handler Functions for Each Relationship Type ====================
    
    def _handle_k1_contains_k2(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                              pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle K1_CONTAINS_K2 relationship (pen1 completely contains pen3)
        
        Special considerations:
        - Pen1 range completely encompasses pen3 range
        - This suggests pen1 is a larger movement that contains pen3's smaller range
        - May indicate pen consolidation or reversal pattern
        
        Args:
            pen1: First pen (contains pen3)
            pen2: Second pen (context)
            pen3: Third pen (contained by pen1)
            relationship: KBarRelationship.K1_CONTAINS_K2
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing K1_CONTAINS_K2 relationship")
        
        # Get context-enhanced analysis
        enhanced_analysis = self._get_context_enhanced_analysis(pen1, pen2, pen3)
        
        # TODO: Implement specific logic for K1_CONTAINS_K2
        # Placeholder implementation
        special_considerations = [
            "Pen1 completely contains pen3 range",
            "Potential consolidation or reversal pattern",
            "Consider pen1 as dominant movement"
        ]
        
        # Add context-specific considerations
        if enhanced_analysis.get('global_line_direction'):
            special_considerations.append(f"Global line direction: {enhanced_analysis['global_line_direction']}")
        
        analysis_details = {
            "pen1_range": pen1.length,
            "pen3_range": pen3.length,
            "containment_ratio": pen3.length / pen1.length if pen1.length > 0 else 0
        }
        analysis_details.update(enhanced_analysis)
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=True,  # Placeholder
            merge_recommendation="Consider merging with pen1 dominance",
            special_considerations=special_considerations,
            confidence_score=0.7,  # Placeholder
            analysis_details=analysis_details
        )
    
    def _handle_k2_contains_k1(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                              pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle K2_CONTAINS_K1 relationship (pen3 completely contains pen1)
        
        Special considerations:
        - Pen3 range completely encompasses pen1 range
        - This suggests pen3 is a larger movement that contains pen1's smaller range
        - May indicate trend continuation or expansion
        
        Args:
            pen1: First pen (contained by pen3)
            pen2: Second pen (context)
            pen3: Third pen (contains pen1)
            relationship: KBarRelationship.K2_CONTAINS_K1
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing K2_CONTAINS_K1 relationship")
        
        # TODO: Implement specific logic for K2_CONTAINS_K1
        # Placeholder implementation
        special_considerations = [
            "Pen3 completely contains pen1 range",
            "Potential trend continuation or expansion",
            "Consider pen3 as dominant movement"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=True,  # Placeholder
            merge_recommendation="Consider merging with pen3 dominance",
            special_considerations=special_considerations,
            confidence_score=0.7,  # Placeholder
            analysis_details={
                "pen1_range": pen1.length,
                "pen3_range": pen3.length,
                "containment_ratio": pen1.length / pen3.length if pen3.length > 0 else 0
            }
        )
    
    def _handle_identical(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                         pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle IDENTICAL relationship (pen1 and pen3 have identical ranges)
        
        Special considerations:
        - Pen1 and pen3 have exactly the same high and low points
        - This is a rare but significant pattern
        - May indicate strong support/resistance levels
        
        Args:
            pen1: First pen (identical to pen3)
            pen2: Second pen (context)
            pen3: Third pen (identical to pen1)
            relationship: KBarRelationship.IDENTICAL
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing IDENTICAL relationship")
        
        # TODO: Implement specific logic for IDENTICAL
        # Placeholder implementation
        special_considerations = [
            "Pen1 and pen3 have identical ranges",
            "Rare pattern indicating strong support/resistance",
            "High probability of significant price level"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=False,  # Placeholder - identical ranges are special
            merge_recommendation="Keep separate due to identical range significance",
            special_considerations=special_considerations,
            confidence_score=0.9,  # High confidence for rare pattern
            analysis_details={
                "pen1_range": pen1.length,
                "pen3_range": pen3.length,
                "identical_high": pen1.high,
                "identical_low": pen1.low
            }
        )
    
    def _handle_k1_above_k2(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                           pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle K1_ABOVE_K2 relationship (pen1 completely above pen3)
        
        Special considerations:
        - Pen1 low is above pen3 high (complete separation)
        - This indicates a significant gap between pen ranges
        - May suggest strong trend or gap pattern
        
        Args:
            pen1: First pen (above pen3)
            pen2: Second pen (context)
            pen3: Third pen (below pen1)
            relationship: KBarRelationship.K1_ABOVE_K2
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing K1_ABOVE_K2 relationship")
        
        # TODO: Implement specific logic for K1_ABOVE_K2
        # Placeholder implementation
        special_considerations = [
            "Pen1 completely above pen3 with gap",
            "Strong separation suggests significant movement",
            "Potential gap or strong trend pattern"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=False,  # Complete separation cannot merge
            merge_recommendation="Cannot merge - complete separation",
            special_considerations=special_considerations,
            confidence_score=0.8,  # High confidence for clear separation
            analysis_details={
                "gap_size": pen1.low - pen3.high,
                "pen1_range": pen1.length,
                "pen3_range": pen3.length
            }
        )
    
    def _handle_k1_below_k2(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                           pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle K1_BELOW_K2 relationship (pen1 completely below pen3)
        
        Special considerations:
        - Pen1 high is below pen3 low (complete separation)
        - This indicates a significant gap between pen ranges
        - May suggest strong upward trend or gap pattern
        
        Args:
            pen1: First pen (below pen3)
            pen2: Second pen (context)
            pen3: Third pen (above pen1)
            relationship: KBarRelationship.K1_BELOW_K2
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing K1_BELOW_K2 relationship")
        
        # TODO: Implement specific logic for K1_BELOW_K2
        # Placeholder implementation
        special_considerations = [
            "Pen1 completely below pen3 with gap",
            "Strong upward separation suggests bullish movement",
            "Potential gap up or strong uptrend pattern"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=False,  # Complete separation cannot merge
            merge_recommendation="Cannot merge - complete separation",
            special_considerations=special_considerations,
            confidence_score=0.8,  # High confidence for clear separation
            analysis_details={
                "gap_size": pen3.low - pen1.high,
                "pen1_range": pen1.length,
                "pen3_range": pen3.length
            }
        )
    
    def _handle_up_overlap(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                          pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle UP_OVERLAP relationship (pen1 and pen3 overlap with upward bias)
        
        Special considerations:
        - Pen1's high < pen3's high, pen1's low < pen3's low, pen1's high > pen3's low
        - This indicates upward progression with overlap
        - May suggest upward trend continuation
        
        Args:
            pen1: First pen (overlapping below)
            pen2: Second pen (context)
            pen3: Third pen (overlapping above)
            relationship: KBarRelationship.UP_OVERLAP
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing UP_OVERLAP relationship")
        
        # TODO: Implement specific logic for UP_OVERLAP
        # Placeholder implementation
        special_considerations = [
            "Upward overlapping pattern detected",
            "Suggests upward trend continuation",
            "Partial overlap with bullish bias"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=False,  # Overlaps typically don't merge
            merge_recommendation="Monitor for trend continuation",
            special_considerations=special_considerations,
            confidence_score=0.6,  # Medium confidence for overlap
            analysis_details={
                "overlap_size": pen1.high - pen3.low,
                "upward_bias": pen3.high - pen1.high,
                "pen1_range": pen1.length,
                "pen3_range": pen3.length
            }
        )
    
    def _handle_down_overlap(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                            pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle DOWN_OVERLAP relationship (pen1 and pen3 overlap with downward bias)
        
        Special considerations:
        - Pen1's high > pen3's high, pen1's low > pen3's low, pen3's high > pen1's low
        - This indicates downward progression with overlap
        - May suggest downward trend continuation
        
        Args:
            pen1: First pen (overlapping above)
            pen2: Second pen (context)
            pen3: Third pen (overlapping below)
            relationship: KBarRelationship.DOWN_OVERLAP
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing DOWN_OVERLAP relationship")
        
        # TODO: Implement specific logic for DOWN_OVERLAP
        # Placeholder implementation
        special_considerations = [
            "Downward overlapping pattern detected",
            "Suggests downward trend continuation",
            "Partial overlap with bearish bias"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=False,  # Overlaps typically don't merge
            merge_recommendation="Monitor for trend continuation",
            special_considerations=special_considerations,
            confidence_score=0.6,  # Medium confidence for overlap
            analysis_details={
                "overlap_size": pen3.high - pen1.low,
                "downward_bias": pen1.high - pen3.high,
                "pen1_range": pen1.length,
                "pen3_range": pen3.length
            }
        )
    
    def _handle_same_low_k1_higher(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                                  pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle SAME_LOW_K1_HIGHER relationship (same low, pen1 has higher high)
        
        Special considerations:
        - Pen1 and pen3 share the same low point
        - Pen1 extends higher than pen3
        - May indicate bullish divergence or expansion
        
        Args:
            pen1: First pen (higher high)
            pen2: Second pen (context)
            pen3: Third pen (same low, lower high)
            relationship: KBarRelationship.SAME_LOW_K1_HIGHER
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing SAME_LOW_K1_HIGHER relationship")
        
        # TODO: Implement specific logic for SAME_LOW_K1_HIGHER
        # Placeholder implementation
        special_considerations = [
            "Same low point with pen1 extending higher",
            "Potential bullish divergence or expansion",
            "Strong support level confirmed"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=True,  # Placeholder
            merge_recommendation="Consider merging with bullish bias",
            special_considerations=special_considerations,
            confidence_score=0.7,  # Good confidence for same low
            analysis_details={
                "shared_low": pen1.low,
                "pen1_high": pen1.high,
                "pen3_high": pen3.high,
                "high_difference": pen1.high - pen3.high
            }
        )
    
    def _handle_same_low_k2_higher(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                                  pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle SAME_LOW_K2_HIGHER relationship (same low, pen3 has higher high)
        
        Special considerations:
        - Pen1 and pen3 share the same low point
        - Pen3 extends higher than pen1
        - May indicate bullish momentum or trend acceleration
        
        Args:
            pen1: First pen (same low, lower high)
            pen2: Second pen (context)
            pen3: Third pen (higher high)
            relationship: KBarRelationship.SAME_LOW_K2_HIGHER
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing SAME_LOW_K2_HIGHER relationship")
        
        # TODO: Implement specific logic for SAME_LOW_K2_HIGHER
        # Placeholder implementation
        special_considerations = [
            "Same low point with pen3 extending higher",
            "Potential bullish momentum or trend acceleration",
            "Strong support level with upward breakout"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=True,  # Placeholder
            merge_recommendation="Consider merging with bullish momentum",
            special_considerations=special_considerations,
            confidence_score=0.7,  # Good confidence for same low
            analysis_details={
                "shared_low": pen1.low,
                "pen1_high": pen1.high,
                "pen3_high": pen3.high,
                "high_difference": pen3.high - pen1.high
            }
        )
    
    def _handle_same_high_k1_lower(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                                  pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle SAME_HIGH_K1_LOWER relationship (same high, pen1 has lower low)
        
        Special considerations:
        - Pen1 and pen3 share the same high point
        - Pen1 extends lower than pen3
        - May indicate bearish divergence or expansion
        
        Args:
            pen1: First pen (lower low)
            pen2: Second pen (context)
            pen3: Third pen (same high, higher low)
            relationship: KBarRelationship.SAME_HIGH_K1_LOWER
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing SAME_HIGH_K1_LOWER relationship")
        
        # TODO: Implement specific logic for SAME_HIGH_K1_LOWER
        # Placeholder implementation
        special_considerations = [
            "Same high point with pen1 extending lower",
            "Potential bearish divergence or expansion",
            "Strong resistance level confirmed"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=True,  # Placeholder
            merge_recommendation="Consider merging with bearish bias",
            special_considerations=special_considerations,
            confidence_score=0.7,  # Good confidence for same high
            analysis_details={
                "shared_high": pen1.high,
                "pen1_low": pen1.low,
                "pen3_low": pen3.low,
                "low_difference": pen3.low - pen1.low
            }
        )
    
    def _handle_same_high_k2_lower(self, pen1: 'ChanPen', pen2: 'ChanPen', 
                                  pen3: 'ChanPen', relationship: KBarRelationship) -> PenRelationshipResult:
        """
        Handle SAME_HIGH_K2_LOWER relationship (same high, pen3 has lower low)
        
        Special considerations:
        - Pen1 and pen3 share the same high point
        - Pen3 extends lower than pen1
        - May indicate bearish momentum or trend acceleration
        
        Args:
            pen1: First pen (same high, higher low)
            pen2: Second pen (context)
            pen3: Third pen (lower low)
            relationship: KBarRelationship.SAME_HIGH_K2_LOWER
            
        Returns:
            PenRelationshipResult with analysis
        """
        self.logger.debug("Processing SAME_HIGH_K2_LOWER relationship")
        
        # TODO: Implement specific logic for SAME_HIGH_K2_LOWER
        # Placeholder implementation
        special_considerations = [
            "Same high point with pen3 extending lower",
            "Potential bearish momentum or trend acceleration",
            "Strong resistance level with downward breakout"
        ]
        
        return PenRelationshipResult(
            relationship=relationship,
            can_merge=True,  # Placeholder
            merge_recommendation="Consider merging with bearish momentum",
            special_considerations=special_considerations,
            confidence_score=0.7,  # Good confidence for same high
            analysis_details={
                "shared_high": pen1.high,
                "pen1_low": pen1.low,
                "pen3_low": pen3.low,
                "low_difference": pen1.low - pen3.low
            }
        )
    
    # ==================== Utility Methods ====================
    
    def get_supported_relationships(self) -> List[KBarRelationship]:
        """
        Get list of all supported relationship types
        
        Returns:
            List of KBarRelationship types supported by this handler
        """
        return list(self.handlers.keys())
    
    def get_relationship_description(self, relationship: KBarRelationship) -> str:
        """
        Get human-readable description of a relationship type
        
        Args:
            relationship: KBarRelationship type
            
        Returns:
            Human-readable description
        """
        return relationship.get_description()
    
    def validate_relationship_handler(self, relationship: KBarRelationship) -> bool:
        """
        Validate that a handler exists for the given relationship type
        
        Args:
            relationship: KBarRelationship type to validate
            
        Returns:
            True if handler exists, False otherwise
        """
        return relationship in self.handlers
    
    def get_handler_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the handler configuration
        
        Returns:
            Dictionary with handler statistics
        """
        return {
            "total_handlers": len(self.handlers),
            "supported_relationships": [rel.value for rel in self.handlers.keys()],
            "handler_coverage": len(self.handlers) / len(KBarRelationship),
            "missing_handlers": [rel.value for rel in KBarRelationship if rel not in self.handlers]
        }
