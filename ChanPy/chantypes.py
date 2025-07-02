from enum import Enum
from dataclasses import dataclass, field
from typing import List

class BodySizeCategory(Enum):
    """Body size category enumeration for K-bar classification"""
    SMALL = "小"      # Small body (小阳线/小阴线)
    MEDIUM = "中"     # Medium body (中阳线/中阴线)  
    LARGE = "大"      # Large body (大阳线/大阴线)
    DOJI = "十字星"   # Doji (十字星)


class Direction(Enum):
    """Direction enumeration for Chan analysis"""
    UP = 1
    DOWN = -1
    UNKNOWN = 0


class PenType(Enum):
    """Pen type enumeration"""
    TOP = 1      # Top pen (向上笔)
    BOTTOM = -1  # Bottom pen (向下笔)


@dataclass
class Kbar:
    """K-bar data structure"""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    def __post_init__(self):
        """Validate K-bar data after initialization"""
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid K-bar data: high/low inconsistent with open/close")


@dataclass
class FractionalPoint:
    """Fractional point in Chan analysis (分型)"""
    index: int
    timestamp: str
    price: float
    point_type: PenType  # TOP or BOTTOM
    kbar: Kbar
    confirmed: bool = False


@dataclass
class Pen:
    """Pen structure in Chan analysis (笔)"""
    start_point: FractionalPoint
    end_point: FractionalPoint
    direction: Direction
    length: float
    start_time: str
    end_time: str
    confirmed: bool = False
    
    @property
    def duration_bars(self) -> int:
        """Number of bars in this pen"""
        return self.end_point.index - self.start_point.index + 1

@dataclass  
class Segment:
    """Segment structure in Chan analysis (线段)"""
    start_pen: Pen
    end_pen: Pen
    pens: List[Pen] = field(default_factory=list)
    direction: Direction = Direction.UNKNOWN
    high: float = 0.0
    low: float = 0.0
    confirmed: bool = False
    
    def __post_init__(self):
        """Calculate segment properties after initialization"""
        if self.pens:
            self.high = max(pen.end_point.price for pen in self.pens)
            self.low = min(pen.end_point.price for pen in self.pens)
            # Determine overall direction
            if self.start_pen.end_point.price < self.end_pen.end_point.price:
                self.direction = Direction.UP
            else:
                self.direction = Direction.DOWN




class KbarShape(Enum):
    """
    Enumeration of K-bar shapes based on OHLC relationships.
    
    Categorizes individual K-bars (candlesticks) based on:
    - Body size (relationship between open and close)  
    - Shadow length (upper and lower shadows)
    - Overall proportions and patterns
    """
    
    # === Bullish (阳线) Patterns - Close > Open ===
    
    # Full-body bullish - no shadows (光头光脚阳线)
    BULLISH_MARUBOZU = "bullish_marubozu"
    
    # Long bullish body with small shadows (大阳线)  
    BULLISH_LONG_BODY = "bullish_long_body"
    
    # Medium bullish body (中阳线)
    BULLISH_MEDIUM_BODY = "bullish_medium_body"
    
    # Short bullish body (小阳线)
    BULLISH_SHORT_BODY = "bullish_short_body"
    
    # Bullish with long upper shadow (上影阳线)
    BULLISH_UPPER_SHADOW = "bullish_upper_shadow"
    
    # Bullish with long lower shadow (下影阳线) 
    BULLISH_LOWER_SHADOW = "bullish_lower_shadow"
    
    # Bullish hammer - long lower shadow, short body (阳锤子线)
    BULLISH_HAMMER = "bullish_hammer"
    
    # Bullish inverted hammer - long upper shadow, short body (阳倒锤子线)
    BULLISH_INVERTED_HAMMER = "bullish_inverted_hammer"
    
    # === Bearish (阴线) Patterns - Close < Open ===
    
    # Full-body bearish - no shadows (光头光脚阴线)
    BEARISH_MARUBOZU = "bearish_marubozu"
    
    # Long bearish body with small shadows (大阴线)
    BEARISH_LONG_BODY = "bearish_long_body"
    
    # Medium bearish body (中阴线)
    BEARISH_MEDIUM_BODY = "bearish_medium_body"
    
    # Short bearish body (小阴线)
    BEARISH_SHORT_BODY = "bearish_short_body"
    
    # Bearish with long upper shadow (上影阴线)
    BEARISH_UPPER_SHADOW = "bearish_upper_shadow"
    
    # Bearish with long lower shadow (下影阴线)
    BEARISH_LOWER_SHADOW = "bearish_lower_shadow"
    
    # Bearish hammer - long lower shadow, short body (阴锤子线)
    BEARISH_HAMMER = "bearish_hammer"
    
    # Bearish shooting star - long upper shadow, short body (阴流星线)
    BEARISH_SHOOTING_STAR = "bearish_shooting_star"
    
    # === Doji Patterns (十字星) - Open ≈ Close ===
    
    # Perfect doji - open = close (十字星)
    DOJI = "doji"
    
    # Long-legged doji - long shadows on both sides (长脚十字星)
    LONG_LEGGED_DOJI = "long_legged_doji"
    
    # Dragonfly doji - long lower shadow only (蜻蜓十字星)
    DRAGONFLY_DOJI = "dragonfly_doji"
    
    # Gravestone doji - long upper shadow only (墓碑十字星)
    GRAVESTONE_DOJI = "gravestone_doji"
    
    # Four-price doji - all OHLC equal (一字线)
    FOUR_PRICE_DOJI = "four_price_doji"
    
    @classmethod
    def determine_shape(cls, open_price: float, high: float, low: float, close: float, 
                       body_threshold: float = 0.3, shadow_threshold: float = 2.0,
                       doji_threshold: float = 0.1) -> 'KbarShape':
        """
        Determine the shape of a K-bar based on its OHLC values.
        
        Args:
            open_price (float): Opening price
            high (float): Highest price
            low (float): Lowest price  
            close (float): Closing price
            body_threshold (float): Threshold for body size classification (as ratio of total range)
            shadow_threshold (float): Threshold for shadow length (as ratio of body size)
            doji_threshold (float): Threshold for doji detection (as ratio of total range)
            
        Returns:
            KbarShape: The determined shape of the K-bar
            
        Raises:
            ValueError: If OHLC values are invalid
        """
        # Validate OHLC data
        if high < max(open_price, close) or low > min(open_price, close):
            raise ValueError("Invalid OHLC data: high/low inconsistent with open/close")
        
        # Calculate basic measurements
        total_range = high - low
        body_size = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        
        # Handle special case where total_range is 0 (all prices equal)
        if total_range == 0:
            return cls.FOUR_PRICE_DOJI
        
        # Calculate ratios
        body_ratio = body_size / total_range if total_range > 0 else 0
        is_bullish = close > open_price
        is_bearish = close < open_price
        is_doji = body_ratio <= doji_threshold
        
        # Determine if shadows are long relative to body
        body_size_for_shadow = max(body_size, total_range * 0.01)  # Avoid division by zero
        upper_shadow_ratio = upper_shadow / body_size_for_shadow
        lower_shadow_ratio = lower_shadow / body_size_for_shadow
        
        has_long_upper_shadow = upper_shadow_ratio >= shadow_threshold
        has_long_lower_shadow = lower_shadow_ratio >= shadow_threshold
        has_minimal_shadows = (upper_shadow / total_range <= 0.05 and 
                              lower_shadow / total_range <= 0.05)
        
        # === Doji Patterns ===
        if is_doji:
            if has_long_upper_shadow and not has_long_lower_shadow:
                return cls.GRAVESTONE_DOJI
            elif has_long_lower_shadow and not has_long_upper_shadow:
                return cls.DRAGONFLY_DOJI
            elif has_long_upper_shadow and has_long_lower_shadow:
                return cls.LONG_LEGGED_DOJI
            else:
                return cls.DOJI
        
        # === Bullish Patterns ===
        elif is_bullish:
            # Check for special patterns first
            if has_long_lower_shadow and body_ratio <= 0.3:
                return cls.BULLISH_HAMMER
            elif has_long_upper_shadow and body_ratio <= 0.3:
                return cls.BULLISH_INVERTED_HAMMER
            elif has_minimal_shadows:
                return cls.BULLISH_MARUBOZU
            elif has_long_upper_shadow:
                return cls.BULLISH_UPPER_SHADOW
            elif has_long_lower_shadow:
                return cls.BULLISH_LOWER_SHADOW
            # Classify by body size
            elif body_ratio >= 0.7:
                return cls.BULLISH_LONG_BODY
            elif body_ratio >= body_threshold:
                return cls.BULLISH_MEDIUM_BODY
            else:
                return cls.BULLISH_SHORT_BODY
        
        # === Bearish Patterns ===
        elif is_bearish:
            # Check for special patterns first
            if has_long_lower_shadow and body_ratio <= 0.3:
                return cls.BEARISH_HAMMER
            elif has_long_upper_shadow and body_ratio <= 0.3:
                return cls.BEARISH_SHOOTING_STAR
            elif has_minimal_shadows:
                return cls.BEARISH_MARUBOZU
            elif has_long_upper_shadow:
                return cls.BEARISH_UPPER_SHADOW
            elif has_long_lower_shadow:
                return cls.BEARISH_LOWER_SHADOW
            # Classify by body size
            elif body_ratio >= 0.7:
                return cls.BEARISH_LONG_BODY
            elif body_ratio >= body_threshold:
                return cls.BEARISH_MEDIUM_BODY
            else:
                return cls.BEARISH_SHORT_BODY
        
        # Fallback (shouldn't reach here with valid data)
        return cls.DOJI
    
    def get_description(self) -> str:
        """
        Get a human-readable description of the K-bar shape.
        
        Returns:
            str: Description of the K-bar shape in Chinese and English
        """
        descriptions = {
            # Bullish patterns
            self.BULLISH_MARUBOZU: "光头光脚阳线 - Bullish Marubozu (no shadows)",
            self.BULLISH_LONG_BODY: "大阳线 - Long Bullish Body",
            self.BULLISH_MEDIUM_BODY: "中阳线 - Medium Bullish Body", 
            self.BULLISH_SHORT_BODY: "小阳线 - Short Bullish Body",
            self.BULLISH_UPPER_SHADOW: "上影阳线 - Bullish with Upper Shadow",
            self.BULLISH_LOWER_SHADOW: "下影阳线 - Bullish with Lower Shadow",
            self.BULLISH_HAMMER: "阳锤子线 - Bullish Hammer",
            self.BULLISH_INVERTED_HAMMER: "阳倒锤子线 - Bullish Inverted Hammer",
            
            # Bearish patterns
            self.BEARISH_MARUBOZU: "光头光脚阴线 - Bearish Marubozu (no shadows)",
            self.BEARISH_LONG_BODY: "大阴线 - Long Bearish Body",
            self.BEARISH_MEDIUM_BODY: "中阴线 - Medium Bearish Body",
            self.BEARISH_SHORT_BODY: "小阴线 - Short Bearish Body", 
            self.BEARISH_UPPER_SHADOW: "上影阴线 - Bearish with Upper Shadow",
            self.BEARISH_LOWER_SHADOW: "下影阴线 - Bearish with Lower Shadow",
            self.BEARISH_HAMMER: "阴锤子线 - Bearish Hammer",
            self.BEARISH_SHOOTING_STAR: "阴流星线 - Bearish Shooting Star",
            
            # Doji patterns
            self.DOJI: "十字星 - Doji",
            self.LONG_LEGGED_DOJI: "长脚十字星 - Long-legged Doji",
            self.DRAGONFLY_DOJI: "蜻蜓十字星 - Dragonfly Doji",
            self.GRAVESTONE_DOJI: "墓碑十字星 - Gravestone Doji",
            self.FOUR_PRICE_DOJI: "一字线 - Four-price Doji (all prices equal)"
        }
        return descriptions.get(self, "Unknown K-bar shape")
    
    def is_bullish(self) -> bool:
        """Check if this shape represents a bullish pattern."""
        bullish_patterns = {
            self.BULLISH_MARUBOZU, self.BULLISH_LONG_BODY, self.BULLISH_MEDIUM_BODY,
            self.BULLISH_SHORT_BODY, self.BULLISH_UPPER_SHADOW, self.BULLISH_LOWER_SHADOW,
            self.BULLISH_HAMMER, self.BULLISH_INVERTED_HAMMER
        }
        return self in bullish_patterns
    
    def is_bearish(self) -> bool:
        """Check if this shape represents a bearish pattern."""
        bearish_patterns = {
            self.BEARISH_MARUBOZU, self.BEARISH_LONG_BODY, self.BEARISH_MEDIUM_BODY,
            self.BEARISH_SHORT_BODY, self.BEARISH_UPPER_SHADOW, self.BEARISH_LOWER_SHADOW,
            self.BEARISH_HAMMER, self.BEARISH_SHOOTING_STAR
        }
        return self in bearish_patterns
    
    def is_doji(self) -> bool:
        """Check if this shape represents a doji pattern."""
        doji_patterns = {
            self.DOJI, self.LONG_LEGGED_DOJI, self.DRAGONFLY_DOJI, 
            self.GRAVESTONE_DOJI, self.FOUR_PRICE_DOJI
        }
        return self in doji_patterns
    
    @property
    def body_size_category(self) -> BodySizeCategory:
        """
        Get the body size category of this K-bar shape.
        
        Returns:
            BodySizeCategory: The quantized body size category (小/中/大/十字星)
        """
        # Doji patterns
        if self.is_doji():
            return BodySizeCategory.DOJI
        
        # Large body patterns (大阳线/大阴线)
        large_body_patterns = {
            self.BULLISH_LONG_BODY, self.BEARISH_LONG_BODY,
            self.BULLISH_MARUBOZU, self.BEARISH_MARUBOZU
        }
        if self in large_body_patterns:
            return BodySizeCategory.LARGE
        
        # Medium body patterns (中阳线/中阴线)
        medium_body_patterns = {
            self.BULLISH_MEDIUM_BODY, self.BEARISH_MEDIUM_BODY,
            self.BULLISH_UPPER_SHADOW, self.BEARISH_UPPER_SHADOW,
            self.BULLISH_LOWER_SHADOW, self.BEARISH_LOWER_SHADOW
        }
        if self in medium_body_patterns:
            return BodySizeCategory.MEDIUM
        
        # Small body patterns (小阳线/小阴线) - includes hammers and shooting stars
        small_body_patterns = {
            self.BULLISH_SHORT_BODY, self.BEARISH_SHORT_BODY,
            self.BULLISH_HAMMER, self.BEARISH_HAMMER,
            self.BULLISH_INVERTED_HAMMER, self.BEARISH_SHOOTING_STAR
        }
        if self in small_body_patterns:
            return BodySizeCategory.SMALL
        
        # Fallback to small for any unclassified patterns
        return BodySizeCategory.SMALL


# Helper functions for convenience
def get_kbar_shape(open_price: float, high: float, low: float, close: float) -> KbarShape:
    """
    Convenience function to determine K-bar shape.
    
    Args:
        open_price (float): Opening price
        high (float): Highest price
        low (float): Lowest price
        close (float): Closing price
        
    Returns:
        KbarShape: The shape of the K-bar
    """
    return KbarShape.determine_shape(open_price, high, low, close)


def get_kbar_object_shape(kbar) -> KbarShape:
    """
    Convenience function to determine K-bar shape from Kbar object.
    
    Args:
        kbar: Kbar object (should have .open, .high, .low, .close attributes)
        
    Returns:
        KbarShape: The shape of the K-bar
        
    Raises:
        AttributeError: If Kbar object doesn't have required attributes
    """
    try:
        return KbarShape.determine_shape(
            open_price=kbar.open,
            high=kbar.high, 
            low=kbar.low,
            close=kbar.close
        )
    except AttributeError as e:
        raise AttributeError(f"Kbar object must have 'open', 'high', 'low', 'close' attributes: {e}")
    except Exception as e:
        raise ValueError(f"Error determining shape of Kbar object: {e}")

class KBarRelationship(Enum):
    """
    Enumeration of all possible relationships between two consecutive K-bars.
    
    For two K-bars K1 and K2:
    - K1 has high point G1 and low point D1
    - K2 has high point G2 and low point D2
    
    The relationship is determined by comparing their high and low points.
    """
    
    # K1 completely contains K2
    K1_CONTAINS_K2 = "k1_contains_k2"
    
    # K2 completely contains K1
    K2_CONTAINS_K1 = "k2_contains_k1"
    
    # Both K-bars have identical high and low points
    IDENTICAL = "identical"
    
    # K1 is completely above K2 (no overlap)
    K1_ABOVE_K2 = "k1_above_k2"
    
    # K1 is completely below K2 (no overlap)
    K1_BELOW_K2 = "k1_below_k2"
    
    # K1 and K2 overlap but neither contains the other
    UP_OVERLAP = "up_overlap"      # K1's high is below K2's high, and K1's low is below K2's low, and K1's high is above K2's low
    DOWN_OVERLAP = "down_overlap"  # K1's high is above K2's high, and K1's low is above K2's low, and K2's high is above K1's low
    
    # K1 and K2 share the same low point but different highs
    SAME_LOW_K1_HIGHER = "same_low_k1_higher"
    SAME_LOW_K2_HIGHER = "same_low_k2_higher"
    
    # K1 and K2 share the same high point but different lows
    SAME_HIGH_K1_LOWER = "same_high_k1_lower"
    SAME_HIGH_K2_LOWER = "same_high_k2_lower"
    
    @classmethod
    def determine_relationship(cls, d1: float, g1: float, d2: float, g2: float) -> 'KBarRelationship':
        """
        Determine the relationship between two K-bars based on their high and low points.
        
        Args:
            d1 (float): Low point of K1
            g1 (float): High point of K1
            d2 (float): Low point of K2
            g2 (float): High point of K2
            
        Returns:
            KBarRelationship: The relationship between K1 and K2
            
        Raises:
            ValueError: If high point is less than low point for either K-bar
        """
        # Validate input
        if g1 < d1:
            raise ValueError("K1 high point must be >= low point")
        if g2 < d2:
            raise ValueError("K2 high point must be >= low point")
        
        # Check for identical K-bars
        if d1 == d2 and g1 == g2:
            return cls.IDENTICAL
        
        # Check containment relationships
        if d1 <= d2 and g1 >= g2:
            # K1 contains K2
            if d1 == d2 and g1 > g2:
                return cls.SAME_LOW_K1_HIGHER
            elif d1 < d2 and g1 == g2:
                return cls.SAME_HIGH_K2_LOWER
            else:
                return cls.K1_CONTAINS_K2
                
        elif d1 >= d2 and g1 <= g2:
            # K2 contains K1
            if d1 == d2 and g1 < g2:
                return cls.SAME_LOW_K2_HIGHER
            elif d1 > d2 and g1 == g2:
                return cls.SAME_HIGH_K1_LOWER
            else:
                return cls.K2_CONTAINS_K1
        
        # Check for complete separation
        elif g1 < d2:
            # K1 is completely below K2
            return cls.K1_BELOW_K2
        elif g2 < d1:
            # K1 is completely above K2
            return cls.K1_ABOVE_K2
        
        # Otherwise, they must be overlapping
        else:
            # Determine if it's up overlap or down overlap
            if g1 < g2:
                # K1's high is below K2's high
                return cls.UP_OVERLAP
            else:
                # K1's high is above K2's high (g1 > g2)
                return cls.DOWN_OVERLAP
    
    def get_description(self) -> str:
        """
        Get a human-readable description of the relationship.
        
        Returns:
            str: Description of the relationship
        """
        descriptions = {
            self.K1_CONTAINS_K2: "K1包含K2 - K1 completely contains K2",
            self.K2_CONTAINS_K1: "K2包含K1 - K2 completely contains K1", 
            self.IDENTICAL: "相同 - Both K-bars have identical range",
            self.K1_ABOVE_K2: "K1在K2上方 - K1 is completely above K2",
            self.K1_BELOW_K2: "K1在K2下方 - K1 is completely below K2",
            self.UP_OVERLAP: "上重叠 - K1's high is below K2's high, and K1's low is below K2's low, but K1's high is above K2's low",
            self.DOWN_OVERLAP: "下重叠 - K1's high is above K2's high, K1's low is above K2's low and K2's high is above K1's low",
            self.SAME_LOW_K1_HIGHER: "同低K1高 - Same low point, K1 has higher high",
            self.SAME_LOW_K2_HIGHER: "同低K2高 - Same low point, K2 has higher high",
            self.SAME_HIGH_K1_LOWER: "同高K1低 - Same high point, K1 has lower low",
            self.SAME_HIGH_K2_LOWER: "同高K2低 - Same high point, K2 has lower low"
        }
        return descriptions.get(self, "Unknown relationship")


# Helper function for convenience
def get_kbar_relationship(k1_low: float, k1_high: float, k2_low: float, k2_high: float) -> KBarRelationship:
    """
    Convenience function to determine K-bar relationship.
    
    Args:
        k1_low (float): Low point of first K-bar
        k1_high (float): High point of first K-bar  
        k2_low (float): Low point of second K-bar
        k2_high (float): High point of second K-bar
        
    Returns:
        KBarRelationship: The relationship between the two K-bars
    """
    return KBarRelationship.determine_relationship(k1_low, k1_high, k2_low, k2_high)


def get_kbar_objects_relationship(kbar1, kbar2) -> KBarRelationship:
    """
    Convenience function to determine K-bar relationship from Kbar objects.
    
    Args:
        kbar1: First Kbar object (should have .low and .high attributes)
        kbar2: Second Kbar object (should have .low and .high attributes)
        
    Returns:
        KBarRelationship: The relationship between the two K-bars
        
    Raises:
        AttributeError: If Kbar objects don't have required attributes
    """
    try:
        return KBarRelationship.determine_relationship(
            d1=kbar1.low, 
            g1=kbar1.high, 
            d2=kbar2.low, 
            g2=kbar2.high
        )
    except AttributeError as e:
        raise AttributeError(f"Kbar objects must have 'low' and 'high' attributes: {e}")
    except Exception as e:
        raise ValueError(f"Error determining relationship between Kbar objects: {e}")


# Example usage and test cases
if __name__ == "__main__":
    print("=== 完整测试用例 - Complete Test Cases ===\n")
    
    # Test 1: K1_CONTAINS_K2 - K1 completely contains K2
    print("1. K1_CONTAINS_K2 - K1包含K2:")
    relationship1 = get_kbar_relationship(k1_low=10, k1_high=30, k2_low=15, k2_high=25)
    print(f"   K1(10-30) vs K2(15-25): {relationship1.value}")
    print(f"   {relationship1.get_description()}\n")
    
    # Test 2: K2_CONTAINS_K1 - K2 completely contains K1  
    print("2. K2_CONTAINS_K1 - K2包含K1:")
    relationship2 = get_kbar_relationship(k1_low=15, k1_high=25, k2_low=10, k2_high=30)
    print(f"   K1(15-25) vs K2(10-30): {relationship2.value}")
    print(f"   {relationship2.get_description()}\n")
    
    # Test 3: IDENTICAL - Both K-bars have identical range
    print("3. IDENTICAL - 相同:")
    relationship3 = get_kbar_relationship(k1_low=10, k1_high=20, k2_low=10, k2_high=20)
    print(f"   K1(10-20) vs K2(10-20): {relationship3.value}")
    print(f"   {relationship3.get_description()}\n")
    
    # Test 4: K1_ABOVE_K2 - K1 is completely above K2
    print("4. K1_ABOVE_K2 - K1在K2上方:")
    relationship4 = get_kbar_relationship(k1_low=25, k1_high=30, k2_low=10, k2_high=20)
    print(f"   K1(25-30) vs K2(10-20): {relationship4.value}")
    print(f"   {relationship4.get_description()}\n")
    
    # Test 5: K1_BELOW_K2 - K1 is completely below K2
    print("5. K1_BELOW_K2 - K1在K2下方:")
    relationship5 = get_kbar_relationship(k1_low=10, k1_high=15, k2_low=20, k2_high=25)
    print(f"   K1(10-15) vs K2(20-25): {relationship5.value}")
    print(f"   {relationship5.get_description()}\n")
    
    # Test 6: UP_OVERLAP - K1's high < K2's high, K1's low < K2's low, K1's high > K2's low
    print("6. UP_OVERLAP - 上重叠:")
    relationship6 = get_kbar_relationship(k1_low=10, k1_high=20, k2_low=15, k2_high=25)
    print(f"   K1(10-20) vs K2(15-25): {relationship6.value}")
    print(f"   {relationship6.get_description()}")
    print(f"   验证: K1高({20}) < K2高({25}) ✓, K1低({10}) < K2低({15}) ✓, K1高({20}) > K2低({15}) ✓\n")
    
    # Test 7: DOWN_OVERLAP - K1's high > K2's high, K1's low > K2's low, K2's high > K1's low
    print("7. DOWN_OVERLAP - 下重叠:")
    relationship7 = get_kbar_relationship(k1_low=15, k1_high=25, k2_low=10, k2_high=20)
    print(f"   K1(15-25) vs K2(10-20): {relationship7.value}")
    print(f"   {relationship7.get_description()}")
    print(f"   验证: K1高({25}) > K2高({20}) ✓, K1低({15}) > K2低({10}) ✓, K2高({20}) > K1低({15}) ✓\n")
    
    # Test 8: SAME_LOW_K1_HIGHER - Same low point, K1 has higher high
    print("8. SAME_LOW_K1_HIGHER - 同低K1高:")
    relationship8 = get_kbar_relationship(k1_low=10, k1_high=25, k2_low=10, k2_high=20)
    print(f"   K1(10-25) vs K2(10-20): {relationship8.value}")
    print(f"   {relationship8.get_description()}\n")
    
    # Test 9: SAME_LOW_K2_HIGHER - Same low point, K2 has higher high
    print("9. SAME_LOW_K2_HIGHER - 同低K2高:")
    relationship9 = get_kbar_relationship(k1_low=10, k1_high=20, k2_low=10, k2_high=25)
    print(f"   K1(10-20) vs K2(10-25): {relationship9.value}")
    print(f"   {relationship9.get_description()}\n")
    
    # Test 10: SAME_HIGH_K1_LOWER - Same high point, K1 has lower low
    print("10. SAME_HIGH_K1_LOWER - 同高K1低:")
    relationship10 = get_kbar_relationship(k1_low=5, k1_high=20, k2_low=10, k2_high=20)
    print(f"    K1(5-20) vs K2(10-20): {relationship10.value}")
    print(f"    {relationship10.get_description()}\n")
    
    # Test 11: SAME_HIGH_K2_LOWER - Same high point, K2 has lower low
    print("11. SAME_HIGH_K2_LOWER - 同高K2低:")
    relationship11 = get_kbar_relationship(k1_low=10, k1_high=20, k2_low=5, k2_high=20)
    print(f"    K1(10-20) vs K2(5-20): {relationship11.value}")
    print(f"    {relationship11.get_description()}\n")
    
    print("=== Kbar对象测试 - Kbar Object Tests ===\n")
    
    # Create mock Kbar objects for testing
    class MockKbar:
        def __init__(self, low, high, name=""):
            self.low = low
            self.high = high
            self.name = name
        
        def __repr__(self):
            return f"MockKbar{self.name}(low={self.low}, high={self.high})"
    
    # Test with Kbar objects - UP_OVERLAP example
    print("12. 使用Kbar对象测试 UP_OVERLAP:")
    kbar_obj1 = MockKbar(low=10, high=20, name="1")
    kbar_obj2 = MockKbar(low=15, high=25, name="2")
    relationship_obj1 = get_kbar_objects_relationship(kbar_obj1, kbar_obj2)
    print(f"    {kbar_obj1} vs {kbar_obj2}")
    print(f"    结果: {relationship_obj1.value} - {relationship_obj1.get_description()}\n")
    
    # Test with Kbar objects - DOWN_OVERLAP example
    print("13. 使用Kbar对象测试 DOWN_OVERLAP:")
    kbar_obj3 = MockKbar(low=15, high=25, name="3")
    kbar_obj4 = MockKbar(low=10, high=20, name="4")
    relationship_obj2 = get_kbar_objects_relationship(kbar_obj3, kbar_obj4)
    print(f"    {kbar_obj3} vs {kbar_obj4}")
    print(f"    结果: {relationship_obj2.value} - {relationship_obj2.get_description()}\n")
    
    # Test edge cases
    print("=== 边界情况测试 - Edge Case Tests ===\n")
    
    # Test 14: Adjacent K-bars (touching but not overlapping)
    print("14. 相邻K线 - Adjacent K-bars:")
    relationship14 = get_kbar_relationship(k1_low=10, k1_high=15, k2_low=15, k2_high=20)
    print(f"    K1(10-15) vs K2(15-20): {relationship14.value}")
    print(f"    {relationship14.get_description()}\n")
    
    # Test 15: Single point K-bars (high = low)
    print("15. 单点K线 - Single point K-bars:")
    relationship15 = get_kbar_relationship(k1_low=15, k1_high=15, k2_low=10, k2_high=20)
    print(f"    K1(15-15) vs K2(10-20): {relationship15.value}")
    print(f"    {relationship15.get_description()}\n")
    
    print("=== 测试完成 - All Tests Completed ===")
    
    print("=== K线形态测试 - KbarShape Tests ===\n")
    
    # Test 1: Bullish Marubozu (光头光脚阳线)
    print("1. 光头光脚阳线 - Bullish Marubozu:")
    shape1 = get_kbar_shape(open_price=100, high=120, low=100, close=120)
    print(f"   OHLC(100,120,100,120): {shape1.value}")
    print(f"   {shape1.get_description()}")
    print(f"   Is Bullish: {shape1.is_bullish()}")
    print(f"   Body Size Category: {shape1.body_size_category.value}\n")
    
    # Test 2: Bearish Marubozu (光头光脚阴线)
    print("2. 光头光脚阴线 - Bearish Marubozu:")
    shape2 = get_kbar_shape(open_price=120, high=120, low=100, close=100)
    print(f"   OHLC(120,120,100,100): {shape2.value}")
    print(f"   {shape2.get_description()}")
    print(f"   Is Bearish: {shape2.is_bearish()}")
    print(f"   Body Size Category: {shape2.body_size_category.value}\n")
    
    # Test 3: Doji (十字星)
    print("3. 十字星 - Doji:")
    shape3 = get_kbar_shape(open_price=110, high=115, low=105, close=110)
    print(f"   OHLC(110,115,105,110): {shape3.value}")
    print(f"   {shape3.get_description()}")
    print(f"   Is Doji: {shape3.is_doji()}")
    print(f"   Body Size Category: {shape3.body_size_category.value}\n")
    
    # Test 4: Bullish Hammer (阳锤子线)
    print("4. 阳锤子线 - Bullish Hammer:")
    shape4 = get_kbar_shape(open_price=105, high=108, low=95, close=107)
    print(f"   OHLC(105,108,95,107): {shape4.value}")
    print(f"   {shape4.get_description()}")
    print(f"   Is Bullish: {shape4.is_bullish()}")
    print(f"   Body Size Category: {shape4.body_size_category.value}\n")
    
    # Test 5: Bearish Shooting Star (阴流星线)
    print("5. 阴流星线 - Bearish Shooting Star:")
    shape5 = get_kbar_shape(open_price=107, high=125, low=105, close=106)
    print(f"   OHLC(107,125,105,106): {shape5.value}")
    print(f"   {shape5.get_description()}")
    print(f"   Is Bearish: {shape5.is_bearish()}")
    print(f"   Body Size Category: {shape5.body_size_category.value}\n")
    
    # Test 6: Long-legged Doji (长脚十字星)
    print("6. 长脚十字星 - Long-legged Doji:")
    shape6 = get_kbar_shape(open_price=110, high=130, low=90, close=111)
    print(f"   OHLC(110,130,90,111): {shape6.value}")
    print(f"   {shape6.get_description()}")
    print(f"   Is Doji: {shape6.is_doji()}")
    print(f"   Body Size Category: {shape6.body_size_category.value}\n")
    
    # Test 7: Dragonfly Doji (蜻蜓十字星)
    print("7. 蜻蜓十字星 - Dragonfly Doji:")
    shape7 = get_kbar_shape(open_price=110, high=112, low=90, close=110)
    print(f"   OHLC(110,112,90,110): {shape7.value}")
    print(f"   {shape7.get_description()}")
    print(f"   Is Doji: {shape7.is_doji()}")
    print(f"   Body Size Category: {shape7.body_size_category.value}\n")
    
    # Test 8: Gravestone Doji (墓碑十字星)
    print("8. 墓碑十字星 - Gravestone Doji:")
    shape8 = get_kbar_shape(open_price=110, high=130, low=108, close=110)
    print(f"   OHLC(110,130,108,110): {shape8.value}")
    print(f"   {shape8.get_description()}")
    print(f"   Is Doji: {shape8.is_doji()}")
    print(f"   Body Size Category: {shape8.body_size_category.value}\n")
    
    # Test 9: Four-price Doji (一字线)
    print("9. 一字线 - Four-price Doji:")
    shape9 = get_kbar_shape(open_price=110, high=110, low=110, close=110)
    print(f"   OHLC(110,110,110,110): {shape9.value}")
    print(f"   {shape9.get_description()}")
    print(f"   Is Doji: {shape9.is_doji()}")
    print(f"   Body Size Category: {shape9.body_size_category.value}\n")
    
    # Test 10: Long Bullish Body (大阳线)
    print("10. 大阳线 - Long Bullish Body:")
    shape10 = get_kbar_shape(open_price=100, high=125, low=98, close=123)
    print(f"    OHLC(100,125,98,123): {shape10.value}")
    print(f"    {shape10.get_description()}")
    print(f"    Is Bullish: {shape10.is_bullish()}")
    print(f"    Body Size Category: {shape10.body_size_category.value}\n")
    
    print("=== Kbar对象形态测试 - Kbar Object Shape Tests ===\n")
    
    # Create mock Kbar objects for testing
    class MockShapeKbar:
        def __init__(self, open_p, high, low, close, name=""):
            self.open = open_p
            self.high = high
            self.low = low
            self.close = close
            self.name = name
        
        def __repr__(self):
            return f"MockKbar{self.name}(O:{self.open}, H:{self.high}, L:{self.low}, C:{self.close})"
    
    # Test with Kbar object - Bullish Upper Shadow
    print("11. 使用Kbar对象测试 上影阳线:")
    kbar_obj1 = MockShapeKbar(open_p=100, high=130, low=98, close=105, name="1")
    shape_obj1 = get_kbar_object_shape(kbar_obj1)
    print(f"    {kbar_obj1}")
    print(f"    结果: {shape_obj1.value} - {shape_obj1.get_description()}")
    print(f"    Body Size Category: {shape_obj1.body_size_category.value}\n")
    
    # Test with Kbar object - Bearish Lower Shadow
    print("12. 使用Kbar对象测试 下影阴线:")
    kbar_obj2 = MockShapeKbar(open_p=120, high=122, low=90, close=115, name="2")
    shape_obj2 = get_kbar_object_shape(kbar_obj2)
    print(f"    {kbar_obj2}")
    print(f"    结果: {shape_obj2.value} - {shape_obj2.get_description()}")
    print(f"    Body Size Category: {shape_obj2.body_size_category.value}\n")
    
    # Additional test cases for different body size categories
    print("13. 中阳线 - Medium Bullish Body:")
    shape13 = get_kbar_shape(open_price=100, high=115, low=98, close=110)
    print(f"    OHLC(100,115,98,110): {shape13.value}")
    print(f"    {shape13.get_description()}")
    print(f"    Body Size Category: {shape13.body_size_category.value}\n")
    
    print("14. 小阴线 - Short Bearish Body:")
    shape14 = get_kbar_shape(open_price=110, high=115, low=105, close=107)
    print(f"    OHLC(110,115,105,107): {shape14.value}")
    print(f"    {shape14.get_description()}")
    print(f"    Body Size Category: {shape14.body_size_category.value}\n")
    
    print("=== 形态分类汇总 - Shape Classification Summary ===\n")
    
    all_shapes = [shape1, shape2, shape3, shape4, shape5, shape6, shape7, shape8, shape9, shape10, shape_obj1, shape_obj2, shape13, shape14]
    bullish_count = sum(1 for s in all_shapes if s.is_bullish())
    bearish_count = sum(1 for s in all_shapes if s.is_bearish())
    doji_count = sum(1 for s in all_shapes if s.is_doji())
    
    # Body size category statistics
    large_count = sum(1 for s in all_shapes if s.body_size_category == BodySizeCategory.LARGE)
    medium_count = sum(1 for s in all_shapes if s.body_size_category == BodySizeCategory.MEDIUM)
    small_count = sum(1 for s in all_shapes if s.body_size_category == BodySizeCategory.SMALL)
    doji_body_count = sum(1 for s in all_shapes if s.body_size_category == BodySizeCategory.DOJI)
    
    print(f"总测试形态数: {len(all_shapes)}")
    print(f"阳线形态数: {bullish_count}")
    print(f"阴线形态数: {bearish_count}")
    print(f"十字星形态数: {doji_count}")
    print(f"验证: {bullish_count + bearish_count + doji_count} = {len(all_shapes)} ✓\n")
    
    print("=== 实体大小分类统计 - Body Size Category Statistics ===")
    print(f"大实体 (大): {large_count}")
    print(f"中实体 (中): {medium_count}")
    print(f"小实体 (小): {small_count}")
    print(f"十字星 (十字星): {doji_body_count}")
    print(f"验证: {large_count + medium_count + small_count + doji_body_count} = {len(all_shapes)} ✓\n")
    
    # Detailed breakdown by body size category
    print("=== 详细分类明细 - Detailed Category Breakdown ===")
    for category in BodySizeCategory:
        category_shapes = [s for s in all_shapes if s.body_size_category == category]
        if category_shapes:
            print(f"\n{category.value} 类别 ({len(category_shapes)}个):")
            for i, shape in enumerate(category_shapes, 1):
                print(f"  {i}. {shape.get_description()}")
    
    print(f"\n总计: {len(all_shapes)} 个测试形态")