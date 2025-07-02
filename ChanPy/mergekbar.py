"""
Kbar Merging Module for Chan Algorithm

This module handles the merging of consecutive kbars according to Chan algorithm rules.
The merging process combines two consecutive kbars based on inclusion relationships.
"""

import logging
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from .chantypes import KBarRelationship, get_kbar_objects_relationship

if TYPE_CHECKING:
    from .chan import Kbar


class MergeDirection(Enum):
    """Direction for kbar merging"""
    UP = 1
    DOWN = -1
    UNKNOWN = 0


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
        
        return (f"MergedKbar({start_str:19s}→{end_str:19s} {direction}\n"
                f"O:{self.open:6.2f} H:{self.high:6.2f} L:{self.low:6.2f} C:{self.close:6.2f} "
                f"V:{self.volume:8d} Body:{body_size:5.2f} Range:{range_size:5.2f} Count:{self.original_count})")
    
    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return self.__str__()


class KbarMerger:
    """
    Kbar Merger Class
    
    Handles the merging of consecutive kbars according to Chan algorithm rules.
    Two kbars are merged if one is completely contained within the other.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}")
        self.merged_kbars: List[MergedKbar] = []
    
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
    
    def merge_two_kbars(self, kbar1: 'Kbar', kbar2: 'Kbar', skip_merge_check: bool = False) -> MergedKbar:
        """
        Merge two consecutive kbars
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            skip_merge_check: If True, skip the merge compatibility check (for performance when already verified)
            
        Returns:
            Merged kbar
        """
        if not skip_merge_check and not self.can_merge(kbar1, kbar2):
            raise ValueError("Cannot merge kbars: no inclusion relationship")
        
        # Determine the merged kbar properties
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
            original_count=2
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
            # Convert single kbar to merged format
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
                    original_count=1
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
                    # Merge the two kbars (skip merge check since we already verified)
                    merged = self.merge_two_kbars(current_kbar, next_kbar, skip_merge_check=True)
                    
                    # print the merged kbar
                    self.logger.debug(f"Merged kbar: {merged}")
                    

                    # Continue merging with subsequent kbars if possible
                    j = i + 2
                    while j < len(kbars):
                        temp_kbar = self._merged_to_kbar(merged)
                        next_relationship = self._get_merge_relationship(temp_kbar, kbars[j])
                        if next_relationship is not None:
                            # Merge with next kbar (skip merge check since we already verified)
                            merged = self._merge_merged_with_kbar(merged, kbars[j], skip_merge_check=True)
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
                        original_count=1
                    )
                    merged_result.append(single_merged)
                    i += 1
            else:
                # Last kbar, add as single merged kbar
                single_merged = MergedKbar(
                    timestamp_start=current_kbar.timestamp,
                    timestamp_end=current_kbar.timestamp,
                    open=current_kbar.open,
                    high=current_kbar.high,
                    low=current_kbar.low,
                    close=current_kbar.close,
                    volume=current_kbar.volume,
                    original_count=1
                )
                merged_result.append(single_merged)
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
    
    def _merge_merged_with_kbar(self, merged_kbar: MergedKbar, kbar: 'Kbar', skip_merge_check: bool = False) -> MergedKbar:
        """Merge a MergedKbar with a regular Kbar"""
        temp_kbar = self._merged_to_kbar(merged_kbar)
        if not skip_merge_check and not self.can_merge(temp_kbar, kbar):
            raise ValueError("Cannot merge: no inclusion relationship")
        
        return MergedKbar(
            timestamp_start=merged_kbar.timestamp_start,
            timestamp_end=kbar.timestamp,
            open=merged_kbar.open,
            high=max(merged_kbar.high, kbar.high),
            low=min(merged_kbar.low, kbar.low),
            close=kbar.close,
            volume=merged_kbar.volume + kbar.volume,
            original_count=merged_kbar.original_count + 1
        )
    
    def get_merge_direction(self, merged_kbar: MergedKbar) -> MergeDirection:
        """
        Determine the direction of a merged kbar
        
        Args:
            merged_kbar: The merged kbar to analyze
            
        Returns:
            Direction of the merged kbar
        """
        if merged_kbar.close > merged_kbar.open:
            return MergeDirection.UP
        elif merged_kbar.close < merged_kbar.open:
            return MergeDirection.DOWN
        else:
            return MergeDirection.UNKNOWN
    
    def get_merged_kbars(self) -> List[MergedKbar]:
        """Get the list of merged kbars"""
        return self.merged_kbars.copy()
    
    def clear(self):
        """Clear all merged kbars"""
        self.merged_kbars.clear()
        self.logger.debug("Cleared all merged kbars") 