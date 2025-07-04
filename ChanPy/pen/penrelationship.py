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
from datetime import datetime
from ..chantypes import KBarRelationship
from ..fractal import Fractal

if TYPE_CHECKING:
    from .pen import ChanPen
    from ..fractal import Fractal
    from ..chan import Kbar
    from ..context import ChanContext
    from .pen import PenProcessor


@dataclass
class PenRelationshipResult:
    """Result of pen relationship analysis"""
    relationship: KBarRelationship
    can_merge: bool
    merge_recommendation: str
    special_considerations: List[str]
    confidence_score: float  # 0.0 to 1.0
    analysis_details: Dict[str, Any]


@dataclass
class PenDispatchResult:
    """Result of pen relationship dispatch processing"""
    action: str  # 'merge', 'treat_first_as_line', 'bypass_first', 'use_all', 'fallback'
    new_pens: List['ChanPen']
    pens_to_continue: List['ChanPen'] 
    global_line_created: bool
    case_type: str
    recommendation: str
    success: bool
    error_message: Optional[str] = None
    parsed_details: Optional[Dict[str, Any]] = None


class PenRelationshipHandler:
    """
    Pen Relationship Handler Class
    
    Handles special considerations for each KBarRelationship case when analyzing
    pen relationships. Provides specialized processing and recommendations for
    different types of relationships between pens.
    """
    
    def __init__(self, context: Optional['ChanContext'] = None, pen_processor: Optional['PenProcessor'] = None):
        """
        Initialize the pen relationship handler
        
        Args:
            context: ChanContext instance for accessing Chan structures and state
            pen_processor: PenProcessor instance for creating pens and global lines
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.context = context
        self.pen_processor = pen_processor
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
    
    def set_pen_processor(self, pen_processor: 'PenProcessor'):
        """
        Set the PenProcessor for creating pens and global lines
        
        Args:
            pen_processor: PenProcessor instance
        """
        self.pen_processor = pen_processor
        self.logger.debug("PenProcessor set for pen relationship handler")
    
    def dispatch_pen_relationship(self, pen1: 'ChanPen', pen2: 'ChanPen', pen3: 'ChanPen',
                                 relationship_result: PenRelationshipResult,
                                 pen_relationship: KBarRelationship,
                                 pen_list: List['ChanPen'], 
                                 current_index: int) -> PenDispatchResult:
        """
        Dispatch pen relationship processing based on the relationship analysis result
        
        This function handles the dispatch logic for processing three consecutive pens
        based on their relationship analysis. It determines what action to take and
        executes the appropriate processing.
        
        Args:
            pen1: First pen in the sequence
            pen2: Second pen in the sequence
            pen3: Third pen in the sequence
            relationship_result: Result from pen relationship analysis
            pen_relationship: The KBarRelationship between pen1 and pen3
            pen_list: The full list of pens being processed
            current_index: Current index in the pen list
            
        Returns:
            PenDispatchResult containing the processing outcome
        """
        if not self.pen_processor:
            return PenDispatchResult(
                action='error',
                new_pens=[],
                pens_to_continue=[],
                global_line_created=False,
                case_type='error',
                recommendation='No PenProcessor available',
                success=False,
                error_message='PenProcessor not set in PenRelationshipHandler'
            )
        
        self.logger.debug(f"Dispatching pen relationship: {relationship_result.relationship.value}")
        self.logger.debug(f"Can merge: {relationship_result.can_merge}")
        self.logger.debug(f"Merge recommendation: {relationship_result.merge_recommendation}")
        self.logger.debug(f"Confidence score: {relationship_result.confidence_score}")
        
        # Log special considerations
        for consideration in relationship_result.special_considerations:
            self.logger.debug(f"Special consideration: {consideration}")
        
        # Log analysis details
        for key, value in relationship_result.analysis_details.items():
            self.logger.debug(f"Analysis detail - {key}: {value}")
        
        # Parse analysis details to determine processing strategy
        parsed_details = self._parse_analysis_details(relationship_result.analysis_details)

        # Initialize result structure
        result = PenDispatchResult(
            action='unknown',
            new_pens=[],
            pens_to_continue=[],
            global_line_created=False,
            case_type=parsed_details['case_type'],
            recommendation=parsed_details['recommendation'],
            success=False,
            parsed_details=parsed_details
        )
        
        try:
            # Handle merging case
            if relationship_result.can_merge:
                result.action = 'merge'
                new_pen = self.pen_processor.create_validate_pen(pen1.start_fractal, pen3.end_fractal)
                
                if new_pen:
                    # Add information about the source pens and their relationship
                    new_pen.validation_details = new_pen.validation_details or {}
                    new_pen.validation_details['source_pens'] = [
                        f"Pen1({pen1.start_time}-{pen1.end_time})",
                        f"Pen2({pen2.start_time}-{pen2.end_time})",
                        f"Pen3({pen3.start_time}-{pen3.end_time})"
                    ]
                    new_pen.validation_details['three_pen_relationship'] = pen_relationship.value
                    new_pen.validation_details['three_pen_relationship_description'] = pen_relationship.get_description()
                    
                    # Add relationship analysis results
                    new_pen.validation_details['relationship_analysis'] = {
                        'can_merge': relationship_result.can_merge,
                        'merge_recommendation': relationship_result.merge_recommendation,
                        'confidence_score': relationship_result.confidence_score,
                        'special_considerations': relationship_result.special_considerations,
                        'analysis_details': relationship_result.analysis_details
                    }
                    
                    # Add parsed analysis details
                    new_pen.validation_details['parsed_analysis'] = parsed_details
                    
                    result.new_pens.append(new_pen)
                    result.success = True
                    self.logger.debug(f"Created new pen from 3 consecutive pens: {new_pen}")
                    self.logger.debug(f"Relationship analysis: {relationship_result.relationship.value} - {relationship_result.merge_recommendation}")
                else:
                    result.error_message = "Failed to create new pen from merged fractals"
                    result.success = False
                    
            else:
                self.logger.debug(f"Skipping pen creation - relationship analysis suggests not to merge: {relationship_result.merge_recommendation}")
                
                # Handle special cases based on parsed analysis details
                if parsed_details['case_type'] == "treat_first_pen_as_line":
                    result.action = 'treat_first_as_line'
                    self.logger.info("Special case: treating first pen as line - creating global line from pen1")
                    
                    # Create and add global line from the first pen
                    success = self.pen_processor.create_and_add_global_line_from_pen(pen1)
                    if success:
                        result.global_line_created = True
                        self.logger.info("Successfully created and added global line from first pen")
                        
                        # Add pen1 as a line-equivalent pen to the results
                        # Mark pen1 with special status to indicate it's been converted to a line
                        pen1.validation_details = pen1.validation_details or {}
                        pen1.validation_details['converted_to_global_line'] = True
                        pen1.validation_details['conversion_timestamp'] = datetime.now().isoformat()
                        result.new_pens.append(pen1)
                        
                        # Continue processing with pen2 and pen3 if available
                        if len(pen_list) > current_index + 2:
                            # Add pen2 and pen3 to continue processing
                            result.pens_to_continue.extend([pen2, pen3])
                            
                        result.success = True
                    else:
                        result.error_message = "Failed to create and add global line from first pen"
                        result.success = False
                        self.logger.error("Failed to create and add global line from first pen")
                        
                elif parsed_details['case_type'] == "bypass_first_pen":
                    result.action = 'bypass_first'
                    self.logger.info("Special case: bypassing first pen - need to shift processing window")
                    # Add pen2 and pen3 to continue processing, skip pen1
                    result.pens_to_continue.extend([pen2, pen3])
                    result.success = True
                    
                elif parsed_details['case_type'] == "all_valid":
                    result.action = 'use_all'
                    self.logger.info("All pens are valid - adding all three pens")
                    # Add all three pens
                    result.new_pens.extend([pen1, pen2, pen3])
                    result.success = True
                    
                else:
                    result.action = 'fallback'
                    self.logger.warning(f"Unknown case type: {parsed_details['case_type']} - using fallback")
                    # Fallback: add all pens
                    result.new_pens.extend([pen1, pen2, pen3])
                    result.success = True
                    
        except Exception as e:
            result.error_message = f"Error during pen relationship dispatch: {str(e)}"
            result.success = False
            self.logger.error(f"Error during pen relationship dispatch: {str(e)}")
            
        return result
    
    def _parse_analysis_details(self, analysis_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse analysis details from pen relationship analysis
        
        This function interprets the analysis_details from the relationship handler
        and provides instructions on how to handle the three consecutive pens.
        
        Args:
            analysis_details: Dictionary containing analysis details from relationship handler
            
        Returns:
            Dictionary with parsed instructions containing:
            - 'case_type': The type of case identified
            - 'action': The action to take
            - 'first_pen_treatment': How to treat the first pen ('use' or 'bypass')
            - 'next_pens_pattern': The pattern for next pens
            - 'recommendation': Human-readable recommendation
        """
        parsed_result = {
            'case_type': 'unknown',
            'action': 'default',
            'first_pen_treatment': 'use',
            'next_pens_pattern': 'sequential',
            'recommendation': 'Use default sequential processing'
        }
        
        if not analysis_details:
            return parsed_result
            
        case_type = analysis_details.get('case_type', 'unknown')
        parsed_result['case_type'] = case_type
        
        if case_type == "treat_first_pen_as_line":
            # First 4 cases: treat first pen as valid line
            parsed_result.update({
                'action': 'treat_pen1_as_first_line',
                'first_pen_treatment': 'use',
                'next_pens_pattern': 'pen1_as_line_then_p2_p3',
                'recommendation': 'Use pen1 as the first line and move to next two pens (p2-p3) to create new pen'
            })
            
        elif case_type == "bypass_first_pen":
            # Rest 3 cases: bypass first pen
            parsed_result.update({
                'action': 'bypass_pen1_use_p2_p3_p4',
                'first_pen_treatment': 'bypass',
                'next_pens_pattern': 'p2_p3_p4',
                'recommendation': 'Bypass pen1 and use pen2 as the first line, move to next two pens (p3-p4) to create new pen'
            })
            
        elif case_type == "all_valid":
            # All pens are valid, use normal processing
            parsed_result.update({
                'action': 'use_all_pens',
                'first_pen_treatment': 'use',
                'next_pens_pattern': 'p2_p3_p4',
                'recommendation': 'All pens are valid, use normal processing with p2-p3-p4 pattern'
            })
            
        elif case_type == "fallback":
            # Fallback case for unexpected patterns
            parsed_result.update({
                'action': 'fallback',
                'first_pen_treatment': 'use',
                'next_pens_pattern': 'sequential',
                'recommendation': 'Unexpected pattern detected, use fallback sequential processing'
            })
            
        # Add additional information from analysis_details
        if 'case_name' in analysis_details:
            parsed_result['case_name'] = analysis_details['case_name']
        if 'next_pens' in analysis_details:
            parsed_result['next_pens'] = analysis_details['next_pens']
        if 'error' in analysis_details:
            parsed_result['error'] = analysis_details['error']
            
        self.logger.debug(f"Parsed analysis details: {parsed_result}")
        return parsed_result

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
        - First check if there's already a first line existed
        - If no first line exists, handle 8 combinations of pen validity
        - For all valid pens: treat first pen as first line, move to p2-p3-p4
        - For not all valid pens: check 7 cases from image
        - Red circle = valid pen, green circle = invalid pen
        - First 4 cases: treat first pen as valid line
        - Rest 3 cases: bypass first pen like step 2
        
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
        
        # Step 1: Check if there's already a first line existed
        first_line_exists = False
        if self.context:
            try:
                # Check if there's a global line or any existing line
                self.logger.info(f"Checking if there's a global line or any existing line using context")
                global_line = self.context.get_global_line()
                latest_line = self.context.get_latest_line()
                
                if global_line or latest_line:
                    first_line_exists = True
                    self.logger.debug("First line already exists")
                else:
                    self.logger.debug("No first line exists, proceeding with pen validity analysis")
            except Exception as e:
                self.logger.warning(f"Error checking first line existence: {e}")
                first_line_exists = False
        
        special_considerations = []
        analysis_details = {
            "pen1_range": pen1.length,
            "pen3_range": pen3.length,
            "containment_ratio": pen3.length / pen1.length if pen1.length > 0 else 0,
            "first_line_exists": first_line_exists
        }
        
        # If first line exists, use original logic
        if first_line_exists:
            special_considerations.extend([
                "First line already exists",
                "Pen1 completely contains pen3 range",
                "Potential consolidation or reversal pattern",
                "Consider pen1 as dominant movement"
            ])
            
            # Add context-specific considerations
            if enhanced_analysis.get('global_line_direction'):
                special_considerations.append(f"Global line direction: {enhanced_analysis['global_line_direction']}")
            
            analysis_details.update(enhanced_analysis)
            
            return PenRelationshipResult(
                relationship=relationship,
                can_merge=True,
                merge_recommendation="First line exists - consider merging with pen1 dominance",
                special_considerations=special_considerations,
                confidence_score=0.7,
                analysis_details=analysis_details
            )
        
        # Step 2: Handle case when first line doesn't exist
        # Check validity of each pen (8 combinations: 2^3 = 8)
        pen1_valid = pen1.is_valid
        pen2_valid = pen2.is_valid
        pen3_valid = pen3.is_valid
        
        # Create validity pattern string for logging
        validity_pattern = f"pen1:{'V' if pen1_valid else 'I'}, pen2:{'V' if pen2_valid else 'I'}, pen3:{'V' if pen3_valid else 'I'}"
        self.logger.debug(f"Pen validity pattern: {validity_pattern}")
        
        analysis_details.update({
            "pen1_valid": pen1_valid,
            "pen2_valid": pen2_valid,
            "pen3_valid": pen3_valid,
            "validity_pattern": validity_pattern
        })
        
        # Step 3: Handle all pens valid case
        if pen1_valid and pen2_valid and pen3_valid:
            special_considerations.extend([
                "All pens are valid",
                "Treat first pen as first line",
                "Move to 3 consecutive pens starting from pen-2 (p2-p3-p4)"
            ])
            
            analysis_details["case_type"] = "all_valid"
            analysis_details["next_pens"] = "p2-p3-p4"
            
            return PenRelationshipResult(
                relationship=relationship,
                can_merge=False,  # Don't merge, treat pen1 as first line
                merge_recommendation="Treat pen1 as first line, process p2-p3-p4 next",
                special_considerations=special_considerations,
                confidence_score=0.9,
                analysis_details=analysis_details
            )
        
        # Step 4: Handle not all pens valid case - 7 cases from image
        # According to the image description:
        # - Red circle on black = valid pen, green circle = invalid pen
        # - First 4 cases: treat first pen as valid line
        # - Rest 3 cases: bypass first pen
        
        # Define the 7 cases based on validity patterns from the image
        # Case 1: pen1=I, pen2=I, pen3=I (III) - green-green-green
        # Case 2: pen1=I, pen2=I, pen3=V (IIV) - green-green-red
        # Case 3: pen1=I, pen2=V, pen3=I (IVI) - green-red-green
        # Case 4: pen1=I, pen2=V, pen3=V (IVV) - green-red-red
        # Case 5: pen1=V, pen2=I, pen3=I (VII) - red-green-green
        # Case 6: pen1=V, pen2=I, pen3=V (VIV) - red-green-red
        # Case 7: pen1=V, pen2=V, pen3=I (VVI) - red-red-green
        
        # First 4 cases: treat first pen as valid line
        if ((not pen1_valid and not pen2_valid and not pen3_valid) or  # Case 1: III
            (not pen1_valid and not pen2_valid and pen3_valid) or      # Case 2: IIV
            (not pen1_valid and pen2_valid and not pen3_valid) or      # Case 3: IVI
            (not pen1_valid and pen2_valid and pen3_valid)):           # Case 4: IVV
            
            case_names = {
                (False, False, False): "Case 1: III",
                (False, False, True): "Case 2: IIV",
                (False, True, False): "Case 3: IVI",
                (False, True, True): "Case 4: IVV"
            }
            
            case_name = case_names.get((pen1_valid, pen2_valid, pen3_valid), "Unknown Case")
            
            special_considerations.extend([
                f"Pen validity: {case_name}",
                "First 4 cases: treat first pen as valid line",
                "Use first pen as basis for line formation"
            ])
            
            analysis_details["case_type"] = "treat_first_pen_as_line"
            analysis_details["case_name"] = case_name
            analysis_details["action"] = "treat_pen1_as_first_line"
            
            return PenRelationshipResult(
                relationship=relationship,
                can_merge=False,  # Don't merge, treat pen1 as first line
                merge_recommendation=f"{case_name} - treat first pen as valid line",
                special_considerations=special_considerations,
                confidence_score=0.8,
                analysis_details=analysis_details
            )
        
        # Rest 3 cases: bypass first pen
        elif ((not pen1_valid and pen2_valid and not pen3_valid) or  # Case 5: IVI
              (not pen1_valid and not pen2_valid and pen3_valid) or  # Case 6: IIV
              (not pen1_valid and not pen2_valid and not pen3_valid)): # Case 7: III
            
            case_names = {
                (False, True, False): "Case 5: IVI",
                (False, False, True): "Case 6: IIV",
                (False, False, False): "Case 7: III"
            }
            
            case_name = case_names.get((pen1_valid, pen2_valid, pen3_valid), "Unknown Case")
            
            special_considerations.extend([
                f"Pen validity: {case_name}",
                "Rest 3 cases: bypass first pen",
                "Move to 3 consecutive pens starting from pen-2 (p2-p3-p4)"
            ])
            
            analysis_details["case_type"] = "bypass_first_pen"
            analysis_details["case_name"] = case_name
            analysis_details["action"] = "bypass_pen1_use_p2_p3_p4"
            analysis_details["next_pens"] = "p2-p3-p4"
            
            return PenRelationshipResult(
                relationship=relationship,
                can_merge=True,  # Merge by bypassing first pen
                merge_recommendation=f"{case_name} - bypass first pen, use p2-p3-p4",
                special_considerations=special_considerations,
                confidence_score=0.8,
                analysis_details=analysis_details
            )
        
        # Fallback case (shouldn't happen with 3 boolean values)
        else:
            special_considerations.extend([
                "Unexpected pen validity pattern",
                "Using fallback logic"
            ])
            
            analysis_details["case_type"] = "fallback"
            analysis_details["error"] = "Unexpected validity pattern"
            
            return PenRelationshipResult(
                relationship=relationship,
                can_merge=False,
                merge_recommendation="Unexpected pattern - manual review required",
                special_considerations=special_considerations,
                confidence_score=0.3,
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
            can_merge=True,  # merge with pen1
            merge_recommendation="Merge with pen1 to Down Trend",
            special_considerations=special_considerations,
            confidence_score=1,  # High confidence for clear separation
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
            can_merge=True,
            merge_recommendation="Merge with pen1 to Up Trend",
            special_considerations=special_considerations,
            confidence_score=1,  # High confidence for clear separation
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
            can_merge=True,
            merge_recommendation="Merge with pen1 to Up Trend",
            special_considerations=special_considerations,
            confidence_score=1,  # Strong confidence for overlap
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
            can_merge=True,
            merge_recommendation="Merge with pen1 to Down Trend",
            special_considerations=special_considerations,
            confidence_score=1,  # Strong confidence for overlap
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

# ==================== Helper Functions ====================

def get_three_pens_relationship(pen1: 'ChanPen', pen2: 'ChanPen', pen3: 'ChanPen') -> KBarRelationship:
    """
    Get the KBarRelationship between 3 consecutive pens
    
    This function treats:
    - pen1 as kbar1 (using pen1's low and high)
    - pen3 as kbar2 (using pen3's low and high)
    - pen2 is used for context but not directly in the relationship calculation
    
    Args:
        pen1: First pen (treated as kbar1)
        pen2: Second pen (for context)
        pen3: Third pen (treated as kbar2)
        
    Returns:
        KBarRelationship: The relationship between pen1 and pen3
    """
    logger = logging.getLogger(f"{__name__}.get_three_pens_relationship")
    
    # Use pen1's low and high as kbar1 (d1, g1)
    d1 = pen1.low   # Low of pen1
    g1 = pen1.high  # High of pen1
    
    # Use pen3's low and high as kbar2 (d2, g2)
    d2 = pen3.low   # Low of pen3
    g2 = pen3.high  # High of pen3
    
    # Get the relationship using KBarRelationship
    relationship = KBarRelationship.determine_relationship(d1, g1, d2, g2)
    logger.debug(f"  Relationship: {relationship.value} - {relationship.get_description()}")
    return relationship
