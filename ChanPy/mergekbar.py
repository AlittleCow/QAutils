"""
Kbar Merging Module for Chan Algorithm

This module handles the merging of consecutive kbars according to Chan algorithm rules.
The merging process combines two consecutive kbars based on inclusion relationships.
"""

import logging
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from .chantypes import KBarRelationship, get_kbar_objects_relationship, Direction

if TYPE_CHECKING:
    from .chan import Kbar
    from .context import ChanContext


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
                return [MergedKbar(
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
                )]
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
        # Check if current line exists in chan context
        if self.context:
            try:
                global_line = self.context.get_global_line()
                self.logger.debug(f"Global line: {global_line}")
                if global_line is not None:
                    # Map LineDirection to Direction
                    from .line import LineDirection
                    if global_line.direction == LineDirection.UP:
                        return Direction.UP
                    elif global_line.direction == LineDirection.DOWN:
                        return Direction.DOWN
                    else:
                        # If line direction is unknown, fall back to current method
                        pass
            except Exception as e:
                self.logger.debug(f"Failed to get global line from context: {e}")
        
        # Fallback to current method if no current line exists or context unavailable
        # Simple heuristic: if both kbars are generally trending in the same direction,
        # use that direction. Otherwise, use UNKNOWN for traditional merge behavior.
        
        kbar1_direction = Direction.UP if kbar2.close > kbar1.close else Direction.DOWN if kbar2.close < kbar1.close else Direction.UNKNOWN
        
        # You can add more sophisticated logic here based on your specific requirements
        # For now, return UNKNOWN to maintain existing behavior
        return Direction.UNKNOWN 