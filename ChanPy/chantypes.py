from enum import Enum


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
    UP_OVERLAP = "up_overlap"      # K1's high is above K2's high, but K1's low is above K2's low
    DOWN_OVERLAP = "down_overlap"  # K1's high is below K2's high, but K1's low is below K2's low
    
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
            if g1 > g2:
                # K1's high is above K2's high
                return cls.UP_OVERLAP
            else:
                # K1's high is below K2's high (g1 < g2)
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
            self.UP_OVERLAP: "上重叠 - K1's high is above K2's high, but K1's low is above K2's low",
            self.DOWN_OVERLAP: "下重叠 - K1's high is below K2's high, but K1's low is below K2's low",
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
    # Test the examples from the user
    print("测试用例:")
    
    # Example 1: K1 contains K2 (D1 <= D2, G1 >= G2)
    relationship1 = get_kbar_relationship(k1_low=10, k1_high=20, k2_low=12, k2_high=18)
    print(f"K1(10-20) vs K2(12-18): {relationship1.value} - {relationship1.get_description()}")
    
    # Example 2: K2 contains K1 (D1 >= D2, G1 <= G2)  
    relationship2 = get_kbar_relationship(k1_low=12, k1_high=18, k2_low=10, k2_high=20)
    print(f"K1(12-18) vs K2(10-20): {relationship2.value} - {relationship2.get_description()}")
    
    # Additional test cases
    relationship3 = get_kbar_relationship(k1_low=10, k1_high=15, k2_low=20, k2_high=25)
    print(f"K1(10-15) vs K2(20-25): {relationship3.value} - {relationship3.get_description()}")
    
    relationship4 = get_kbar_relationship(k1_low=10, k1_high=20, k2_low=10, k2_high=20)
    print(f"K1(10-20) vs K2(10-20): {relationship4.value} - {relationship4.get_description()}")
    
    # Test UP_OVERLAP: K1's high > K2's high, but K1's low > K2's low
    relationship5 = get_kbar_relationship(k1_low=15, k1_high=25, k2_low=10, k2_high=20)
    print(f"K1(15-25) vs K2(10-20): {relationship5.value} - {relationship5.get_description()}")
    
    # Test DOWN_OVERLAP: K1's high < K2's high, but K1's low < K2's low  
    relationship6 = get_kbar_relationship(k1_low=10, k1_high=20, k2_low=15, k2_high=25)
    print(f"K1(10-20) vs K2(15-25): {relationship6.value} - {relationship6.get_description()}")
    
    print("\n使用Kbar对象测试:")
    
    # Create mock Kbar objects for testing
    class MockKbar:
        def __init__(self, low, high):
            self.low = low
            self.high = high
        
        def __repr__(self):
            return f"MockKbar(low={self.low}, high={self.high})"
    
    # Test with Kbar objects
    kbar_obj1 = MockKbar(low=10, high=20)
    kbar_obj2 = MockKbar(low=12, high=18)
    relationship_obj1 = get_kbar_objects_relationship(kbar_obj1, kbar_obj2)
    print(f"{kbar_obj1} vs {kbar_obj2}: {relationship_obj1.value} - {relationship_obj1.get_description()}")
    
    kbar_obj3 = MockKbar(low=15, high=25)
    kbar_obj4 = MockKbar(low=10, high=20)
    relationship_obj2 = get_kbar_objects_relationship(kbar_obj3, kbar_obj4)
    print(f"{kbar_obj3} vs {kbar_obj4}: {relationship_obj2.value} - {relationship_obj2.get_description()}")
