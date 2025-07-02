"""
Kbar Merging Module for Chan Algorithm

This module handles the merging of consecutive kbars according to Chan algorithm rules.
The merging process combines two consecutive kbars based on inclusion relationships.
"""

import logging
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

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
    
    def __post_init__(self):
        """Validate merged K-bar data after initialization"""
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid merged K-bar data: high/low inconsistent with open/close")


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
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            
        Returns:
            True if kbars can be merged, False otherwise
        """
        # Check if kbar2 is completely contained within kbar1
        kbar2_in_kbar1 = (kbar1.high >= kbar2.high and kbar1.low <= kbar2.low)
        
        # Check if kbar1 is completely contained within kbar2
        kbar1_in_kbar2 = (kbar2.high >= kbar1.high and kbar2.low <= kbar1.low)
        
        return kbar2_in_kbar1 or kbar1_in_kbar2
    
    def merge_two_kbars(self, kbar1: 'Kbar', kbar2: 'Kbar') -> MergedKbar:
        """
        Merge two consecutive kbars
        
        Args:
            kbar1: First kbar (earlier in time)
            kbar2: Second kbar (later in time)
            
        Returns:
            Merged kbar
        """
        if not self.can_merge(kbar1, kbar2):
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
                
                if self.can_merge(current_kbar, next_kbar):
                    # Merge the two kbars
                    merged = self.merge_two_kbars(current_kbar, next_kbar)
                    
                    # Continue merging with subsequent kbars if possible
                    j = i + 2
                    while j < len(kbars):
                        temp_kbar = self._merged_to_kbar(merged)
                        if self.can_merge(temp_kbar, kbars[j]):
                            # Merge with next kbar
                            merged = self._merge_merged_with_kbar(merged, kbars[j])
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
    
    def _merge_merged_with_kbar(self, merged_kbar: MergedKbar, kbar: 'Kbar') -> MergedKbar:
        """Merge a MergedKbar with a regular Kbar"""
        temp_kbar = self._merged_to_kbar(merged_kbar)
        if not self.can_merge(temp_kbar, kbar):
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