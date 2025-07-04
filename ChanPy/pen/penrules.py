"""
Pen Rules Module for Chan Theory (缠中说禅)

This module implements the comprehensive pen formation and validation rules
according to Chan Zhongshuochan's theory. It provides strict validation
criteria for pen formation, breaking analysis, and quality assessment.

Chan Theory Pen Rules:
1. Pen Formation Rules - Basic requirements for valid pen formation
2. Fractal Validation - Ensure proper fractal connections
3. Kbar Validation - Validate pen against underlying kbar data
4. Direction Consistency - Maintain proper directional flow
5. Length Requirements - Minimum pen length and strength criteria
6. Breaking Analysis - Detect pen breaking patterns
7. Quality Assessment - Evaluate pen reliability and strength
"""

import logging
from typing import List, Optional, Dict, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from ..fractal import Fractal, FractalType, get_kbars_between_fractals
from ..chantypes import KBarRelationship
from .pentypes import ChanPen, PenDirection, PenBreakType

if TYPE_CHECKING:
    from ..chan import Kbar
    from ..context import ChanContext


class PenValidationResult(Enum):
    """Pen validation result enumeration"""
    VALID = "valid"
    INVALID_FRACTAL_TYPE = "invalid_fractal_type"
    INVALID_DIRECTION = "invalid_direction"
    INSUFFICIENT_KBARS = "insufficient_kbars"
    INVALID_LENGTH = "invalid_length"
    INVALID_TREND = "invalid_trend"
    INVALID_MACD = "invalid_macd"
    INVALID_VOLUME = "invalid_volume"


class PenQuality(Enum):
    """Pen quality enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class PenValidationConfig:
    """Configuration for pen validation rules"""
    min_kbar_count: int = 5
    min_pen_length: float = 0.0
    min_pen_length_ratio: float = 0.001  # Minimum 0.1% of price
    require_macd_validation: bool = True
    require_volume_validation: bool = False
    allow_same_fractal_type: bool = False
    max_pen_kbar_count: int = 1000
    min_fractal_strength: int = 3
    require_trend_consistency: bool = True
    breaking_threshold: float = 0.01  # 1% breaking threshold


class PenRule(ABC):
    """Abstract base class for pen validation rules"""
    
    @abstractmethod
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate pen according to specific rule
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            pen_kbars: Kbars between fractals
            config: Validation configuration
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def get_rule_name(self) -> str:
        """Get rule name"""
        pass


class FractalTypeRule(PenRule):
    """Rule 1: Validate fractal types are different"""
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """Validate that start and end fractals are of different types"""
        if not config.allow_same_fractal_type:
            if start_fractal.fractal_type == end_fractal.fractal_type:
                return PenValidationResult.INVALID_FRACTAL_TYPE
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        return "FractalTypeRule"


class DirectionConsistencyRule(PenRule):
    """Rule 2: Validate pen direction consistency"""
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """Validate pen direction matches fractal types"""
        if start_fractal.fractal_type == FractalType.BOTTOM:
            # Should be upward pen
            if end_fractal.price <= start_fractal.price:
                return PenValidationResult.INVALID_DIRECTION
        else:
            # Should be downward pen
            if end_fractal.price >= start_fractal.price:
                return PenValidationResult.INVALID_DIRECTION
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        return "DirectionConsistencyRule"


class KbarCountRule(PenRule):
    """Rule 3: Validate minimum kbar count"""
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """Validate minimum kbar count requirement"""
        if len(pen_kbars) < config.min_kbar_count:
            return PenValidationResult.INSUFFICIENT_KBARS
        if len(pen_kbars) > config.max_pen_kbar_count:
            return PenValidationResult.INSUFFICIENT_KBARS
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        return "KbarCountRule"


class PenLengthRule(PenRule):
    """Rule 4: Validate pen length requirements"""
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """Validate pen length meets minimum requirements"""
        pen_length = abs(end_fractal.price - start_fractal.price)
        
        # Absolute length check
        if pen_length < config.min_pen_length:
            return PenValidationResult.INVALID_LENGTH
        
        # Relative length check (percentage of price)
        avg_price = (start_fractal.price + end_fractal.price) / 2
        length_ratio = pen_length / avg_price
        if length_ratio < config.min_pen_length_ratio:
            return PenValidationResult.INVALID_LENGTH
        
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        return "PenLengthRule"


class TrendConsistencyRule(PenRule):
    """Rule 5: Validate trend consistency throughout pen"""
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """Validate trend consistency in pen kbars"""
        if not config.require_trend_consistency or not pen_kbars:
            return PenValidationResult.VALID
        
        if start_fractal.fractal_type == FractalType.BOTTOM:
            # Upward pen - no kbar low should break below start
            start_low = start_fractal.price
            for kbar in pen_kbars:
                if kbar.low < start_low * (1 - config.breaking_threshold):
                    return PenValidationResult.INVALID_TREND
        else:
            # Downward pen - no kbar high should break above start
            start_high = start_fractal.price
            for kbar in pen_kbars:
                if kbar.high > start_high * (1 + config.breaking_threshold):
                    return PenValidationResult.INVALID_TREND
        
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        return "TrendConsistencyRule"


class MACDValidationRule(PenRule):
    """Rule 6: Validate MACD consistency (if enabled)"""
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """Validate MACD trend consistency"""
        if not config.require_macd_validation:
            return PenValidationResult.VALID
        
        # This would require MACD calculation implementation
        # For now, return valid - can be implemented later
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        return "MACDValidationRule"


class VolumeValidationRule(PenRule):
    """Rule 7: Validate volume patterns (if enabled)"""
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """Validate volume patterns in pen"""
        if not config.require_volume_validation:
            return PenValidationResult.VALID
        
        # This would require volume analysis implementation
        # For now, return valid - can be implemented later
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        return "VolumeValidationRule"


class PenRuleValidator:
    """
    Comprehensive pen rule validator
    
    Implements all Chan theory pen validation rules and provides
    detailed validation results and quality assessment.
    """
    
    def __init__(self, config: Optional[PenValidationConfig] = None):
        """
        Initialize pen rule validator
        
        Args:
            config: Validation configuration
        """
        self.logger = logging.getLogger(f"{__name__}.PenRuleValidator")
        self.config = config or PenValidationConfig()
        self.raw_kbars: List['Kbar'] = []
        self.context: Optional['ChanContext'] = None
        
        # Initialize all validation rules
        self.rules: List[PenRule] = [
            FractalTypeRule(),
            DirectionConsistencyRule(),
            KbarCountRule(),
            PenLengthRule(),
            TrendConsistencyRule(),
            MACDValidationRule(),
            VolumeValidationRule()
        ]
        
        self.logger.info(f"Initialized PenRuleValidator with {len(self.rules)} rules")
    
    def set_raw_kbars(self, kbars: List['Kbar']):
        """
        Set the raw kbar data for pen validation
        
        Args:
            kbars: List of raw kbars in chronological order
        """
        self.raw_kbars = kbars
        self.logger.debug(f"Set {len(kbars)} raw kbars for pen validation")
    
    def set_context(self, context: 'ChanContext'):
        """
        Set the ChanContext for the pen validator
        
        Args:
            context: ChanContext instance
        """
        self.context = context
        self.logger.debug("ChanContext set for pen validator")
    
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
        pen_kbars = []
        
        if self.context:
            # Use context to get kbars between fractals
            pen_kbars = get_kbars_between_fractals(start_fractal, end_fractal, self.context)
        else:
            raise ValueError("ChanContext not set for pen validation")
        
        if len(pen_kbars) < self.config.min_kbar_count:
            return False
        
        # Validate pen direction consistency
        if start_fractal.fractal_type == FractalType.BOTTOM:
            # Should be an upward pen
            return self._validate_upward_pen(start_fractal, end_fractal, pen_kbars)
        else:
            # Should be a downward pen
            return self._validate_downward_pen(start_fractal, end_fractal, pen_kbars)
    
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
    
    def validate_pen(self, start_fractal: Fractal, end_fractal: Fractal, 
                    pen_kbars: List['Kbar']) -> Tuple[bool, List[PenValidationResult], Dict[str, Any]]:
        """
        Validate pen against all rules
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            pen_kbars: Kbars between fractals
            
        Returns:
            Tuple of (is_valid, failed_rules, validation_details)
        """
        failed_rules = []
        validation_details = {
            'total_rules': len(self.rules),
            'passed_rules': 0,
            'failed_rules': 0,
            'rule_results': {}
        }
        
        self.logger.debug(f"Validating pen:\nstart_fractal={start_fractal}\n  end_fractal={end_fractal}")

        for rule in self.rules:
            try:
                result = rule.validate(start_fractal, end_fractal, pen_kbars, self.config)
                rule_name = rule.get_rule_name()
                
                if result == PenValidationResult.VALID:
                    validation_details['passed_rules'] += 1
                    validation_details['rule_results'][rule_name] = 'PASSED'
                else:
                    failed_rules.append(result)
                    validation_details['failed_rules'] += 1
                    validation_details['rule_results'][rule_name] = result.value
                    
            except Exception as e:
                self.logger.error(f"Error validating rule {rule.get_rule_name()}: {e}")
                failed_rules.append(PenValidationResult.INVALID_TREND)
                validation_details['failed_rules'] += 1
                validation_details['rule_results'][rule.get_rule_name()] = f'ERROR: {str(e)}'
        
        is_valid = len(failed_rules) == 0
        
        if is_valid:
            self.logger.info(f"Pen validation: PASSED "
                           f"({validation_details['passed_rules']}/{validation_details['total_rules']} rules passed)")
        else:
            self.logger.debug(f"Pen validation: FAILED "
                            f"({validation_details['passed_rules']}/{validation_details['total_rules']} rules passed)")
        
        return is_valid, failed_rules, validation_details
    

    def analyze_pen_breaking(self, pen: ChanPen, current_price: float, 
                           current_kbars: List['Kbar']) -> Dict[str, Any]:
        """
        Analyze pen breaking patterns
        
        Args:
            pen: Pen to analyze
            current_price: Current market price
            current_kbars: Recent kbars for analysis
            
        Returns:
            Breaking analysis results
        """
        breaking_analysis = {
            'is_breaking': False,
            'break_type': PenBreakType.NONE,
            'break_strength': 0.0,
            'break_confirmation': False,
            'break_price': current_price,
            'support_resistance_level': 0.0
        }
        
        if pen.direction == PenDirection.UP:
            # Upward pen breaking analysis
            support_level = pen.low
            breaking_analysis['support_resistance_level'] = support_level
            
            if current_price < support_level:
                breaking_analysis['is_breaking'] = True
                break_strength = (support_level - current_price) / support_level
                breaking_analysis['break_strength'] = break_strength
                
                if break_strength > self.config.breaking_threshold * 2:
                    breaking_analysis['break_type'] = PenBreakType.FULL_BREAK
                else:
                    breaking_analysis['break_type'] = PenBreakType.PARTIAL_BREAK
                
                # Check for confirmation with multiple kbars
                if len(current_kbars) >= 2:
                    recent_closes = [kbar.close for kbar in current_kbars[-2:]]
                    if all(close < support_level for close in recent_closes):
                        breaking_analysis['break_confirmation'] = True
        
        else:
            # Downward pen breaking analysis
            resistance_level = pen.high
            breaking_analysis['support_resistance_level'] = resistance_level
            
            if current_price > resistance_level:
                breaking_analysis['is_breaking'] = True
                break_strength = (current_price - resistance_level) / resistance_level
                breaking_analysis['break_strength'] = break_strength
                
                if break_strength > self.config.breaking_threshold * 2:
                    breaking_analysis['break_type'] = PenBreakType.FULL_BREAK
                else:
                    breaking_analysis['break_type'] = PenBreakType.PARTIAL_BREAK
                
                # Check for confirmation with multiple kbars
                if len(current_kbars) >= 2:
                    recent_closes = [kbar.close for kbar in current_kbars[-2:]]
                    if all(close > resistance_level for close in recent_closes):
                        breaking_analysis['break_confirmation'] = True
        
        return breaking_analysis
    
    def get_pen_formation_rules(self) -> List[str]:
        """
        Get list of pen formation rules
        
        Returns:
            List of rule descriptions
        """
        return [
            "1. Fractal Type Rule: Start and end fractals must be of different types",
            "2. Direction Consistency Rule: Pen direction must match fractal types",
            "3. Kbar Count Rule: Minimum number of kbars required between fractals",
            "4. Pen Length Rule: Minimum absolute and relative pen length",
            "5. Trend Consistency Rule: No significant trend violations in pen kbars",
            "6. MACD Validation Rule: MACD should support pen direction (if enabled)",
            "7. Volume Validation Rule: Volume patterns should support pen (if enabled)"
        ]
    
    def update_config(self, **kwargs):
        """
        Update validation configuration
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown config parameter: {key}")
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics
        
        Returns:
            Dictionary with validation statistics
        """
        return {
            'total_rules': len(self.rules),
            'rule_names': [rule.get_rule_name() for rule in self.rules],
            'config': {
                'min_kbar_count': self.config.min_kbar_count,
                'min_pen_length': self.config.min_pen_length,
                'min_pen_length_ratio': self.config.min_pen_length_ratio,
                'require_macd_validation': self.config.require_macd_validation,
                'require_volume_validation': self.config.require_volume_validation,
                'breaking_threshold': self.config.breaking_threshold
            }
        }


# Factory function for easy instantiation
def create_pen_validator(min_kbar_count: int = 5,
                        min_pen_length: float = 0.0,
                        min_pen_length_ratio: float = 0.001,
                        require_macd_validation: bool = False,
                        require_volume_validation: bool = False) -> PenRuleValidator:
    """
    Create a pen rule validator with custom configuration
    
    Args:
        min_kbar_count: Minimum kbar count
        min_pen_length: Minimum pen length
        min_pen_length_ratio: Minimum pen length ratio
        require_macd_validation: Enable MACD validation
        require_volume_validation: Enable volume validation
        
    Returns:
        Configured PenRuleValidator instance
    """
    config = PenValidationConfig(
        min_kbar_count=min_kbar_count,
        min_pen_length=min_pen_length,
        min_pen_length_ratio=min_pen_length_ratio,
        require_macd_validation=require_macd_validation,
        require_volume_validation=require_volume_validation
    )
    
    return PenRuleValidator(config) 