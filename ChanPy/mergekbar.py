"""
Kbar Merging Module for Chan Algorithm

This module handles the merging of consecutive kbars according to Chan algorithm rules.
The merging process combines two consecutive kbars based on inclusion relationships.
"""

import logging
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from .chantypes import KBarRelationship, get_kbar_objects_relationship, Direction, KbarShape

if TYPE_CHECKING:
    from .chan import Kbar
    from .context import ChanContext


class ChanMergeKbarDirection:
    """
    Chan Merge Kbar Direction Determiner
    
    This class determines the merge direction for kbars using a fallback hierarchy:
    1. Line direction (if global line is available)
    2. Pen direction (if pens are available, use latest two pens)
    3. Fractal direction (if fractals are available, use latest 5, 3, or 1 fractal)
    4. Relationship-based direction (if kbar relationship is available)
    5. Fallback to UNKNOWN if no Chan structures are available
    """
    
    def __init__(self, context: Optional['ChanContext'] = None):
        """
        Initialize the direction determiner
        
        Args:
            context: ChanContext instance for accessing Chan structures
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.context = context
        self.current_relationship: Optional[KBarRelationship] = None
    
    def determine_merge_direction(self, kbar1: 'Kbar', kbar2: 'Kbar', relationship: Optional[KBarRelationship] = None) -> Direction:
        """
        Determine the merge direction using the fallback hierarchy
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            relationship: Optional KBarRelationship between the two kbars
            
        Returns:
            Direction for merging
        """
        # Store the relationship for use in fallback
        self.current_relationship = relationship
        
        # Step 1: Try to get direction from global line
        line_direction = self._get_line_direction()
        if line_direction != Direction.UNKNOWN:
            self.logger.debug(f"Using line direction: {line_direction}")
            return line_direction
        
        # Step 2: Try to get direction from pens
        pen_direction = self._get_pen_direction()
        if pen_direction != Direction.UNKNOWN:
            self.logger.debug(f"Using pen direction: {pen_direction}")
            return pen_direction
        
        # Step 3: Try to get direction from fractals
        fractal_direction = self._get_fractal_direction()
        if fractal_direction != Direction.UNKNOWN:
            self.logger.debug(f"Using fractal direction: {fractal_direction}")
            return fractal_direction
        
        # Step 4: Fallback to relationship-based and simple heuristic
        self.logger.warning("No Chan structures available, using fallback heuristic")
        return self._get_fallback_direction(kbar1, kbar2)
    
    def _get_line_direction(self) -> Direction:
        """Get direction from global line"""
        if not self.context:
            return Direction.UNKNOWN
        
        try:
            global_line = self.context.get_global_line()
            if global_line is not None:
                # Map LineDirection to Direction
                from .line import LineDirection
                if global_line.direction == LineDirection.UP:
                    return Direction.UP
                elif global_line.direction == LineDirection.DOWN:
                    return Direction.DOWN
        except Exception as e:
            self.logger.debug(f"Failed to get global line: {e}")
        
        return Direction.UNKNOWN
    
    def _get_pen_direction(self) -> Direction:
        """Get direction from the latest two pens"""
        if not self.context:
            return Direction.UNKNOWN
        
        try:
            # Get current state to access the pen list
            state = self.context.get_current_state()
            if not state or len(state.current_pens) < 2:
                return Direction.UNKNOWN
            
            # Get the latest two pens
            latest_pens = state.current_pens[-2:]
            
            # Determine trend direction from the two pens
            pen1, pen2 = latest_pens
            
            # Map PenDirection to Direction
            from .pen import PenDirection
            
            # If both pens are in the same direction, use that direction
            if pen1.direction == pen2.direction:
                if pen1.direction == PenDirection.UP:
                    return Direction.UP
                elif pen1.direction == PenDirection.DOWN:
                    return Direction.DOWN
            
            # If pens alternate, use the direction of the most recent pen
            if pen2.direction == PenDirection.UP:
                return Direction.UP
            elif pen2.direction == PenDirection.DOWN:
                return Direction.DOWN
            
        except Exception as e:
            self.logger.debug(f"Failed to get pen direction: {e}")
        
        return Direction.UNKNOWN
    
    def _get_fractal_direction(self) -> Direction:
        """Get direction from fractals using the fallback hierarchy"""
        if not self.context:
            return Direction.UNKNOWN
        
        try:
            # Get current state to access the fractal list
            state = self.context.get_current_state()
            if not state or not state.current_fractals:
                return Direction.UNKNOWN
            
            fractals = state.current_fractals
            
            # Try latest 5 fractals
            if len(fractals) >= 5:
                direction = self._analyze_fractal_trend(fractals[-5:])
                if direction != Direction.UNKNOWN:
                    return direction
            
            # Try latest 3 fractals  
            if len(fractals) >= 3:
                direction = self._analyze_fractal_trend(fractals[-3:])
                if direction != Direction.UNKNOWN:
                    return direction
            
            # Try last fractal
            if len(fractals) >= 1:
                return self._get_single_fractal_direction(fractals[-1])
            
        except Exception as e:
            self.logger.debug(f"Failed to get fractal direction: {e}")
        
        return Direction.UNKNOWN
    
    def _analyze_fractal_trend(self, fractals: List) -> Direction:
        """
        Analyze the trend direction from a sequence of fractals
        
        Args:
            fractals: List of fractals to analyze
            
        Returns:
            Direction based on fractal trend
        """
        if len(fractals) < 2:
            return Direction.UNKNOWN
        
        # Import here to avoid circular import
        from .fractal import FractalType
        
        # Calculate the overall trend by comparing first and last fractal prices
        first_fractal = fractals[0]
        last_fractal = fractals[-1]
        
        # If the trend is generally upward
        if last_fractal.price > first_fractal.price:
            return Direction.UP
        # If the trend is generally downward
        elif last_fractal.price < first_fractal.price:
            return Direction.DOWN
        else:
            # If prices are equal, look at the fractal types
            # If we end with a bottom fractal, trend might be turning up
            if last_fractal.fractal_type == FractalType.BOTTOM:
                return Direction.UP
            # If we end with a top fractal, trend might be turning down
            elif last_fractal.fractal_type == FractalType.TOP:
                return Direction.DOWN
        
        return Direction.UNKNOWN
    
    def _get_single_fractal_direction(self, fractal) -> Direction:
        """
        Get direction from a single fractal
        
        Args:
            fractal: Single fractal to analyze
            
        Returns:
            Direction based on fractal type
        """
        # Import here to avoid circular import
        from .fractal import FractalType
        
        # If it's a bottom fractal, expect upward movement
        if fractal.fractal_type == FractalType.BOTTOM:
            return Direction.UP
        # If it's a top fractal, expect downward movement
        elif fractal.fractal_type == FractalType.TOP:
            return Direction.DOWN
        
        return Direction.UNKNOWN
    
    def _get_fallback_direction(self, kbar1: 'Kbar', kbar2: 'Kbar') -> Direction:
        """
        Fallback direction determination using relationship and simple heuristic
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            
        Returns:
            Direction based on relationship type and price movement
        """
        # First, try to use the relationship information if available
        if self.current_relationship is not None:
            direction = self._get_direction_from_relationship(self.current_relationship, kbar1, kbar2)
            if direction != Direction.UNKNOWN:
                self.logger.debug(f"Using relationship-based direction: {direction} for relationship: {self.current_relationship}")
                return direction
        
        # Second, try to use KbarShape information if no relationship
        shape_direction = self._get_direction_from_kbar_shape(kbar1, kbar2)
        if shape_direction != Direction.UNKNOWN:
            self.logger.debug(f"Using KbarShape-based direction: {shape_direction}")
            return shape_direction
        
        # Final fallback to simple heuristic based on price movement
        if kbar2.close > kbar1.close:
            return Direction.UP
        elif kbar2.close < kbar1.close:
            return Direction.DOWN
        else:
            return Direction.UNKNOWN
    
    def _get_direction_from_relationship(self, relationship: KBarRelationship, kbar1: 'Kbar', kbar2: 'Kbar') -> Direction:
        """
        Determine merge direction based on the relationship type between two kbars
        
        Args:
            relationship: The KBarRelationship between the two kbars
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            
        Returns:
            Direction based on relationship analysis
        """
        # For containment relationships, analyze the containment pattern
        if relationship == KBarRelationship.K1_CONTAINS_K2:
            # K1 contains K2 - the containing kbar (K1) is dominant
            # If K1 is bullish and K2 is contained within, lean towards up
            if kbar1.close > kbar1.open:
                return Direction.UP
            elif kbar1.close < kbar1.open:
                return Direction.DOWN
            else:
                # If K1 is neutral, check K2's direction
                if kbar2.close > kbar2.open:
                    return Direction.UP
                elif kbar2.close < kbar2.open:
                    return Direction.DOWN
                    
        elif relationship == KBarRelationship.K2_CONTAINS_K1:
            # K2 contains K1 - the newer kbar (K2) is dominant
            # Use K2's direction as it's the containing and more recent kbar
            if kbar2.close > kbar2.open:
                return Direction.UP
            elif kbar2.close < kbar2.open:
                return Direction.DOWN
            else:
                # If K2 is neutral, check K1's direction
                if kbar1.close > kbar1.open:
                    return Direction.UP
                elif kbar1.close < kbar1.open:
                    return Direction.DOWN
                    
        elif relationship == KBarRelationship.IDENTICAL:
            # Same range - use the trend direction
            if kbar2.close > kbar1.close:
                return Direction.UP
            elif kbar2.close < kbar1.close:
                return Direction.DOWN
                
        elif relationship == KBarRelationship.SAME_HIGH_K1_LOWER:
            # Same high, K1 extends lower - K1 is more bearish
            if kbar1.close < kbar1.open:
                return Direction.DOWN
            elif kbar2.close > kbar2.open:
                return Direction.UP
                
        elif relationship == KBarRelationship.SAME_HIGH_K2_LOWER:
            # Same high, K2 extends lower - K2 is more bearish
            if kbar2.close < kbar2.open:
                return Direction.DOWN
            elif kbar1.close > kbar1.open:
                return Direction.UP
                
        elif relationship == KBarRelationship.SAME_LOW_K1_HIGHER:
            # Same low, K1 extends higher - K1 is more bullish
            if kbar1.close > kbar1.open:
                return Direction.UP
            elif kbar2.close < kbar2.open:
                return Direction.DOWN
                
        elif relationship == KBarRelationship.SAME_LOW_K2_HIGHER:
            # Same low, K2 extends higher - K2 is more bullish
            if kbar2.close > kbar2.open:
                return Direction.UP
            elif kbar1.close < kbar1.open:
                return Direction.DOWN
        
        # For other relationships or when no clear direction is determined
        return Direction.UNKNOWN
    
    def _get_direction_from_kbar_shape(self, kbar1: 'Kbar', kbar2: 'Kbar') -> Direction:
        """
        Determine merge direction based on KbarShape analysis
        
        This method analyzes the shapes of both kbars to determine the merge direction.
        It prioritizes the more recent kbar (kbar2) shape but also considers kbar1.
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            
        Returns:
            Direction based on KbarShape analysis
        """
        try:
            # Determine shapes for both kbars
            shape1 = KbarShape.determine_shape(kbar1.open, kbar1.high, kbar1.low, kbar1.close)
            shape2 = KbarShape.determine_shape(kbar2.open, kbar2.high, kbar2.low, kbar2.close)
            
            self.logger.debug(f"Kbar1 shape: {shape1.name}, Kbar2 shape: {shape2.name}")
            
            # Priority 1: If kbar2 (more recent) has a strong directional shape, use it
            if shape2.is_bullish():
                return Direction.UP
            elif shape2.is_bearish():
                return Direction.DOWN
            
            # Priority 2: If kbar2 is doji, check kbar1's shape
            if shape2.is_doji():
                if shape1.is_bullish():
                    return Direction.UP
                elif shape1.is_bearish():
                    return Direction.DOWN
            
            # Priority 3: If neither has clear direction, analyze body sizes and patterns
            # Check for continuation patterns - if both have same bias, continue that direction
            if shape1.is_bullish() and shape2.is_doji():
                # Bullish followed by doji - possible continuation up
                return Direction.UP
            elif shape1.is_bearish() and shape2.is_doji():
                # Bearish followed by doji - possible continuation down
                return Direction.DOWN
            
            # Priority 4: Check for reversal patterns
            # Strong opposite patterns might indicate reversal
            if shape1.is_bullish() and shape2.is_bearish():
                # Bullish to bearish - trend might be turning down
                return Direction.DOWN
            elif shape1.is_bearish() and shape2.is_bullish():
                # Bearish to bullish - trend might be turning up
                return Direction.UP
            
            # If both are doji or no clear pattern, return UNKNOWN
            return Direction.UNKNOWN
            
        except Exception as e:
            self.logger.debug(f"Failed to determine direction from KbarShape: {e}")
            return Direction.UNKNOWN


@dataclass
class MergedKbar:
    """Merged K-bar data structure"""
    timestamp_start: str
    timestamp_end: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    original_count: int = 1  # Number of original kbars merged into this one
    original_kbars: List['Kbar'] = field(default_factory=list)  # List of original raw kbars that were merged
    mergetype: Optional[KBarRelationship] = None  # How this mergekbar was merged
    merge_direction: Direction = Direction.UNKNOWN  # Direction of the merge
    
    def __post_init__(self):
        """Validate merged K-bar data after initialization"""
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid merged K-bar data: high/low inconsistent with open/close")
    
    def __str__(self) -> str:
        """String representation for debugging"""
        direction = "↑" if self.close > self.open else "↓" if self.close < self.open else "→"
        body_size = abs(self.close - self.open)
        range_size = self.high - self.low
        
        # Format timestamps to be more readable
        start_str = self.timestamp_start.replace('+00:00', '').replace('T', ' ')
        end_str = self.timestamp_end.replace('+00:00', '').replace('T', ' ')
        if len(start_str) > 19:
            start_str = start_str[:19]
        if len(end_str) > 19:
            end_str = end_str[:19]
        
        # Add merge info to string representation
        merge_info = f"Type:{self.mergetype.value if self.mergetype else 'None'} Dir:{self.merge_direction.name}"
        
        return (f"MergedKbar({start_str:19s}→{end_str:19s} {direction}\n"
                f"O:{self.open:6.2f} H:{self.high:6.2f} L:{self.low:6.2f} C:{self.close:6.2f} "
                f"V:{self.volume:8d} Body:{body_size:5.2f} Range:{range_size:5.2f} Count:{self.original_count} {merge_info})")
    
    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return self.__str__()


class KbarMerger:
    """
    Kbar Merger Class
    
    Handles the merging of consecutive kbars according to Chan algorithm rules.
    Two kbars are merged if one is completely contained within the other.
    """
    
    def __init__(self, context: Optional['ChanContext'] = None):
        self.logger = logging.getLogger(f"{__name__}")
        self.merged_kbars: List[MergedKbar] = []
        self.context = context
        # Initialize the direction determiner
        self.direction_determiner = ChanMergeKbarDirection(context)
    
    def can_merge(self, kbar1: 'Kbar', kbar2: 'Kbar') -> bool:
        """
        Check if two consecutive kbars can be merged
        
        Two kbars can be merged if they have a containment relationship.
        This excludes overlap-only and completely separated relationships.
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            
        Returns:
            True if kbars can be merged (containment relationship), False otherwise
        """
        relationship = self._get_merge_relationship(kbar1, kbar2)
        return relationship is not None
    
    def _get_merge_relationship(self, kbar1: 'Kbar', kbar2: 'Kbar') -> Optional[KBarRelationship]:
        """
        Get the relationship between two kbars and determine if they can be merged.
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            
        Returns:
            KBarRelationship if kbars can be merged, None if they cannot be merged
        """
        # Get the relationship between the two kbars
        relationship = get_kbar_objects_relationship(kbar1, kbar2)
        
        # Define non-mergeable relationships (overlap and separation)
        non_mergeable_relationships = {
            KBarRelationship.UP_OVERLAP,
            KBarRelationship.DOWN_OVERLAP,
            KBarRelationship.K1_ABOVE_K2,
            KBarRelationship.K1_BELOW_K2
        }
        
        # If it's not an overlap or separation relationship, it's a containment relationship
        # which means the kbars can be merged
        can_merge_result = relationship not in non_mergeable_relationships
        
        self.logger.debug(f"Kbar relationship: {relationship} - Can merge: {can_merge_result}")
        if can_merge_result:
            self.logger.debug(f"Kbar1: {kbar1}")
            self.logger.debug(f"Kbar2: {kbar2}")

        return relationship if can_merge_result else None
    
    def merge_two_kbars(self, kbar1: 'Kbar', kbar2: 'Kbar', merge_direction: Direction, skip_merge_check: bool = False) -> MergedKbar:
        """
        Merge two consecutive kbars
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            merge_direction: Direction for merging (UP, DOWN, or UNKNOWN)
                           - For DOWN merge: low = min(low1, low2), high = min(high1, high2)
                           - For UP merge: low = max(low1, low2), high = max(high1, high2)
                           - For UNKNOWN: uses traditional merge (max high, min low)
            skip_merge_check: If True, skip the merge compatibility check (for performance when already verified)
            
        Returns:
            Merged kbar
        """
        if not skip_merge_check and not self.can_merge(kbar1, kbar2):
            raise ValueError("Cannot merge kbars: no inclusion relationship")
        
        # Determine the merged kbar properties based on merge direction
        if merge_direction == Direction.DOWN:
            # For down merge: min of both highs and lows
            merged_high = min(kbar1.high, kbar2.high)
            merged_low = min(kbar1.low, kbar2.low)
        elif merge_direction == Direction.UP:
            # For up merge: max of both highs and lows
            merged_high = max(kbar1.high, kbar2.high)
            merged_low = max(kbar1.low, kbar2.low)
        else:
            # For UNKNOWN or traditional merge: max high, min low
            merged_high = max(kbar1.high, kbar2.high)
            merged_low = min(kbar1.low, kbar2.low)
        
        # Open is from the first kbar, close is from the second kbar
        merged_open = kbar1.open
        merged_close = kbar2.close
        
        # Volume is sum of both
        merged_volume = kbar1.volume + kbar2.volume

        return MergedKbar(
            timestamp_start=kbar1.timestamp,
            timestamp_end=kbar2.timestamp,
            open=merged_open,
            high=merged_high,
            low=merged_low,
            close=merged_close,
            volume=merged_volume,
            original_count=2,
            mergetype=self._get_merge_relationship(kbar1, kbar2),
            merge_direction=merge_direction
        )
    
    def process_kbar_sequence(self, kbars: List['Kbar']) -> List[MergedKbar]:
        """
        Process a sequence of kbars and return merged kbars
        
        Args:
            kbars: List of original kbars in chronological order
            
        Returns:
            List of merged kbars
        """
        if len(kbars) < 2:
            # Convert single kbar to MergedKbar
            if len(kbars) == 1:
                kbar = kbars[0]
                single_merged = MergedKbar(
                    timestamp_start=kbar.timestamp,
                    timestamp_end=kbar.timestamp,
                    open=kbar.open,
                    high=kbar.high,
                    low=kbar.low,
                    close=kbar.close,
                    volume=kbar.volume,
                    original_count=1,
                    mergetype=None,  # No actual merging happened
                    merge_direction=Direction.UNKNOWN
                )
                self.logger.debug(f"Single kbar converted to MergedKbar: {single_merged}")
                return [single_merged]
            return []
        
        merged_result = []
        i = 0
        
        while i < len(kbars):
            current_kbar = kbars[i]
            
            # Try to merge with next kbar
            if i + 1 < len(kbars):
                next_kbar = kbars[i + 1]
                
                # Check relationship once and reuse result
                relationship = self._get_merge_relationship(current_kbar, next_kbar)
                if relationship is not None:
                    # Determine merge direction
                    merge_direction = self._determine_merge_direction(current_kbar, next_kbar)
                    
                    # Merge the two kbars (skip merge check since we already verified)
                    merged = self.merge_two_kbars(current_kbar, next_kbar, merge_direction, skip_merge_check=True)
                    
                    # print the merged kbar
                    self.logger.debug(f"Merged kbar: {merged}")
                    

                    # Continue merging with subsequent kbars if possible
                    j = i + 2
                    while j < len(kbars):
                        temp_kbar = self._merged_to_kbar(merged)
                        next_relationship = self._get_merge_relationship(temp_kbar, kbars[j])
                        if next_relationship is not None:
                            # Determine merge direction for subsequent merge
                            subsequent_merge_direction = self._determine_merge_direction(temp_kbar, kbars[j])
                            
                            # Merge with next kbar (skip merge check since we already verified)
                            merged = self._merge_merged_with_kbar(merged, kbars[j], subsequent_merge_direction, skip_merge_check=True)
                            j += 1
                        else:
                            break
                    
                    merged_result.append(merged)
                    i = j  # Skip all merged kbars
                else:
                    # Cannot merge, add current kbar as single merged kbar
                    single_merged = MergedKbar(
                        timestamp_start=current_kbar.timestamp,
                        timestamp_end=current_kbar.timestamp,
                        open=current_kbar.open,
                        high=current_kbar.high,
                        low=current_kbar.low,
                        close=current_kbar.close,
                        volume=current_kbar.volume,
                        original_count=1,
                        mergetype=None,  # No actual merging happened
                        merge_direction=Direction.UNKNOWN
                    )
                    merged_result.append(single_merged)
                    self.logger.debug(f"kbar [{i}] added to merged result: {single_merged}")
                    i += 1
            else:
                # Add the last kbar as single merged kbar
                merged_result.append(MergedKbar(
                    timestamp_start=current_kbar.timestamp,
                    timestamp_end=current_kbar.timestamp,
                    open=current_kbar.open,
                    high=current_kbar.high,
                    low=current_kbar.low,
                    close=current_kbar.close,
                    volume=current_kbar.volume,
                    original_count=1,
                    mergetype=None,  # No actual merging happened
                    merge_direction=Direction.UNKNOWN
                ))
                i += 1
        
        self.merged_kbars = merged_result
        self.logger.debug(f"Merged {len(kbars)} kbars into {len(merged_result)} merged kbars")
        
        return merged_result
    
    def _merged_to_kbar(self, merged_kbar: MergedKbar) -> 'Kbar':
        """Convert MergedKbar to Kbar for compatibility"""
        from .chan import Kbar  # Import here to avoid circular import
        return Kbar(
            timestamp=merged_kbar.timestamp_end,
            open=merged_kbar.open,
            high=merged_kbar.high,
            low=merged_kbar.low,
            close=merged_kbar.close,
            volume=merged_kbar.volume
        )
    
    def _merge_merged_with_kbar(self, merged_kbar: MergedKbar, kbar: 'Kbar', merge_direction: Direction = Direction.UNKNOWN, skip_merge_check: bool = False) -> MergedKbar:
        """
        Merge a MergedKbar with a regular Kbar
        
        Args:
            merged_kbar: The existing merged kbar
            kbar: The kbar to merge with
            merge_direction: Direction for merging (UP, DOWN, or UNKNOWN)
            skip_merge_check: If True, skip the merge compatibility check
            
        Returns:
            New MergedKbar with the kbar merged in
        """
        temp_kbar = self._merged_to_kbar(merged_kbar)
        if not skip_merge_check and not self.can_merge(temp_kbar, kbar):
            raise ValueError("Cannot merge: no inclusion relationship")
        
        # Apply merge direction logic
        if merge_direction == Direction.DOWN:
            # For down merge: min of both highs and lows
            new_high = min(merged_kbar.high, kbar.high)
            new_low = min(merged_kbar.low, kbar.low)
        elif merge_direction == Direction.UP:
            # For up merge: max of both highs and lows
            new_high = max(merged_kbar.high, kbar.high)
            new_low = max(merged_kbar.low, kbar.low)
        else:
            # For UNKNOWN or traditional merge: max high, min low
            new_high = max(merged_kbar.high, kbar.high)
            new_low = min(merged_kbar.low, kbar.low)

        return MergedKbar(
            timestamp_start=merged_kbar.timestamp_start,
            timestamp_end=kbar.timestamp,
            open=merged_kbar.open,
            high=new_high,
            low=new_low,
            close=kbar.close,
            volume=merged_kbar.volume + kbar.volume,
            original_count=merged_kbar.original_count + 1,
            mergetype=self._get_merge_relationship(temp_kbar, kbar),
            merge_direction=merge_direction
        )
    
    def get_merge_direction(self, merged_kbar: MergedKbar) -> Direction:
        """
        Determine the direction of a merged kbar
        
        Args:
            merged_kbar: The merged kbar to analyze
            
        Returns:
            Direction: The direction of the merged kbar
        """
        if merged_kbar.close > merged_kbar.open:
            return Direction.UP
        elif merged_kbar.close < merged_kbar.open:
            return Direction.DOWN
        else:
            return Direction.UNKNOWN
    
    def get_merged_kbars(self) -> List[MergedKbar]:
        """Get the list of merged kbars"""
        return self.merged_kbars.copy()
    
    def clear(self):
        """Clear all merged kbars"""
        self.merged_kbars.clear()
        self.logger.debug("Cleared all merged kbars")
    
    def _determine_merge_direction(self, kbar1: 'Kbar', kbar2: 'Kbar') -> Direction:
        """
        Determine the merge direction based on the relationship between two kbars
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            
        Returns:
            Direction: The merge direction to use
        """
        # Get the relationship between the two kbars
        relationship = self._get_merge_relationship(kbar1, kbar2)
        
        # Use the ChanMergeKbarDirection class to determine the direction
        return self.direction_determiner.determine_merge_direction(kbar1, kbar2, relationship) 