"""
Line Processing Module for Chan Algorithm

This module handles the formation of lines (线段) from pens and the analysis
of line breaking patterns. Lines are formed from sequences of pens and
represent higher-level trend structures in the Chan algorithm.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from .pen import ChanPen, PenDirection, PenBreakType


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
class ChanLine:
    """Chan Line data structure"""
    start_pen: ChanPen
    end_pen: ChanPen
    pens: List[ChanPen] = field(default_factory=list)
    direction: LineDirection = LineDirection.UP
    high: float = 0.0
    low: float = 0.0
    length: float = 0.0
    status: LineStatus = LineStatus.FORMING
    break_type: LineBreakType = LineBreakType.NONE
    break_price: Optional[float] = None
    break_pen: Optional[ChanPen] = None
    is_global: bool = False  # Whether this is a global line
    confirmed: bool = False
    
    def __post_init__(self):
        """Calculate line properties after initialization"""
        self._calculate_properties()
    
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
        if self.end_pen.end_price > self.start_pen.start_price:
            self.direction = LineDirection.UP
        else:
            self.direction = LineDirection.DOWN
        
        # Calculate length
        self.length = self.high - self.low
    
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


class LineProcessor:
    """
    Line Processor Class
    
    Processes pens to form lines according to Chan algorithm rules.
    Handles line breaking analysis and maintains global line state.
    """
    
    def __init__(self, min_line_pens: int = 3, break_confirmation_pens: int = 2):
        """
        Initialize Line Processor
        
        Args:
            min_line_pens: Minimum number of pens required for a valid line
            break_confirmation_pens: Number of pens needed to confirm a line break
        """
        self.logger = logging.getLogger(f"{__name__}")
        self.min_line_pens = min_line_pens
        self.break_confirmation_pens = break_confirmation_pens
        self.lines: List[ChanLine] = []
        self.global_line: Optional[ChanLine] = None
        self.current_forming_line: Optional[ChanLine] = None
    
    def can_form_line(self, pens: List[ChanPen]) -> bool:
        """
        Check if a sequence of pens can form a valid line
        
        Args:
            pens: List of pens to check
            
        Returns:
            True if pens can form a line
        """
        if len(pens) < self.min_line_pens:
            return False
        
        # Check that pens alternate in direction
        for i in range(len(pens) - 1):
            if pens[i].direction == pens[i + 1].direction:
                return False
        
        # Additional line formation rules can be added here
        return True
    
    def create_line(self, pens: List[ChanPen]) -> Optional[ChanLine]:
        """
        Create a line from a sequence of pens
        
        Args:
            pens: List of pens to form the line
            
        Returns:
            ChanLine object if valid, None otherwise
        """
        if not self.can_form_line(pens):
            return None
        
        line = ChanLine(
            start_pen=pens[0],
            end_pen=pens[-1],
            pens=pens.copy(),
            status=LineStatus.COMPLETED,
            confirmed=True
        )
        
        return line
    
    def identify_line_standard(self, pens: List[ChanPen]) -> List[ChanLine]:
        """
        Identify lines using Chan line standard
        
        Args:
            pens: List of pens in chronological order
            
        Returns:
            List of identified lines
        """
        if len(pens) < self.min_line_pens:
            return []
        
        lines = []
        i = 0
        
        while i <= len(pens) - self.min_line_pens:
            # Try to form a line starting from pen i
            for j in range(i + self.min_line_pens - 1, len(pens)):
                candidate_pens = pens[i:j + 1]
                
                if self.can_form_line(candidate_pens):
                    # Check if this is a valid line endpoint
                    if self._is_valid_line_endpoint(candidate_pens):
                        line = self.create_line(candidate_pens)
                        if line:
                            lines.append(line)
                            self.logger.debug(f"Created {line.direction.name} line with "
                                            f"{len(candidate_pens)} pens, length: {line.length:.4f}")
                            i = j  # Skip to next potential line start
                            break
            else:
                i += 1  # Move to next pen if no line found
        
        return lines
    
    def _is_valid_line_endpoint(self, pens: List[ChanPen]) -> bool:
        """
        Check if the pen sequence forms a valid line with proper endpoints
        
        Args:
            pens: List of pens to check
            
        Returns:
            True if endpoint is valid
        """
        # Simplified validation - can be enhanced with more Chan rules
        if len(pens) < 3:
            return False
        
        # Check that the line has proper structure
        # For example, an up-line should end with a down pen that breaks the previous structure
        last_pen = pens[-1]
        second_last_pen = pens[-2]
        
        # Basic validation: ensure the last pen creates a proper reversal
        if last_pen.direction != second_last_pen.direction:
            return True
        
        return False
    
    def process_pens(self, pens: List[ChanPen]) -> List[ChanLine]:
        """
        Process a list of pens to create lines
        
        Args:
            pens: List of pens in chronological order
            
        Returns:
            List of valid lines
        """
        lines = self.identify_line_standard(pens)
        self.lines = lines
        
        # Set the first line as global line if no global line exists
        if lines and not self.global_line:
            self.global_line = lines[0]
            self.global_line.is_global = True
            self.logger.info(f"Set global line: {self.global_line.direction.name} "
                           f"from {self.global_line.start_time} to {self.global_line.end_time}")
        
        self.logger.info(f"Created {len(lines)} lines from {len(pens)} pens")
        return lines
    
    def analyze_line_breaking(self, line: ChanLine, new_pens: List[ChanPen]) -> LineBreakType:
        """
        Analyze if a line is being broken by new pens
        
        Args:
            line: The line to analyze
            new_pens: New pens to check for breaking
            
        Returns:
            Type of line breaking
        """
        if not new_pens:
            return LineBreakType.NONE
        
        latest_pen = new_pens[-1]
        
        # Check for breaking based on line direction
        if line.direction == LineDirection.UP:
            # For upward line, breaking means a pen goes below the line's low
            if latest_pen.low < line.low:
                line.break_price = latest_pen.low
                line.break_pen = latest_pen
                
                # Check if it's a confirmed break
                if len(new_pens) >= self.break_confirmation_pens:
                    # Check if multiple pens confirm the break
                    confirming_pens = [pen for pen in new_pens[-self.break_confirmation_pens:] 
                                     if pen.low < line.low]
                    if len(confirming_pens) >= self.break_confirmation_pens:
                        line.break_type = LineBreakType.CONFIRMED_BREAK
                        line.status = LineStatus.BROKEN
                        return LineBreakType.CONFIRMED_BREAK
                
                # Determine if it's full or partial break
                break_threshold = line.low * 0.99  # 1% below
                if latest_pen.low < break_threshold:
                    line.break_type = LineBreakType.FULL_BREAK
                else:
                    line.break_type = LineBreakType.PARTIAL_BREAK
                
                return line.break_type
        
        else:  # Downward line
            # For downward line, breaking means a pen goes above the line's high
            if latest_pen.high > line.high:
                line.break_price = latest_pen.high
                line.break_pen = latest_pen
                
                # Check if it's a confirmed break
                if len(new_pens) >= self.break_confirmation_pens:
                    confirming_pens = [pen for pen in new_pens[-self.break_confirmation_pens:] 
                                     if pen.high > line.high]
                    if len(confirming_pens) >= self.break_confirmation_pens:
                        line.break_type = LineBreakType.CONFIRMED_BREAK
                        line.status = LineStatus.BROKEN
                        return LineBreakType.CONFIRMED_BREAK
                
                # Determine if it's full or partial break
                break_threshold = line.high * 1.01  # 1% above
                if latest_pen.high > break_threshold:
                    line.break_type = LineBreakType.FULL_BREAK
                else:
                    line.break_type = LineBreakType.PARTIAL_BREAK
                
                return line.break_type
        
        line.break_type = LineBreakType.NONE
        line.break_price = None
        line.break_pen = None
        return LineBreakType.NONE
    
    def update_global_line_status(self, new_pens: List[ChanPen]):
        """
        Update the global line status based on new pens
        
        Args:
            new_pens: New pens to analyze
        """
        if not self.global_line or not new_pens:
            return
        
        # Analyze if global line is broken
        break_type = self.analyze_line_breaking(self.global_line, new_pens)
        
        if break_type == LineBreakType.CONFIRMED_BREAK:
            self.logger.info(f"Global line broken at price {self.global_line.break_price}")
            
            # Try to form new global line from recent pens
            if len(new_pens) >= self.min_line_pens:
                new_line = self.create_line(new_pens[-self.min_line_pens:])
                if new_line:
                    self.global_line = new_line
                    self.global_line.is_global = True
                    self.logger.info(f"New global line formed: {self.global_line.direction.name}")
    
    def get_upward_lines(self) -> List[ChanLine]:
        """Get all upward lines"""
        return [line for line in self.lines if line.direction == LineDirection.UP]
    
    def get_downward_lines(self) -> List[ChanLine]:
        """Get all downward lines"""
        return [line for line in self.lines if line.direction == LineDirection.DOWN]
    
    def get_broken_lines(self) -> List[ChanLine]:
        """Get all broken lines"""
        return [line for line in self.lines if line.status == LineStatus.BROKEN]
    
    def get_active_lines(self) -> List[ChanLine]:
        """Get all active (non-broken) lines"""
        return [line for line in self.lines if line.status != LineStatus.BROKEN]
    
    def get_latest_line(self) -> Optional[ChanLine]:
        """Get the most recent line"""
        return self.lines[-1] if self.lines else None
    
    def get_global_line(self) -> Optional[ChanLine]:
        """Get the current global line"""
        return self.global_line
    
    def filter_lines_by_length(self, min_length: float) -> List[ChanLine]:
        """
        Filter lines by minimum length
        
        Args:
            min_length: Minimum line length
            
        Returns:
            List of lines meeting the length requirement
        """
        return [line for line in self.lines if line.length >= min_length]
    
    def get_line_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the lines
        
        Returns:
            Dictionary with line statistics
        """
        if not self.lines:
            return {
                'total_lines': 0,
                'upward_lines': 0,
                'downward_lines': 0,
                'broken_lines': 0,
                'active_lines': 0,
                'average_length': 0.0,
                'average_pen_count': 0.0,
                'global_line_direction': None,
                'global_line_broken': False
            }
        
        upward_count = len(self.get_upward_lines())
        downward_count = len(self.get_downward_lines())
        broken_count = len(self.get_broken_lines())
        active_count = len(self.get_active_lines())
        lengths = [line.length for line in self.lines]
        pen_counts = [line.pen_count for line in self.lines]
        
        return {
            'total_lines': len(self.lines),
            'upward_lines': upward_count,
            'downward_lines': downward_count,
            'broken_lines': broken_count,
            'active_lines': active_count,
            'average_length': sum(lengths) / len(lengths) if lengths else 0.0,
            'average_pen_count': sum(pen_counts) / len(pen_counts) if pen_counts else 0.0,
            'global_line_direction': self.global_line.direction.name if self.global_line else None,
            'global_line_broken': self.global_line.status == LineStatus.BROKEN if self.global_line else False
        }
    
    def validate_line_sequence(self) -> bool:
        """
        Validate that the line sequence follows Chan rules
        
        Returns:
            True if sequence is valid
        """
        if len(self.lines) < 2:
            return True
        
        # Check that lines don't overlap inappropriately
        for i in range(len(self.lines) - 1):
            current_line = self.lines[i]
            next_line = self.lines[i + 1]
            
            # Ensure proper chronological order
            if current_line.end_time >= next_line.start_time:
                return False
        
        return True
    
    def clear(self):
        """Clear all lines and reset global line"""
        self.lines.clear()
        self.global_line = None
        self.current_forming_line = None
        self.logger.debug("Cleared all lines and reset global line")
    
    def get_lines(self) -> List[ChanLine]:
        """Get copy of all lines"""
        return self.lines.copy()
    
    def set_parameters(self, min_line_pens: Optional[int] = None, break_confirmation_pens: Optional[int] = None):
        """
        Set line processing parameters
        
        Args:
            min_line_pens: Minimum number of pens for a line
            break_confirmation_pens: Number of pens to confirm break
        """
        if min_line_pens is not None:
            self.min_line_pens = min_line_pens
        if break_confirmation_pens is not None:
            self.break_confirmation_pens = break_confirmation_pens
        
        self.logger.info(f"Updated parameters: min_line_pens={self.min_line_pens}, "
                        f"break_confirmation_pens={self.break_confirmation_pens}")
    
    def get_line_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current line analysis
        
        Returns:
            Dictionary with line analysis summary
        """
        latest_line = self.get_latest_line()
        
        return {
            'total_lines': len(self.lines),
            'global_line_active': self.global_line is not None and self.global_line.status != LineStatus.BROKEN,
            'latest_line': {
                'direction': latest_line.direction.name if latest_line else None,
                'status': latest_line.status.name if latest_line else None,
                'pen_count': latest_line.pen_count if latest_line else 0,
                'length': latest_line.length if latest_line else 0.0,
                'broken': latest_line.status == LineStatus.BROKEN if latest_line else False
            } if latest_line else None,
            'global_line': {
                'direction': self.global_line.direction.name if self.global_line else None,
                'status': self.global_line.status.name if self.global_line else None,
                'broken': self.global_line.status == LineStatus.BROKEN if self.global_line else False,
                'break_price': self.global_line.break_price if self.global_line else None
            } if self.global_line else None
        } 