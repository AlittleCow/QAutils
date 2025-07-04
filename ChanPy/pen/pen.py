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
from ..fractal import Fractal, FractalType, get_kbars_between_fractals
from ..mergekbar import MergedKbar
from ..chantypes import KBarRelationship
from .pentypes import ChanPen, PenDirection, PenBreakType
from .penrelationship import PenRelationshipHandler, PenDispatchResult, get_three_pens_relationship
from .penrules import PenRuleValidator
from .penutils import create_pen
from ..line.lineutils import create_line_from_pen
from datetime import datetime

if TYPE_CHECKING:
    from ..chan import Kbar
    from ..context import ChanContext
    from ..line import ChanLine


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
        self.pen_relationship_handler: Optional[PenRelationshipHandler] = PenRelationshipHandler(
            context=context, pen_processor=self)

    def set_context(self, context: 'ChanContext'):
        """
        Set the ChanContext for the pen processor
        
        Args:
            context: ChanContext instance
        """
        self.context = context
        if self.pen_relationship_handler:
            self.pen_relationship_handler.set_context(context)
            self.pen_relationship_handler.set_pen_processor(self)
        
        # Also set context for pen validator if it exists
        if self.pen_validator:
            self.pen_validator.set_context(context)
        
        self.logger.debug("ChanContext set for pen processor")
    
    def set_raw_kbars(self, kbars: List['Kbar']):
        """
        Set the raw kbar data for pen validation
        
        Args:
            kbars: List of raw kbars in chronological order
        """
        self.raw_kbars = kbars
        self.logger.debug(f"Set {len(kbars)} raw kbars for pen validation")
        
        # Also set raw kbars for pen validator if it exists
        if self.pen_validator:
            self.pen_validator.set_raw_kbars(kbars)
    
    def validate_pen(self, pen: ChanPen) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate a pen using configured validation rules
        
        Args:
            pen: The pen to validate
            
        Returns:
            Tuple of (is_valid, failed_rules, validation_details)
        """
        is_valid = True
        failed_rules = []
        validation_details = {}
        
        # Basic validation checks
        if pen.length < self.min_pen_length:
            is_valid = False
            failed_rules.append("min_pen_length")
        
        if len(pen.raw_kbars) < self.min_kbar_count:
            is_valid = False
            failed_rules.append("min_kbar_count")
        
        # Validate with raw kbars using pen validator if available
        if self.pen_validator:
            # Use pen validator's raw kbar validation method
            if not self.pen_validator.validate_pen_with_raw_kbars(pen.start_fractal, pen.end_fractal, pen.raw_kbars):
                is_valid = False
                failed_rules.append("raw_kbar_validation")
        else:
            # Fallback to basic validation (no raw kbar validation)
            self.logger.warning("No pen validator available - skipping raw kbar validation")
        
        # Advanced pen validation using pen rules (if validator is provided)
        if self.pen_validator:
            rule_valid, rule_failed_rules, rule_validation_details = self.pen_validator.validate_pen(
                pen.start_fractal, pen.end_fractal, pen.raw_kbars
            )
            
            if not rule_valid:
                is_valid = False
                failed_rules.extend([rule.value for rule in rule_failed_rules])
                validation_details.update(rule_validation_details)
                self.logger.debug(f"FAILED  - Pen validation failed: {[rule.value for rule in rule_failed_rules]}")
            else:
                is_valid = True
                validation_details.update(rule_validation_details)
                self.logger.info(f"PASSED  - Pen validation passed: {rule_validation_details.get('passed_rules', 0)}/{rule_validation_details.get('total_rules', 0)} rules")
        
        return is_valid, failed_rules, validation_details
    
    def create_validate_pen(self, start_fractal: Fractal, end_fractal: Fractal) -> Optional[ChanPen]:
        """
        Create a pen from two fractals with validation
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            
        Returns:
            ChanPen object with validation results stored
        """
        # Create pen using utility function
        pen = create_pen(start_fractal, end_fractal, self.context)
        
        if pen is None:
            return None
        
        # Validate the pen
        is_valid, failed_rules, validation_details = self.validate_pen(pen)
        
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
            self.logger.debug(f"\n")
            self.logger.debug(f"🖊️ Creating pen from {start_fractal} to {end_fractal}")
            pen = self.create_validate_pen(start_fractal, end_fractal)
            if pen:
                initial_pens.append(pen)
                self.logger.debug(f"Initial pen: {pen} - Valid: {pen.is_valid}")
        
        passed_count = sum(1 for pen in initial_pens if pen.is_valid)
        self.logger.info(f"📊 Step 1: Created {len(initial_pens)} valid/invalid initial pens from {len(fractals)} fractals ({passed_count} passed validation)\n\n")
        # Step 2: Process every 3 consecutive pens
        processed_pens = self.process_three_consecutive_pens(initial_pens)
        self.logger.info(f"Step 2: Processed {len(processed_pens)} pens with pen shape")
        self.logger.debug(f"\n")
        
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
        
        # Set raw kbars and context for the validator
        if self.raw_kbars:
            pen_validator.set_raw_kbars(self.raw_kbars)
        if self.context:
            pen_validator.set_context(self.context)
        
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
        for current_pen_index in range(0, len(pen_list) - 2, 3):
            pen1 = pen_list[current_pen_index]
            pen2 = pen_list[current_pen_index + 1]
            pen3 = pen_list[current_pen_index + 2]
            self.logger.debug(f"---------->\n")
            self.logger.debug(f"🖊️ Processing 3 consecutive pens")
            self.logger.debug(f"🖊️ Pen 1: {pen1}")
            self.logger.debug(f"🖊️ Pen 2: {pen2}")
            self.logger.debug(f"🖊️ Pen 3: {pen3}")

            # Analyze the 3 consecutive pens using KBarRelationship
            pen_relationship = get_three_pens_relationship(pen1, pen2, pen3)
            self.logger.debug(f"Three pen relationship: {pen_relationship.value} - {pen_relationship.get_description()}")
            # Use pen relationship handler to analyze the three pens
            if hasattr(self, 'pen_relationship_handler') and self.pen_relationship_handler:
                relationship_result = self.pen_relationship_handler.analyze_pen_relationship(
                    pen1, pen2, pen3, pen_relationship
                )

                # Dispatch the relationship processing using the new dispatch method
                dispatch_result = self.pen_relationship_handler.dispatch_pen_relationship(
                    pen1, pen2, pen3, 
                    relationship_result, 
                    pen_relationship,
                    pen_list,
                    current_pen_index
                )

                # Handle the dispatch result
                if dispatch_result.success:
                    # Add new pens from the dispatch result
                    new_pens.extend(dispatch_result.new_pens)
                    
                    # Add pens to continue processing
                    new_pens.extend(dispatch_result.pens_to_continue)
                    
                    self.logger.debug(f"Dispatch successful: {dispatch_result.action}")
                    self.logger.debug(f"Added {len(dispatch_result.new_pens)} new pens")
                    self.logger.debug(f"Added {len(dispatch_result.pens_to_continue)} pens to continue")
                    
                    if dispatch_result.global_line_created:
                        self.logger.info("Global line created during dispatch")
                        
                else:
                    self.logger.error(f"FAILED  - Dispatch failed: {dispatch_result.error_message}")
                    # Fallback: add all three pens
                    new_pens.extend([pen1, pen2, pen3])
            
            else:
                self.logger.error("Pen relationship handler not available, using fallback logic")
                raise ValueError("Pen relationship handler not available")
        
        # Handle remaining pens (if pen_list length is not divisible by 3)
        remaining_start = len(pen_list) - (len(pen_list) % 3)
        if remaining_start < len(pen_list):
            remaining_pens = pen_list[remaining_start:]
            new_pens.extend(remaining_pens)
            self.logger.debug(f"Added {len(remaining_pens)} remaining pens")
        
        self.logger.info(f"Processed {len(pen_list)} pens into {len(new_pens)} new pens")
        return new_pens
    
    def add_line_as_global_line(self, line: 'ChanLine') -> bool:
        """
        Add a line as the first global line using Chan context
        
        Args:
            line: The line to add as global line
            
        Returns:
            True if successful, False otherwise
        """
        if not line or not self.context:
            self.logger.warning("Cannot add global line: missing line or context")
            return False
        
        try:
            # Use the new incremental update method for adding global lines
            success = self.context.add_line_as_global_line_incrementally(
                line,
                save_to_db=True  # Save to database
            )
            
            if success:
                self.logger.info(f"Added global line to context: {line.direction.name} "
                               f"from {line.start_time} to {line.end_time}")
                return True
            else:
                self.logger.error("Failed to add global line to context")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to add global line to context: {str(e)}")
            return False
    
    def create_and_add_global_line_from_pen(self, pen: ChanPen) -> bool:
        """
        Create a line from a pen and add it as the first global line
        
        This is a convenience method that creates a line from a pen
        and adds it as a global line using the context.
        
        Args:
            pen: The pen to create a line from
            
        Returns:
            True if successful, False otherwise
        """        
        # Mark the pen as valid before creating line from it
        if pen:
            pen.is_valid = True
        else:
            raise ValueError("Cannot create line from invalid pen")
        
        # Create line from pen using the standalone helper function
        line = create_line_from_pen(pen)
        
        # Add the line as global line
        if line:
            return self.add_line_as_global_line(line)
        return False 