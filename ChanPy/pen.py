"""
Pen Processing Module for Chan Algorithm

This module handles the formation and validation of pens (笔) from fractals.
A pen connects two fractals of different types and must satisfy specific
validation criteria based on the raw kbars between the fractals.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from .fractal import Fractal, FractalType
from .mergekbar import MergedKbar
from .chantypes import KBarRelationship
from .penrelationship import PenRelationshipHandler

if TYPE_CHECKING:
    from .chan import Kbar
    from .penrules import PenRuleValidator
    from .context import ChanContext


class PenDirection(Enum):
    """Pen direction enumeration"""
    UP = 1      # Upward pen (向上笔)
    DOWN = -1   # Downward pen (向下笔)


class PenBreakType(Enum):
    """Pen breaking type enumeration"""
    NONE = 0           # No breaking
    PARTIAL_BREAK = 1  # Partial breaking
    FULL_BREAK = 2     # Full breaking


@dataclass
class ChanPen:
    """Chan Pen data structure"""
    start_fractal: Fractal
    end_fractal: Fractal
    direction: PenDirection
    high: float
    low: float
    length: float
    raw_kbars: List['Kbar']  # Raw kbars between fractals
    confirmed: bool = False
    break_type: PenBreakType = PenBreakType.NONE
    break_price: Optional[float] = None
    merged_kbars: Optional[List[MergedKbar]] = None  # Merged kbars in the pen
    # Validation result fields
    is_valid: bool = False
    failed_rules: Optional[List[str]] = None
    validation_details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Calculate pen properties after initialization"""
        if self.merged_kbars is None:
            self.merged_kbars = []
        if self.failed_rules is None:
            self.failed_rules = []
        if self.validation_details is None:
            self.validation_details = {}
        self._calculate_properties()
    
    def _calculate_properties(self):
        """Calculate pen high, low, and length"""
        if self.direction == PenDirection.UP:
            self.high = self.end_fractal.price
            self.low = self.start_fractal.price
            self.length = self.high - self.low
        else:
            self.high = self.start_fractal.price
            self.low = self.end_fractal.price
            self.length = self.high - self.low
    
    @property
    def start_price(self) -> float:
        """Get pen start price"""
        return self.start_fractal.price
    
    @property
    def end_price(self) -> float:
        """Get pen end price"""
        return self.end_fractal.price
    
    @property
    def start_time(self) -> str:
        """Get pen start time"""
        return self.start_fractal.timestamp
    
    @property
    def end_time(self) -> str:
        """Get pen end time"""  
        return self.end_fractal.timestamp
    
    @property
    def kbar_count(self) -> int:
        """Get number of raw kbars in this pen"""
        return len(self.raw_kbars)
    
    @property
    def merged_kbar_count(self) -> int:
        """Get number of merged kbars in this pen"""
        return len(self.merged_kbars) if self.merged_kbars else 0
    
    def __repr__(self) -> str:
        """String representation of the pen"""
        direction_str = "UP  " if self.direction == PenDirection.UP else "DOWN"
        valid_str = "VALID" if self.is_valid else "INVALID"
        return (f"ChanPen(direction={direction_str}, "
                f"start={self.start_time}, "
                f"end={self.end_time}, "
                f"raw_kbars={self.kbar_count:2d}, "
                f"merged_kbars={self.merged_kbar_count:2d}, "
                f"length={self.length:8.4f}, "
                f"status={valid_str})")


class PenProcessor:
    """
    Pen Processor Class
    
    Processes fractals to form valid pens according to Chan algorithm rules.
    Validates pens against raw kbar data and handles pen breaking analysis.
    """
    
    def __init__(self, min_pen_length: float = 0.0, min_kbar_count: int = 5, 
                 pen_validator: Optional['PenRuleValidator'] = None,
                 context: Optional['ChanContext'] = None):
        """
        Initialize Pen Processor
        
        Args:
            min_pen_length: Minimum pen length for validation
            min_kbar_count: Minimum number of kbars for a valid pen
            pen_validator: Optional pen rule validator for advanced validation
            context: Optional ChanContext for accessing Chan structures and state
        """
        self.logger = logging.getLogger(f"{__name__}")
        self.min_pen_length = min_pen_length
        self.min_kbar_count = min_kbar_count
        self.pen_validator = pen_validator
        self.context = context
        self.pens: List[ChanPen] = []
        self.raw_kbars: List['Kbar'] = []
        self.pen_relationship_handler: Optional[PenRelationshipHandler] = PenRelationshipHandler(context=context)
    
    def set_context(self, context: 'ChanContext'):
        """
        Set the ChanContext for the pen processor
        
        Args:
            context: ChanContext instance
        """
        self.context = context
        if self.pen_relationship_handler:
            self.pen_relationship_handler.set_context(context)
        self.logger.debug("ChanContext set for pen processor")
    
    def set_raw_kbars(self, kbars: List['Kbar']):
        """
        Set the raw kbar data for pen validation
        
        Args:
            kbars: List of raw kbars in chronological order
        """
        self.raw_kbars = kbars
        self.logger.debug(f"Set {len(kbars)} raw kbars for pen validation")
    
    def validate_pen_with_raw_kbars(self, start_fractal: Fractal, end_fractal: Fractal) -> bool:
        """
        Validate a potential pen using raw kbar data
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            
        Returns:
            True if pen is valid according to raw kbar analysis
        """
        if not self.raw_kbars:
            self.logger.warning("No raw kbars available for pen validation")
            return True  # Allow pen if no raw data available
        
        # Find raw kbars between the two fractals
        pen_kbars = self._get_kbars_between_fractals(start_fractal, end_fractal)
        
        if len(pen_kbars) < self.min_kbar_count:
            return False
        
        # Validate pen direction consistency
        if start_fractal.fractal_type == FractalType.BOTTOM:
            # Should be an upward pen
            return self._validate_upward_pen(start_fractal, end_fractal, pen_kbars)
        else:
            # Should be a downward pen
            return self._validate_downward_pen(start_fractal, end_fractal, pen_kbars)
    
    def _get_kbars_between_fractals(self, start_fractal: Fractal, end_fractal: Fractal) -> List['Kbar']:
        """
        Get raw kbars between two fractals
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            
        Returns:
            List of kbars between the fractals
        """
        # This is a simplified implementation
        # In practice, you would need to match fractals to kbar timestamps
        start_time = start_fractal.timestamp
        end_time = end_fractal.timestamp
        
        # Find kbars within the time range
        pen_kbars = []
        for kbar in self.raw_kbars:
            if start_time <= kbar.timestamp <= end_time:
                pen_kbars.append(kbar)
        
        return pen_kbars
    
    def _validate_upward_pen(self, start_fractal: Fractal, end_fractal: Fractal, 
                           pen_kbars: List['Kbar']) -> bool:
        """
        Validate an upward pen against raw kbars
        
        Args:
            start_fractal: Bottom fractal (start)
            end_fractal: Top fractal (end)
            pen_kbars: Raw kbars in the pen
            
        Returns:
            True if pen is valid
        """
        if not pen_kbars:
            return False
        
        # Check that the pen maintains upward trend
        # No kbar low should break below the start fractal low
        start_low = start_fractal.price
        
        for kbar in pen_kbars:
            if kbar.low < start_low:
                return False
        
        # Check that we reach the end fractal high
        max_high = max(kbar.high for kbar in pen_kbars)
        return abs(max_high - end_fractal.price) < 0.001  # Allow small tolerance
    
    def _validate_downward_pen(self, start_fractal: Fractal, end_fractal: Fractal,
                             pen_kbars: List['Kbar']) -> bool:
        """
        Validate a downward pen against raw kbars
        
        Args:
            start_fractal: Top fractal (start)
            end_fractal: Bottom fractal (end)
            pen_kbars: Raw kbars in the pen
            
        Returns:
            True if pen is valid
        """
        if not pen_kbars:
            return False
        
        # Check that the pen maintains downward trend
        # No kbar high should break above the start fractal high
        start_high = start_fractal.price
        
        for kbar in pen_kbars:
            if kbar.high > start_high:
                return False
        
        # Check that we reach the end fractal low
        min_low = min(kbar.low for kbar in pen_kbars)
        return abs(min_low - end_fractal.price) < 0.001  # Allow small tolerance
    
    def create_pen(self, start_fractal: Fractal, end_fractal: Fractal) -> Optional[ChanPen]:
        """
        Create a pen from two fractals
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            
        Returns:
            ChanPen object with validation results stored
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
        pen_kbars = self._get_kbars_between_fractals(start_fractal, end_fractal)
        
        # Calculate pen length
        length = abs(end_fractal.price - start_fractal.price)
        
        # Create pen with basic validation
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
        
        # Perform validation and store results
        is_valid = True
        failed_rules = []
        validation_details = {}
        
        # Basic validation checks
        if length < self.min_pen_length:
            is_valid = False
            failed_rules.append("min_pen_length")
        
        if len(pen_kbars) < self.min_kbar_count:
            is_valid = False
            failed_rules.append("min_kbar_count")
        
        # Validate with raw kbars
        if not self.validate_pen_with_raw_kbars(start_fractal, end_fractal):
            is_valid = False
            failed_rules.append("raw_kbar_validation")
        
        # Advanced pen validation using pen rules (if validator is provided)
        if self.pen_validator:
            rule_valid, rule_failed_rules, rule_validation_details = self.pen_validator.validate_pen(
                start_fractal, end_fractal, pen_kbars
            )
            
            if not rule_valid:
                is_valid = False
                failed_rules.extend([rule.value for rule in rule_failed_rules])
                validation_details.update(rule_validation_details)
                self.logger.debug(f"Pen validation failed: {[rule.value for rule in rule_failed_rules]}")
                self.logger.debug(f"Validation details: {rule_validation_details}")
            else:
                is_valid = True
                validation_details.update(rule_validation_details)
                self.logger.info(f"Pen validation passed: {rule_validation_details.get('passed_rules', 0)}/{rule_validation_details.get('total_rules', 0)} rules")
        
        # Store validation results in pen
        pen.is_valid = is_valid
        pen.failed_rules = failed_rules
        pen.validation_details = validation_details
        pen.confirmed = is_valid
        
        return pen
    
    def process_fractals(self, fractals: List[Fractal]) -> List[ChanPen]:
        """
        Process a list of fractals to create pens using the correct 3-step flow
        
        Step 1: Create pens from all consecutive fractals and store validation results
        Step 2: Process every 3 consecutive pens to create new pens
        Step 3: Filter to only keep valid pens
        
        Args:
            fractals: List of fractals in chronological order
            
        Returns:
            List of valid pens
        """
        if len(fractals) < 2:
            return []
        
        # Step 1: Create pens from all consecutive fractals
        initial_pens = []
        self.logger.info(f"Step 1: Creating pens from {len(fractals)} fractals\n\n")
        for i in range(len(fractals) - 1):
            start_fractal = fractals[i]
            end_fractal = fractals[i + 1]
            
            pen = self.create_pen(start_fractal, end_fractal)
            if pen:
                initial_pens.append(pen)
                self.logger.debug(f"Initial pen: {pen} - Valid: {pen.is_valid}")
        
        passed_count = sum(1 for pen in initial_pens if pen.is_valid)
        self.logger.info(f"Step 1: Created {len(initial_pens)} initial pens from {len(fractals)} fractals ({passed_count} passed validation)\n\n")
        
        # Step 2: Process every 3 consecutive pens
        processed_pens = self.process_three_consecutive_pens(initial_pens)
        self.logger.info(f"Step 2: Processed into {len(processed_pens)} pens")
        
        # Step 3: Filter to only keep valid pens
        valid_pens = [pen for pen in processed_pens if pen.is_valid]
        self.logger.info(f"Step 3: Filtered to {len(valid_pens)} valid pens")
        
        self.pens = valid_pens
        self.logger.info(f"Final result: {len(valid_pens)} valid pens from {len(fractals)} fractals")
        
        return valid_pens
    
    def analyze_pen_breaking(self, pen: ChanPen, current_price: float) -> PenBreakType:
        """
        Analyze if a pen is being broken by current price
        
        Args:
            pen: The pen to analyze
            current_price: Current market price
            
        Returns:
            Type of pen breaking
        """
        if pen.direction == PenDirection.UP:
            # For upward pen, breaking means price goes below the start (low)
            if current_price < pen.low:
                # Check if it's a full break (significantly below)
                break_threshold = pen.low * 0.99  # 1% below
                if current_price < break_threshold:
                    pen.break_type = PenBreakType.FULL_BREAK
                else:
                    pen.break_type = PenBreakType.PARTIAL_BREAK
                pen.break_price = current_price
                return pen.break_type
        else:
            # For downward pen, breaking means price goes above the start (high)
            if current_price > pen.high:
                # Check if it's a full break (significantly above)
                break_threshold = pen.high * 1.01  # 1% above
                if current_price > break_threshold:
                    pen.break_type = PenBreakType.FULL_BREAK
                else:
                    pen.break_type = PenBreakType.PARTIAL_BREAK
                pen.break_price = current_price
                return pen.break_type
        
        pen.break_type = PenBreakType.NONE
        pen.break_price = None
        return PenBreakType.NONE
    
    def get_upward_pens(self) -> List[ChanPen]:
        """Get all upward pens"""
        return [pen for pen in self.pens if pen.direction == PenDirection.UP]
    
    def get_downward_pens(self) -> List[ChanPen]:
        """Get all downward pens"""
        return [pen for pen in self.pens if pen.direction == PenDirection.DOWN]
    
    def get_latest_pen(self) -> Optional[ChanPen]:
        """Get the most recent pen"""
        return self.pens[-1] if self.pens else None
    
    def get_broken_pens(self) -> List[ChanPen]:
        """Get all pens that have been broken"""
        return [pen for pen in self.pens if pen.break_type != PenBreakType.NONE]
    
    def get_valid_pens(self) -> List[ChanPen]:
        """Get all valid pens"""
        return [pen for pen in self.pens if pen.is_valid]
    
    def get_invalid_pens(self) -> List[ChanPen]:
        """Get all invalid pens"""
        return [pen for pen in self.pens if not pen.is_valid]
    
    def get_pen_sequence_validity(self) -> bool:
        """
        Check if the pen sequence is valid (alternating directions)
        
        Returns:
            True if sequence is valid
        """
        if len(self.pens) < 2:
            return True
        
        for i in range(len(self.pens) - 1):
            if self.pens[i].direction == self.pens[i + 1].direction:
                return False
        
        return True
    
    def filter_pens_by_length(self, min_length: float) -> List[ChanPen]:
        """
        Filter pens by minimum length
        
        Args:
            min_length: Minimum pen length
            
        Returns:
            List of pens meeting the length requirement
        """
        return [pen for pen in self.pens if pen.length >= min_length]
    
    def get_pen_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the pens
        
        Returns:
            Dictionary with pen statistics including validation results
        """
        if not self.pens:
            return {
                'total_pens': 0,
                'upward_pens': 0,
                'downward_pens': 0,
                'valid_pens': 0,
                'invalid_pens': 0,
                'average_length': 0.0,
                'max_length': 0.0,
                'min_length': 0.0,
                'broken_pens': 0,
                'validation_rate': 0.0
            }
        
        upward_count = len(self.get_upward_pens())
        downward_count = len(self.get_downward_pens())
        valid_count = len([pen for pen in self.pens if pen.is_valid])
        invalid_count = len([pen for pen in self.pens if not pen.is_valid])
        lengths = [pen.length for pen in self.pens]
        broken_count = len(self.get_broken_pens())
        
        return {
            'total_pens': len(self.pens),
            'upward_pens': upward_count,
            'downward_pens': downward_count,
            'valid_pens': valid_count,
            'invalid_pens': invalid_count,
            'average_length': sum(lengths) / len(lengths),
            'max_length': max(lengths),
            'min_length': min(lengths),
            'broken_pens': broken_count,
            'validation_rate': valid_count / len(self.pens) if self.pens else 0.0
        }
    
    def clear(self):
        """Clear all pens"""
        self.pens.clear()
        self.logger.debug("Cleared all pens")
    
    def get_pens(self) -> List[ChanPen]:
        """Get copy of all pens"""
        return self.pens.copy()
    
    def set_parameters(self, min_pen_length: Optional[float] = None, 
                      min_kbar_count: Optional[int] = None,
                      pen_validator: Optional['PenRuleValidator'] = None):
        """
        Set pen processing parameters
        
        Args:
            min_pen_length: Minimum pen length
            min_kbar_count: Minimum kbar count
            pen_validator: Pen rule validator
        """
        if min_pen_length is not None:
            self.min_pen_length = min_pen_length
        if min_kbar_count is not None:
            self.min_kbar_count = min_kbar_count
        if pen_validator is not None:
            self.pen_validator = pen_validator
        
        self.logger.info(f"Updated parameters: min_length={self.min_pen_length}, "
                        f"min_kbar_count={self.min_kbar_count}, "
                        f"pen_validator={'enabled' if self.pen_validator else 'disabled'}")
    
    def set_pen_validator(self, pen_validator: 'PenRuleValidator'):
        """
        Set pen rule validator
        
        Args:
            pen_validator: Pen rule validator instance
        """
        self.pen_validator = pen_validator
        self.logger.info("Pen rule validator enabled")
    
    def get_pen_validator(self) -> Optional['PenRuleValidator']:
        """
        Get current pen rule validator
        
        Returns:
            Current pen rule validator or None
        """
        return self.pen_validator
    
    def validate_pen_with_rules(self, start_fractal: Fractal, end_fractal: Fractal, 
                               pen_kbars: List['Kbar']) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate pen using pen rules validator
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            pen_kbars: Raw kbars between fractals
            
        Returns:
            Tuple of (is_valid, failed_rule_names, validation_details)
        """
        if not self.pen_validator:
            return True, [], {"message": "No pen validator configured"}
        
        is_valid, failed_rules, validation_details = self.pen_validator.validate_pen(
            start_fractal, end_fractal, pen_kbars
        )
        
        failed_rule_names = [rule.value for rule in failed_rules]
        
        return is_valid, failed_rule_names, validation_details
    
    def process_three_consecutive_pens(self, pen_list: List[ChanPen]) -> List[ChanPen]:
        """
        Process every 3 consecutive pens to create new pens
        
        For every 3 consecutive pens, create a new pen using:
        - Start fractal of pen 1
        - End fractal of pen 3
        - Validate the new pen with pen validator
        
        Args:
            pen_list: List of pens to process
            
        Returns:
            List of new pens created from 3 consecutive pens
        """
        if len(pen_list) < 3:
            return pen_list  # Not enough pens to process
        
        new_pens = []
        
        # Process every 3 consecutive pens
        for i in range(0, len(pen_list) - 2, 3):
            pen1 = pen_list[i]
            pen2 = pen_list[i + 1]
            pen3 = pen_list[i + 2]
            
            # Analyze the 3 consecutive pens using KBarRelationship
            pen_relationship = self.get_three_pens_relationship(pen1, pen2, pen3)
            self.logger.debug(f"Three pen relationship: {pen_relationship.value} - {pen_relationship.get_description()}")
            # Use pen relationship handler to analyze the three pens
            if hasattr(self, 'pen_relationship_handler') and self.pen_relationship_handler:
                relationship_result = self.pen_relationship_handler.analyze_pen_relationship(
                    pen1, pen2, pen3, pen_relationship
                )
                
                self.logger.debug(f"Pen relationship analysis: {relationship_result.relationship.value}")
                self.logger.debug(f"Can merge: {relationship_result.can_merge}")
                self.logger.debug(f"Merge recommendation: {relationship_result.merge_recommendation}")
                self.logger.debug(f"Confidence score: {relationship_result.confidence_score}")
                
                # Log special considerations
                for consideration in relationship_result.special_considerations:
                    self.logger.debug(f"Special consideration: {consideration}")
                
                # Log analysis details
                for key, value in relationship_result.analysis_details.items():
                    self.logger.debug(f"Analysis detail - {key}: {value}")
                
                # Create new pen if relationship analysis suggests it's appropriate
                if relationship_result.can_merge:
                    new_pen = self.create_pen(pen1.start_fractal, pen3.end_fractal)
                    
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
                        
                        new_pens.append(new_pen)
                        self.logger.debug(f"Created new pen from 3 consecutive pens: {new_pen}")
                        self.logger.debug(f"Relationship analysis: {relationship_result.relationship.value} - {relationship_result.merge_recommendation}")
                else:
                    self.logger.debug(f"Skipping pen creation - relationship analysis suggests not to merge: {relationship_result.merge_recommendation}")
            else:
                self.logger.warning("Pen relationship handler not available, using fallback logic")
                # Fallback to original logic if pen relationship handler is not available
                new_pen = self.create_pen(pen1.start_fractal, pen3.end_fractal)
                
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
                    
                    new_pens.append(new_pen)
                    self.logger.debug(f"Created new pen from 3 consecutive pens (fallback): {new_pen}")
            # # Create new pen from pen1's start to pen3's end
            # new_pen = self.create_pen(pen1.start_fractal, pen3.end_fractal)
            
            # if new_pen:
            #     # Add information about the source pens and their relationship
            #     new_pen.validation_details = new_pen.validation_details or {}
            #     new_pen.validation_details['source_pens'] = [
            #         f"Pen1({pen1.start_time}-{pen1.end_time})",
            #         f"Pen2({pen2.start_time}-{pen2.end_time})",
            #         f"Pen3({pen3.start_time}-{pen3.end_time})"
            #     ]
            #     new_pen.validation_details['three_pen_relationship'] = pen_relationship.value
            #     new_pen.validation_details['three_pen_relationship_description'] = pen_relationship.get_description()
                
            #     new_pens.append(new_pen)
            #     self.logger.debug(f"Created new pen from 3 consecutive pens: {new_pen}")
            #     self.logger.debug(f"Three pen relationship: {pen_relationship.value} - {pen_relationship.get_description()}")
        
        # Handle remaining pens (if pen_list length is not divisible by 3)
        remaining_start = len(pen_list) - (len(pen_list) % 3)
        if remaining_start < len(pen_list):
            remaining_pens = pen_list[remaining_start:]
            new_pens.extend(remaining_pens)
            self.logger.debug(f"Added {len(remaining_pens)} remaining pens")
        
        self.logger.info(f"Processed {len(pen_list)} pens into {len(new_pens)} new pens")
        return new_pens
    
    def get_three_pens_relationship(self, pen1: ChanPen, pen2: ChanPen, pen3: ChanPen) -> KBarRelationship:
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
        # Use pen1's low and high as kbar1 (d1, g1)
        d1 = pen1.low   # Low of pen1
        g1 = pen1.high  # High of pen1
        
        # Use pen3's low and high as kbar2 (d2, g2)
        d2 = pen3.low   # Low of pen3
        g2 = pen3.high  # High of pen3
        
        # Get the relationship using KBarRelationship
        relationship = KBarRelationship.determine_relationship(d1, g1, d2, g2)
        
        self.logger.debug(f"\n\nThree pen relationship analysis:")
        self.logger.debug(f"{pen1}")
        self.logger.debug(f"{pen2}")
        self.logger.debug(f"{pen3}")
        self.logger.debug(f"  Relationship: {relationship.value} - {relationship.get_description()}")
        
        return relationship 