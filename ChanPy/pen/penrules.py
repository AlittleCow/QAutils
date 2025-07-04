"""
Pen Rules Module for Chan Theory (缠中说禅)

This module implements the comprehensive pen formation and validation rules
according to Chan Zhongshuochan's theory. It provides strict validation
criteria for pen formation, breaking analysis, and quality assessment.

Chan Theory Pen Rules Implementation:
1. Pen Formation Rules - Basic requirements for valid pen formation
2. Fractal Validation - Ensure proper fractal connections
3. Kbar Validation - Validate pen against underlying kbar data
4. Direction Consistency - Maintain proper directional flow
5. Length Requirements - Minimum pen length and strength criteria
6. Breaking Analysis - Detect pen breaking patterns
7. Quality Assessment - Evaluate pen reliability and strength

Implements the following Chan Theory Pen Standards (笔的定义):
Standard 1: 一笔必须至少有5根K线 (A pen must have at least 5 K-lines)
Standard 2: 顶分型和底分型绝对不能共用同一根K线 (Top and bottom fractals cannot share the same K-line)
Standard 3: 若没有构造出一个向上笔时，行情再次新低，则从新低的K线处重新开始构造 (Pen construction restart logic - implemented in pen construction algorithm)
Standard 4: 顶不能在底里，底不能在顶里 (Top cannot be inside bottom, bottom cannot be inside top)
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
    INVALID_FRACTAL_SEPARATION = "invalid_fractal_separation"
    INVALID_FRACTAL_LEVEL_RELATION = "invalid_fractal_level_relation"


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
    
    def __init__(self):
        """Initialize the pen rule with logger"""
        import logging
        self.logger = logging.getLogger(self.__class__.__name__)
    
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
    """
    Rule 1: Validate fractal types are different (Partial Standard 2)
    
    This rule ensures that the starting and ending fractals of a pen are of different
    types. A valid pen must connect a bottom fractal to a top fractal (upward pen) or
    a top fractal to a bottom fractal (downward pen). This is a fundamental requirement
    for pen formation in Chan theory.
    
    The rule can be configured to allow same fractal types through the configuration
    parameter, but this is generally not recommended for strict Chan theory compliance.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate that start and end fractals are of different types
        
        This method checks that the starting and ending fractals have different types,
        which is essential for proper pen formation. Same-type fractals would indicate
        an invalid pen structure that doesn't follow Chan theory principles.
        
        Args:
            start_fractal: The starting fractal of the pen
            end_fractal: The ending fractal of the pen
            pen_kbars: List of kbars between fractals (not used in this rule)
            config: Configuration containing fractal type validation settings
            
        Returns:
            PenValidationResult.VALID if fractal types are different,
            PenValidationResult.INVALID_FRACTAL_TYPE if they are the same
        """
        if not config.allow_same_fractal_type:
            if start_fractal.fractal_type == end_fractal.fractal_type:
                self.logger.debug(f"Fractal type validation failed: both fractals are {start_fractal.fractal_type}")
                self.logger.debug(f"Start fractal: {start_fractal}")
                self.logger.debug(f"End fractal: {end_fractal}")
                return PenValidationResult.INVALID_FRACTAL_TYPE
        
        self.logger.debug(f"Fractal type validation passed: {start_fractal.fractal_type} -> {end_fractal.fractal_type}")
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the FractalTypeRule
        """
        return "FractalTypeRule"


class DirectionConsistencyRule(PenRule):
    """
    Rule 2: Validate pen direction consistency (Supporting Standard 1)
    
    This rule ensures that the direction of the pen matches the types of the starting
    and ending fractals. For a bottom-to-top pen (upward), the ending price must be
    higher than the starting price. For a top-to-bottom pen (downward), the ending
    price must be lower than the starting price.
    
    This validation prevents the creation of pens where the price movement contradicts
    the fractal type relationship, which would violate fundamental Chan theory principles.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate pen direction matches fractal types
        
        This method checks that the price movement direction is consistent with the
        fractal types. A bottom fractal should lead to higher prices (upward pen),
        and a top fractal should lead to lower prices (downward pen).
        
        Args:
            start_fractal: The starting fractal that defines the pen's beginning
            end_fractal: The ending fractal that defines the pen's end
            pen_kbars: List of kbars between fractals (not used in this rule)
            config: Configuration settings (not used in this rule)
            
        Returns:
            PenValidationResult.VALID if direction is consistent with fractal types,
            PenValidationResult.INVALID_DIRECTION if direction contradicts fractal types
        """
        if start_fractal.fractal_type == FractalType.BOTTOM:
            # Should be upward pen - ending price should be higher than starting price
            if end_fractal.price <= start_fractal.price:
                self.logger.debug(f"Direction validation failed for upward pen: end_price={end_fractal.price} <= start_price={start_fractal.price}")
                self.logger.debug(f"Start fractal (BOTTOM): {start_fractal}")
                self.logger.debug(f"End fractal (should be TOP): {end_fractal}")
                return PenValidationResult.INVALID_DIRECTION
        else:
            # Should be downward pen - ending price should be lower than starting price
            if end_fractal.price >= start_fractal.price:
                self.logger.debug(f"Direction validation failed for downward pen: end_price={end_fractal.price} >= start_price={start_fractal.price}")
                self.logger.debug(f"Start fractal (TOP): {start_fractal}")
                self.logger.debug(f"End fractal (should be BOTTOM): {end_fractal}")
                return PenValidationResult.INVALID_DIRECTION
        
        direction = "upward" if start_fractal.fractal_type == FractalType.BOTTOM else "downward"
        self.logger.debug(f"Direction validation passed: {direction} pen from {start_fractal.price} to {end_fractal.price}")
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the DirectionConsistencyRule
        """
        return "DirectionConsistencyRule"


class KbarCountRule(PenRule):
    """
    Rule 3: Validate minimum kbar count (Standard 1: 一笔必须至少有5根K线)
    
    This rule implements the fundamental Chan theory requirement that a pen must
    contain at least 5 K-lines. This ensures that the pen has sufficient price
    action to be considered meaningful and reduces noise from very short-term
    price movements.
    
    The rule also enforces a maximum kbar count to prevent excessively long pens
    that might span multiple market cycles and lose their analytical value.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate minimum kbar count requirement
        
        This method checks that the number of kbars between the starting and ending
        fractals meets the minimum requirement of 5 K-lines as specified in Chan theory.
        It also ensures the pen doesn't exceed the maximum allowed length.
        
        Args:
            start_fractal: The starting fractal of the pen
            end_fractal: The ending fractal of the pen
            pen_kbars: List of kbars between the start and end fractals
            config: Configuration containing kbar count limits
            
        Returns:
            PenValidationResult.VALID if kbar count is within acceptable range,
            PenValidationResult.INSUFFICIENT_KBARS if count is too low or too high
        """
        kbar_count = len(pen_kbars)
        
        if kbar_count < config.min_kbar_count:
            self.logger.debug(f"Start fractal: {start_fractal}")
            self.logger.debug(f"End fractal  : {end_fractal}")
            self.logger.debug(f"Pen kbars count: {kbar_count}")
            self.logger.debug(f"Kbar count validation failed: {kbar_count} < min_required={config.min_kbar_count}")
            return PenValidationResult.INSUFFICIENT_KBARS
        
        if kbar_count > config.max_pen_kbar_count:
            self.logger.debug(f"Start fractal: {start_fractal}")
            self.logger.debug(f"End fractal  : {end_fractal}")
            self.logger.debug(f"Pen kbars count: {kbar_count}")
            self.logger.debug(f"Kbar count validation failed: {kbar_count} > max_allowed={config.max_pen_kbar_count}")
            return PenValidationResult.INSUFFICIENT_KBARS
        
        self.logger.debug(f"Kbar count validation passed: {kbar_count} kbars (min={config.min_kbar_count}, max={config.max_pen_kbar_count})")
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the KbarCountRule
        """
        return "KbarCountRule"


class PenLengthRule(PenRule):
    """
    Rule 4: Validate pen length requirements
    
    This rule ensures that a pen meets minimum length requirements both in absolute
    terms and as a percentage of the price level. This prevents the creation of
    insignificant pens that might be caused by minor price fluctuations or market noise.
    
    The rule validates both absolute price difference and relative percentage change
    to ensure the pen represents a meaningful price movement worthy of analysis.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate pen length meets minimum requirements
        
        This method checks that the price difference between the starting and ending
        fractals meets both absolute and relative minimum thresholds. This ensures
        that only meaningful price movements are considered valid pens.
        
        Args:
            start_fractal: The starting fractal of the pen
            end_fractal: The ending fractal of the pen
            pen_kbars: List of kbars between fractals (not used in this rule)
            config: Configuration containing length requirements
            
        Returns:
            PenValidationResult.VALID if pen length meets requirements,
            PenValidationResult.INVALID_LENGTH if length is insufficient
        """
        pen_length = abs(end_fractal.price - start_fractal.price)
        
        # Absolute length check
        if pen_length < config.min_pen_length:
            self.logger.debug(f"Absolute price difference: {pen_length}")
            self.logger.debug(f"Pen length validation failed (absolute): {pen_length} < min_required={config.min_pen_length}")
            return PenValidationResult.INVALID_LENGTH
        
        # Relative length check (percentage of price)
        avg_price = (start_fractal.price + end_fractal.price) / 2
        length_ratio = pen_length / avg_price
        if length_ratio < config.min_pen_length_ratio:
            self.logger.debug(f"Absolute price difference: {pen_length}")
            self.logger.debug(f"Average price: {avg_price}")
            self.logger.debug(f"Length ratio: {length_ratio:.6f}")
            self.logger.debug(f"Pen length validation failed (relative): {length_ratio:.6f} < min_required={config.min_pen_length_ratio}")
            return PenValidationResult.INVALID_LENGTH
        
        self.logger.debug(f"Pen length validation passed: absolute={pen_length}, relative={length_ratio:.6f} (min_abs={config.min_pen_length}, min_rel={config.min_pen_length_ratio})")
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the PenLengthRule
        """
        return "PenLengthRule"


class TrendConsistencyRule(PenRule):
    """
    Rule 5: Validate trend consistency throughout pen
    
    This rule ensures that the price movement within a pen maintains consistent
    directional behavior relative to the starting fractal. For upward pens (starting
    from a bottom fractal), no kbar should break significantly below the starting
    price. For downward pens (starting from a top fractal), no kbar should break
    significantly above the starting price.
    
    The rule uses a configurable breaking threshold to allow for minor price
    fluctuations while preventing significant trend violations that would invalidate
    the pen's directional integrity.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate trend consistency in pen kbars
        
        This method checks that all kbars within the pen maintain the expected
        directional trend relative to the starting fractal. It prevents pens from
        being created when there are significant price movements that contradict
        the intended direction of the pen.
        
        Args:
            start_fractal: The starting fractal that defines the pen's beginning
            end_fractal: The ending fractal that defines the pen's end
            pen_kbars: List of kbars between the start and end fractals
            config: Configuration containing trend consistency settings
            
        Returns:
            PenValidationResult.VALID if trend is consistent throughout the pen,
            PenValidationResult.INVALID_TREND if any kbar violates the trend
        """
        if not config.require_trend_consistency or not pen_kbars:
            return PenValidationResult.VALID
        
        if start_fractal.fractal_type == FractalType.BOTTOM:
            # Upward pen - no kbar low should break below start
            # For upward pens starting from a bottom fractal, we expect the price
            # to generally move upward. If any kbar's low breaks significantly
            # below the starting price, it indicates a trend violation.
            start_low = start_fractal.price
            for kbar in pen_kbars:
                if kbar.low < start_low * (1 - config.breaking_threshold):
                    self.logger.debug(f"Trend violation detected: kbar.low={kbar.low} < start_low={start_low} * (1 - {config.breaking_threshold}) = {start_low * (1 - config.breaking_threshold)}")
                    self.logger.debug(f"Violating kbar: {kbar}")
                    return PenValidationResult.INVALID_TREND
        else:
            # Downward pen - no kbar high should break above start
            # For downward pens starting from a top fractal, we expect the price
            # to generally move downward. If any kbar's high breaks significantly
            # above the starting price, it indicates a trend violation.
            start_high = start_fractal.price
            for kbar in pen_kbars:
                if kbar.high > start_high * (1 + config.breaking_threshold):
                    self.logger.debug(f"Trend violation detected: kbar.high={kbar.high} > start_high={start_high} * (1 + {config.breaking_threshold}) = {start_high * (1 + config.breaking_threshold)}")
                    self.logger.debug(f"Violating kbar: {kbar}")
                    return PenValidationResult.INVALID_TREND
        
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the TrendConsistencyRule
        """
        return "TrendConsistencyRule"


class MACDValidationRule(PenRule):
    """
    Rule 6: Validate MACD consistency (if enabled)
    
    This rule validates that the MACD (Moving Average Convergence Divergence) indicator
    supports the direction of the pen. When enabled, this rule ensures that the MACD
    trend aligns with the pen direction, providing additional confirmation of the
    price movement's validity.
    
    Currently, this rule is a placeholder for future MACD implementation and returns
    VALID by default when MACD validation is disabled.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate MACD trend consistency
        
        This method would check that the MACD indicator supports the pen direction.
        For upward pens, MACD should show bullish signals, and for downward pens,
        MACD should show bearish signals. Currently returns VALID as a placeholder.
        
        Args:
            start_fractal: The starting fractal of the pen
            end_fractal: The ending fractal of the pen
            pen_kbars: List of kbars between fractals (would be used for MACD calculation)
            config: Configuration containing MACD validation settings
            
        Returns:
            PenValidationResult.VALID (placeholder implementation)
        """
        if not config.require_macd_validation:
            self.logger.debug("MACD validation skipped (disabled in config)")
            return PenValidationResult.VALID
        
        # This would require MACD calculation implementation
        # For now, return valid - can be implemented later
        self.logger.debug("MACD validation passed (placeholder implementation)")
        self.logger.debug(f"Pen kbars count: {len(pen_kbars)}")
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the MACDValidationRule
        """
        return "MACDValidationRule"


class VolumeValidationRule(PenRule):
    """
    Rule 7: Validate volume patterns (if enabled)
    
    This rule validates that the volume patterns within the pen support the price
    movement direction. When enabled, this rule ensures that volume characteristics
    align with the pen direction, providing additional confirmation of the price
    movement's strength and validity.
    
    Currently, this rule is a placeholder for future volume analysis implementation
    and returns VALID by default when volume validation is disabled.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate volume patterns in pen
        
        This method would analyze volume patterns to confirm the pen's validity.
        For upward pens, volume should generally increase on up moves and decrease
        on down moves. For downward pens, volume should support the downward movement.
        Currently returns VALID as a placeholder.
        
        Args:
            start_fractal: The starting fractal of the pen
            end_fractal: The ending fractal of the pen
            pen_kbars: List of kbars between fractals (would be used for volume analysis)
            config: Configuration containing volume validation settings
            
        Returns:
            PenValidationResult.VALID (placeholder implementation)
        """
        if not config.require_volume_validation:
            self.logger.debug("Volume validation skipped (disabled in config)")
            return PenValidationResult.VALID
        
        # This would require volume analysis implementation
        # For now, return valid - can be implemented later
        self.logger.debug("Volume validation passed (placeholder implementation)")
        self.logger.debug(f"Pen kbars count: {len(pen_kbars)}")
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the VolumeValidationRule
        """
        return "VolumeValidationRule"


class FractalSeparationRule(PenRule):
    """
    Rule 8: Validate that fractals don't share the same K-line (Standard 2)
    
    This rule implements Standard 2 of Chan theory: "顶分型和底分型绝对不能共用同一根K线"
    (Top and bottom fractals absolutely cannot share the same K-line). This ensures
    that the starting and ending fractals of a pen are properly separated and don't
    overlap in their K-line positions.
    
    The rule validates that fractals have different indices, timestamps, and maintain
    minimum separation to ensure proper pen formation according to Chan theory.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate that start and end fractals don't share the same K-line
        
        This method ensures that the starting and ending fractals are properly
        separated and don't share the same K-line position, which would violate
        fundamental Chan theory principles for pen formation.
        
        Args:
            start_fractal: The starting fractal of the pen
            end_fractal: The ending fractal of the pen
            pen_kbars: List of kbars between fractals (not used in this rule)
            config: Configuration settings (not used in this rule)
            
        Returns:
            PenValidationResult.VALID if fractals are properly separated,
            PenValidationResult.INVALID_FRACTAL_SEPARATION if they share K-lines
        """
        # Check if fractals share the same merged kbar index
        if start_fractal.index == end_fractal.index:
            self.logger.debug(f"Fractal separation validation failed: same index {start_fractal.index}")
            return PenValidationResult.INVALID_FRACTAL_SEPARATION
        
        # Check if fractals are from the same merged kbar timestamp
        if start_fractal.timestamp == end_fractal.timestamp:
            self.logger.debug(f"Fractal separation validation failed: same timestamp {start_fractal.timestamp}")
            return PenValidationResult.INVALID_FRACTAL_SEPARATION
        
        # Ensure minimum separation between fractals
        separation = abs(start_fractal.index - end_fractal.index)
        if separation < 2:
            self.logger.debug(f"Fractal separation validation failed: insufficient separation {separation} < 2")
            self.logger.debug(f"Start fractal index: {start_fractal.index}")
            self.logger.debug(f"End fractal index: {end_fractal.index}")
            return PenValidationResult.INVALID_FRACTAL_SEPARATION
        
        self.logger.debug(f"Fractal separation validation passed: separation={separation}, different timestamps")
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the FractalSeparationRule
        """
        return "FractalSeparationRule"


class FractalLevelRelationRule(PenRule):
    """
    Rule 9: Validate fractal level relationships (Standard 4)
    
    This rule implements Standard 4 of Chan theory: "顶不能在底里，底不能在顶里"
    (Top cannot be inside bottom, bottom cannot be inside top). This ensures that
    the price levels of fractals maintain proper hierarchical relationships.
    
    For bottom-to-top pens, the top fractal's high must be higher than the bottom
    fractal's lowest K-line high. For top-to-bottom pens, the bottom fractal's low
    must be lower than the top fractal's highest K-line low.
    """
    
    def validate(self, start_fractal: Fractal, end_fractal: Fractal, 
                pen_kbars: List['Kbar'], config: PenValidationConfig) -> PenValidationResult:
        """
        Validate that top fractal is not inside bottom fractal and vice versa
        Standard 4: 顶不能在底里，底不能在顶里
        
        This method ensures that the price levels of the starting and ending fractals
        maintain proper hierarchical relationships according to Chan theory principles.
        
        Args:
            start_fractal: The starting fractal of the pen
            end_fractal: The ending fractal of the pen
            pen_kbars: List of kbars between fractals (not used in this rule)
            config: Configuration settings (not used in this rule)
            
        Returns:
            PenValidationResult.VALID if fractal levels are properly related,
            PenValidationResult.INVALID_FRACTAL_LEVEL_RELATION if levels are invalid
        """
        if start_fractal.fractal_type == FractalType.BOTTOM and end_fractal.fractal_type == FractalType.TOP:
            # Bottom to top pen: top fractal high should be higher than bottom fractal's lowest K-line high
            bottom_low_kbar_high = min(start_fractal.left_kbar.high, start_fractal.merged_kbar.high, start_fractal.right_kbar.high)
            top_high = end_fractal.price
            
            if top_high <= bottom_low_kbar_high:
                self.logger.debug(f"Fractal level relation validation failed (bottom-to-top): top_high={top_high} <= bottom_low_kbar_high={bottom_low_kbar_high}")
                self.logger.debug(f"Start fractal (BOTTOM): {start_fractal}")
                self.logger.debug(f"End fractal (TOP): {end_fractal}")
                self.logger.debug(f"Bottom fractal K-line highs: left={start_fractal.left_kbar.high}, middle={start_fractal.merged_kbar.high}, right={start_fractal.right_kbar.high}")
                self.logger.debug(f"Lowest K-line high in bottom fractal: {bottom_low_kbar_high}")
                return PenValidationResult.INVALID_FRACTAL_LEVEL_RELATION
            
            self.logger.debug(f"Fractal level relation validation passed (bottom-to-top): top_high={top_high} > bottom_low_kbar_high={bottom_low_kbar_high}")
        
        elif start_fractal.fractal_type == FractalType.TOP and end_fractal.fractal_type == FractalType.BOTTOM:
            # Top to bottom pen: bottom fractal low should be lower than top fractal's highest K-line low
            top_high_kbar_low = max(start_fractal.left_kbar.low, start_fractal.merged_kbar.low, start_fractal.right_kbar.low)
            bottom_low = end_fractal.price
            
            if bottom_low >= top_high_kbar_low:
                self.logger.debug(f"Fractal level relation validation failed (top-to-bottom): bottom_low={bottom_low} >= top_high_kbar_low={top_high_kbar_low}")
                self.logger.debug(f"Start fractal (TOP): {start_fractal}")
                self.logger.debug(f"End fractal (BOTTOM): {end_fractal}")
                self.logger.debug(f"Top fractal K-line lows: left={start_fractal.left_kbar.low}, middle={start_fractal.merged_kbar.low}, right={start_fractal.right_kbar.low}")
                self.logger.debug(f"Highest K-line low in top fractal: {top_high_kbar_low}")
                return PenValidationResult.INVALID_FRACTAL_LEVEL_RELATION
            
            self.logger.debug(f"Fractal level relation validation passed (top-to-bottom): bottom_low={bottom_low} < top_high_kbar_low={top_high_kbar_low}")
        
        return PenValidationResult.VALID
    
    def get_rule_name(self) -> str:
        """
        Get the name of this validation rule
        
        Returns:
            String identifier for the FractalLevelRelationRule
        """
        return "FractalLevelRelationRule"


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
            VolumeValidationRule(),
            FractalSeparationRule(),
            FractalLevelRelationRule()
        ]
        
        # Note: Standard 3 (pen construction restart logic) is implemented 
        # in the pen construction algorithm, not in these validation rules
        
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
    
    def validate_pen_with_raw_kbars(self, start_fractal: Fractal, end_fractal: Fractal, pen_kbars: List['Kbar']) -> bool:
        """
        Validate a potential pen using raw kbar data
        
        Args:
            start_fractal: Starting fractal
            end_fractal: Ending fractal
            pen_kbars: Raw kbars between the fractals
            
        Returns:
            True if pen is valid according to raw kbar analysis
        """
        # If pen_kbars is empty, fallback to fetching from context
        if not pen_kbars or len(pen_kbars) == 0:
            self.logger.warning("No pen kbars provided, attempting to fetch from context")
            if self.context:
                # Use context to get kbars between fractals
                pen_kbars = get_kbars_between_fractals(start_fractal, end_fractal, self.context)
                self.logger.debug(f"Fetched {len(pen_kbars)} kbars from context as fallback")
            else:
                self.logger.warning("No context available for fallback kbar fetching")
                return True  # Allow pen if no data available
        
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
            "7. Volume Validation Rule: Volume patterns should support pen (if enabled)",
            "8. Fractal Separation Rule: Fractals must not share the same K-line",
            "9. Fractal Level Relation Rule: Top fractal must not be inside bottom fractal"
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