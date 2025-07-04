"""
Line Types Module for Chan Algorithm

This module contains shared types, enums, and data structures used across
the line processing components of the Chan algorithm.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from ..pen import ChanPen


class LineDirection(Enum):
    """Line direction enumeration"""
    UP = 1      # Upward line (向上线段)
    DOWN = -1   # Downward line (向下线段)


class LineBreakType(Enum):
    """Line breaking type enumeration"""
    NONE = 0           # No breaking
    PARTIAL_BREAK = 1  # Partial breaking
    FULL_BREAK = 2     # Full breaking
    CONFIRMED_BREAK = 3  # Confirmed breaking


class LineStatus(Enum):
    """Line status enumeration"""
    FORMING = 0        # Line is still forming
    COMPLETED = 1      # Line is completed
    BROKEN = 2         # Line has been broken


@dataclass
class LineHistoryEntry:
    """
    Single entry in line history tracking
    
    Records when and why a line event occurred
    """
    timestamp: datetime
    event_type: str  # 'created', 'completed', 'broken', 'status_changed', 'direction_determined'
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)
    pen_involved: Optional['ChanPen'] = None
    price_level: Optional[float] = None
    old_status: Optional[LineStatus] = None
    new_status: Optional[LineStatus] = None
    
    def __repr__(self) -> str:
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"LineHistoryEntry({timestamp_str}: {self.event_type} - {self.reason})"


class LineHistory:
    """
    Line History Tracker
    
    Tracks the complete lifecycle of a ChanLine including creation,
    status changes, breaking events, and completion.
    """
    
    def __init__(self):
        """Initialize empty line history"""
        self.entries: List[LineHistoryEntry] = []
    
    def add_entry(self, event_type: str, reason: str, details: Optional[Dict[str, Any]] = None, 
                  pen_involved: Optional['ChanPen'] = None, price_level: Optional[float] = None,
                  old_status: Optional[LineStatus] = None, new_status: Optional[LineStatus] = None):
        """
        Add a new history entry
        
        Args:
            event_type: Type of event ('created', 'completed', 'broken', etc.)
            reason: Reason for the event
            details: Additional details about the event
            pen_involved: Pen that triggered the event (if applicable)
            price_level: Price level associated with the event
            old_status: Previous status (for status changes)
            new_status: New status (for status changes)
        """
        if details is None:
            details = {}
        entry = LineHistoryEntry(
            timestamp=datetime.now(),
            event_type=event_type,
            reason=reason,
            details=details,
            pen_involved=pen_involved,
            price_level=price_level,
            old_status=old_status,
            new_status=new_status
        )
        self.entries.append(entry)
    
    def get_creation_info(self) -> Optional[LineHistoryEntry]:
        """Get the line creation event"""
        for entry in self.entries:
            if entry.event_type == 'created':
                return entry
        return None
    
    def get_completion_info(self) -> Optional[LineHistoryEntry]:
        """Get the line completion event"""
        for entry in self.entries:
            if entry.event_type == 'completed':
                return entry
        return None
    
    def get_break_info(self) -> Optional[LineHistoryEntry]:
        """Get the line breaking event"""
        for entry in self.entries:
            if entry.event_type == 'broken':
                return entry
        return None
    
    def get_status_changes(self) -> List[LineHistoryEntry]:
        """Get all status change events"""
        return [entry for entry in self.entries if entry.event_type == 'status_changed']
    
    def get_events_by_type(self, event_type: str) -> List[LineHistoryEntry]:
        """Get all events of a specific type"""
        return [entry for entry in self.entries if entry.event_type == event_type]
    
    def get_latest_event(self) -> Optional[LineHistoryEntry]:
        """Get the most recent event"""
        return self.entries[-1] if self.entries else None
    
    def get_timeline(self) -> List[str]:
        """Get a formatted timeline of all events"""
        timeline = []
        for entry in self.entries:
            timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if entry.pen_involved:
                pen_info = f" (Pen: {entry.pen_involved.direction.name})"
            else:
                pen_info = ""
            
            if entry.price_level:
                price_info = f" @ {entry.price_level:.4f}"
            else:
                price_info = ""
            
            timeline.append(f"{timestamp_str}: {entry.event_type.upper()} - {entry.reason}{pen_info}{price_info}")
        
        return timeline
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the line's history"""
        creation_info = self.get_creation_info()
        completion_info = self.get_completion_info()
        break_info = self.get_break_info()
        latest_event = self.get_latest_event()
        
        return {
            'total_events': len(self.entries),
            'created_at': creation_info.timestamp if creation_info else None,
            'creation_reason': creation_info.reason if creation_info else None,
            'completed_at': completion_info.timestamp if completion_info else None,
            'completion_reason': completion_info.reason if completion_info else None,
            'broken_at': break_info.timestamp if break_info else None,
            'break_reason': break_info.reason if break_info else None,
            'break_price': break_info.price_level if break_info else None,
            'status_changes': len(self.get_status_changes()),
            'latest_event': latest_event.event_type if latest_event else None
        }
    
    def __repr__(self) -> str:
        return f"LineHistory({len(self.entries)} events)"


@dataclass
class ChanLine:
    """Chan Line data structure"""
    start_pen: 'ChanPen'
    end_pen: 'ChanPen'
    pens: List['ChanPen'] = field(default_factory=list)
    direction: LineDirection = LineDirection.UP
    high: float = 0.0
    low: float = 0.0
    length: float = 0.0 # 线段幅度
    status: LineStatus = LineStatus.FORMING
    break_type: LineBreakType = LineBreakType.NONE
    break_price: Optional[float] = None
    break_pen: Optional['ChanPen'] = None
    is_global: bool = False  # Whether this is a global line
    confirmed: bool = False
    history: LineHistory = field(default_factory=LineHistory)
    
    def __post_init__(self):
        """Calculate line properties after initialization"""
        self._calculate_properties()
        # Record creation in history
        self.history.add_entry(
            event_type='created',
            reason=f'Line created from {len(self.pens)} pens',
            details={
                'start_pen_direction': self.start_pen.direction.name,
                'end_pen_direction': self.end_pen.direction.name,
                'initial_pen_count': len(self.pens),
                'is_global': self.is_global
            },
            price_level=self.start_price,
            new_status=self.status
        )
    
    def _calculate_properties(self):
        """Calculate line high, low, length, and direction"""
        if not self.pens:
            self.pens = [self.start_pen, self.end_pen]
        
        # Calculate high and low from all pens
        all_highs = [pen.high for pen in self.pens]
        all_lows = [pen.low for pen in self.pens]
        self.high = max(all_highs)
        self.low = min(all_lows)
        
        # Determine direction based on start and end pen endpoints
        old_direction = self.direction
        if self.end_pen.end_price > self.start_pen.start_price:
            self.direction = LineDirection.UP
        else:
            self.direction = LineDirection.DOWN
        
        # Record direction determination if it changed
        if hasattr(self, 'history') and old_direction != self.direction:
            self.history.add_entry(
                event_type='direction_determined',
                reason=f'Direction set to {self.direction.name} based on price movement',
                details={
                    'start_price': self.start_pen.start_price,
                    'end_price': self.end_pen.end_price,
                    'price_change': self.end_pen.end_price - self.start_pen.start_price
                }
            )
        
        # Calculate length
        self.length = self.high - self.low
    
    def update_status(self, new_status: LineStatus, reason: str, pen_involved: Optional['ChanPen'] = None, 
                     price_level: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        """
        Update line status and record in history
        
        Args:
            new_status: New status to set
            reason: Reason for the status change
            pen_involved: Pen that caused the change
            price_level: Price level associated with the change
            details: Additional details about the change
        """
        if details is None:
            details = {}
            
        old_status = self.status
        self.status = new_status
        
        # Record status change in history
        self.history.add_entry(
            event_type='status_changed',
            reason=reason,
            details=details,
            pen_involved=pen_involved,
            price_level=price_level,
            old_status=old_status,
            new_status=new_status
        )
        
        # Also record specific completion or breaking events
        if new_status == LineStatus.COMPLETED:
            self.history.add_entry(
                event_type='completed',
                reason=reason,
                details=details,
                pen_involved=pen_involved,
                price_level=price_level
            )
        elif new_status == LineStatus.BROKEN:
            self.history.add_entry(
                event_type='broken',
                reason=reason,
                details=details,
                pen_involved=pen_involved,
                price_level=price_level
            )
    
    def record_break_attempt(self, break_type: LineBreakType, pen: 'ChanPen', price: float, reason: str):
        """
        Record a line break attempt in history
        
        Args:
            break_type: Type of break attempt
            pen: Pen that attempted to break the line
            price: Price level of the break attempt
            reason: Reason for the break attempt
        """
        self.history.add_entry(
            event_type='break_attempt',
            reason=f'{break_type.name}: {reason}',
            details={
                'break_type': break_type.name,
                'pen_direction': pen.direction.name,
                'pen_high': pen.high,
                'pen_low': pen.low,
                'line_high': self.high,
                'line_low': self.low
            },
            pen_involved=pen,
            price_level=price
        )
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get a summary of this line's history"""
        return self.history.get_summary()
    
    def get_history_timeline(self) -> List[str]:
        """Get a formatted timeline of this line's history"""
        return self.history.get_timeline()
    
    @property
    def start_price(self) -> float:
        """Get line start price"""
        return self.start_pen.start_price
    
    @property
    def end_price(self) -> float:
        """Get line end price"""
        return self.end_pen.end_price
    
    @property
    def start_time(self) -> str:
        """Get line start time"""
        return self.start_pen.start_time
    
    @property
    def end_time(self) -> str:
        """Get line end time"""
        return self.end_pen.end_time
    
    @property
    def pen_count(self) -> int:
        """Get number of pens in this line"""
        return len(self.pens)
    
    def __repr__(self) -> str:
        """String representation for debugging and display"""
        # Format direction with arrow
        direction_arrow = "↗" if self.direction == LineDirection.UP else "↘"
        
        # Format timestamps to be more readable
        start_time_str = self.start_time.replace('+00:00', '').replace('T', ' ')
        end_time_str = self.end_time.replace('+00:00', '').replace('T', ' ')
        if len(start_time_str) > 19:
            start_time_str = start_time_str[:19]
        if len(end_time_str) > 19:
            end_time_str = end_time_str[:19]
        
        # Get start and end peak values
        start_peak = self.start_price
        end_peak = self.end_price
        
        # Calculate price change
        price_change = end_peak - start_peak
        price_change_pct = (price_change / start_peak * 100) if start_peak != 0 else 0
        
        # Format the representation
        return (f"ChanLine({self.direction.name} {direction_arrow} "
                f"Start: {start_time_str} @{start_peak:.2f} → "
                f"End: {end_time_str} @{end_peak:.2f} "
                f"[Δ{price_change:+.2f} ({price_change_pct:+.1f}%)] "
                f"Pens:{self.pen_count} Status:{self.status.name})")


# Event type constants for consistency
class LineEventType:
    """Constants for line event types"""
    CREATED = 'created'
    COMPLETED = 'completed'
    BROKEN = 'broken'
    STATUS_CHANGED = 'status_changed'
    DIRECTION_DETERMINED = 'direction_determined'
    BREAK_ATTEMPT = 'break_attempt'
    SINGLE_PEN_CREATION = 'single_pen_creation'
    GLOBAL_LINE_ASSIGNED = 'global_line_assigned'


# Common line formation methods
class LineFormationMethod:
    """Constants for line formation methods"""
    LINE_STANDARD = 'line_standard'
    SINGLE_PEN = 'single_pen'
    MANUAL = 'manual'


# Break analysis constants
class BreakAnalysisConstants:
    """Constants used in break analysis"""
    DEFAULT_BREAK_THRESHOLD_PERCENT = 0.01  # 1% threshold for full breaks
    DEFAULT_MIN_LINE_PENS = 3
    DEFAULT_BREAK_CONFIRMATION_PENS = 2