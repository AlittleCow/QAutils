"""
Chan Algorithm Implementation for QAutils

This module implements the Chan algorithm for technical analysis,
including identification of pens (笔), segments (线段), and central areas (中枢).
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


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


@dataclass
class CentralArea:
    """Central area structure in Chan analysis (中枢)"""
    high: float
    low: float
    start_time: str
    end_time: str
    segments: List[Segment] = field(default_factory=list)
    level: int = 1  # 中枢级别
    confirmed: bool = False
    
    @property
    def range_height(self) -> float:
        """Height of central area"""
        return self.high - self.low
    
    @property
    def center_price(self) -> float:
        """Center price of central area"""
        return (self.high + self.low) / 2


class ChanIndicator:
    """
    Chan Algorithm Indicator Class
    
    This class implements the Chan algorithm for technical analysis,
    processing K-bar data to identify pens, segments, and central areas.
    """
    
    def __init__(self, db_manager, symbol: str, exchange: str = "SH", 
                 period: str = "1min", max_history: int = 1000):
        """
        Initialize Chan Indicator
        
        Args:
            db_manager: Database manager instance from db.py
            symbol: Stock symbol
            exchange: Exchange code (default: "SH")  
            period: Time period (default: "1min")
            max_history: Maximum number of K-bars to keep in memory
        """
        self.db_manager = db_manager
        self.symbol = symbol
        self.exchange = exchange
        self.period = period
        self.max_history = max_history
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{symbol}.{exchange}")
        
        # Data storage
        self.kbars: List[Kbar] = []
        self.fractional_points: List[FractionalPoint] = []
        self.pens: List[Pen] = []
        self.segments: List[Segment] = []
        self.central_areas: List[CentralArea] = []
        
        # Analysis parameters
        self.min_pen_bars = 5  # Minimum bars for a valid pen
        self.min_segment_pens = 3  # Minimum pens for a valid segment
        self.central_area_threshold = 0.618  # Threshold for central area detection
        
        # State tracking
        self.last_processed_index = -1
        self.current_trend = Direction.UNKNOWN
        
        # Load historical data
        self._load_historical_data()
        
        self.logger.info(f"ChanIndicator initialized for {symbol}.{exchange} ({period})")
    
    def _load_historical_data(self):
        """Load historical K-bar data from database"""
        if not self.db_manager:
            self.logger.warning("Database manager not available, starting with empty data")
            return
        
        try:
            # Get historical data from database
            df = self.db_manager.get_kbar_data(
                symbol=self.symbol,
                exchange=self.exchange, 
                period=self.period,
                limit=self.max_history
            )
            
            if not df.empty:
                # Convert DataFrame to Kbar objects
                for _, row in df.iterrows():
                    # Use 'ts' column name as returned by database
                    timestamp_col = 'ts' if 'ts' in row else 'timestamp'
                    kbar = Kbar(
                        timestamp=str(row[timestamp_col]),
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume'])
                    )
                    self.kbars.append(kbar)
                
                self.logger.info(f"Loaded {len(self.kbars)} historical K-bars")
                
                # Perform initial analysis on historical data
                self._analyze_all_data()
                
            else:
                self.logger.info("No historical data found, starting fresh")
                
        except Exception as e:
            self.logger.error(f"Failed to load historical data: {e}")
    
    def onKbar(self, kbar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process new K-bar data and perform Chan analysis
        
        Args:
            kbar_data: New K-bar data dictionary
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Convert input data to Kbar object
            new_kbar = Kbar(
                timestamp=str(kbar_data.get('timestamp', '')),
                open=float(kbar_data.get('open', 0)),
                high=float(kbar_data.get('high', 0)),
                low=float(kbar_data.get('low', 0)),
                close=float(kbar_data.get('close', 0)),
                volume=int(kbar_data.get('volume', 0))
            )
            
            # Add new K-bar to history
            self.kbars.append(new_kbar)
            
            # Maintain maximum history limit
            if len(self.kbars) > self.max_history:
                removed_count = len(self.kbars) - self.max_history
                self.kbars = self.kbars[removed_count:]
                # Adjust indices in existing structures
                self._adjust_indices_after_removal(removed_count)
            
            # Perform incremental analysis
            results = self._analyze_incremental()
            
            self.logger.debug(f"Processed new K-bar at {new_kbar.timestamp}")
            
            return {
                'status': 'success',
                'symbol': self.symbol,
                'exchange': self.exchange,
                'period': self.period,
                'timestamp': new_kbar.timestamp,
                'analysis_results': results,
                'data_summary': self._get_data_summary()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing K-bar: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'symbol': self.symbol,
                'exchange': self.exchange
            }
    
    def _analyze_all_data(self):
        """Perform complete analysis on all historical data"""
        if len(self.kbars) < 3:
            return
        
        # Clear existing analysis
        self.fractional_points.clear()
        self.pens.clear()
        self.segments.clear()
        self.central_areas.clear()
        
        # Step 1: Identify fractional points
        self._identify_fractional_points()
        
        # Step 2: Form pens from fractional points
        self._form_pens()
        
        # Step 3: Form segments from pens
        self._form_segments()
        
        # Step 4: Identify central areas
        self._identify_central_areas()
        
        self.last_processed_index = len(self.kbars) - 1
        
        self.logger.debug(f"Complete analysis: {len(self.fractional_points)} points, "
                         f"{len(self.pens)} pens, {len(self.segments)} segments, "
                         f"{len(self.central_areas)} central areas")
    
    def _analyze_incremental(self) -> Dict[str, Any]:
        """Perform incremental analysis on new data"""
        current_index = len(self.kbars) - 1
        
        if current_index <= self.last_processed_index:
            return self._get_current_status()
        
        # Check for new fractional points
        new_points = self._check_new_fractional_points(self.last_processed_index + 1)
        
        # Update pens if new fractional points found
        if new_points:
            self._update_pens()
            self._update_segments()
            self._update_central_areas()
        
        self.last_processed_index = current_index
        
        return self._get_current_status()
    
    def _identify_fractional_points(self):
        """Identify fractional points (分型) in K-bar data"""
        if len(self.kbars) < 3:
            return
        
        for i in range(1, len(self.kbars) - 1):
            current = self.kbars[i]
            prev = self.kbars[i - 1]
            next_bar = self.kbars[i + 1]
            
            # Check for top fractional point (顶分型)
            if (current.high > prev.high and current.high > next_bar.high and
                current.low >= prev.low and current.low >= next_bar.low):
                
                point = FractionalPoint(
                    index=i,
                    timestamp=current.timestamp,
                    price=current.high,
                    point_type=PenType.TOP,
                    kbar=current,
                    confirmed=True
                )
                self.fractional_points.append(point)
            
            # Check for bottom fractional point (底分型)
            elif (current.low < prev.low and current.low < next_bar.low and
                  current.high <= prev.high and current.high <= next_bar.high):
                
                point = FractionalPoint(
                    index=i,
                    timestamp=current.timestamp,
                    price=current.low,
                    point_type=PenType.BOTTOM,
                    kbar=current,
                    confirmed=True
                )
                self.fractional_points.append(point)
    
    def _check_new_fractional_points(self, start_index: int) -> List[FractionalPoint]:
        """Check for new fractional points from start_index"""
        new_points = []
        
        for i in range(max(1, start_index), len(self.kbars) - 1):
            current = self.kbars[i]
            prev = self.kbars[i - 1]
            next_bar = self.kbars[i + 1]
            
            # Skip if point already exists at this index
            if any(point.index == i for point in self.fractional_points):
                continue
            
            # Check for fractional points
            if (current.high > prev.high and current.high > next_bar.high and
                current.low >= prev.low and current.low >= next_bar.low):
                
                point = FractionalPoint(
                    index=i,
                    timestamp=current.timestamp,
                    price=current.high,
                    point_type=PenType.TOP,
                    kbar=current,
                    confirmed=True
                )
                self.fractional_points.append(point)
                new_points.append(point)
            
            elif (current.low < prev.low and current.low < next_bar.low and
                  current.high <= prev.high and current.high <= next_bar.high):
                
                point = FractionalPoint(
                    index=i,
                    timestamp=current.timestamp,
                    price=current.low,
                    point_type=PenType.BOTTOM,
                    kbar=current,
                    confirmed=True
                )
                self.fractional_points.append(point)
                new_points.append(point)
        
        return new_points
    
    def _form_pens(self):
        """Form pens (笔) from fractional points"""
        if len(self.fractional_points) < 2:
            return
        
        # Sort points by index
        points = sorted(self.fractional_points, key=lambda p: p.index)
        
        for i in range(len(points) - 1):
            start_point = points[i]
            end_point = points[i + 1]
            
            # Ensure alternating point types for valid pen
            if start_point.point_type == end_point.point_type:
                continue
            
            # Check minimum distance requirement
            if end_point.index - start_point.index < self.min_pen_bars:
                continue
            
            # Determine direction
            if start_point.point_type == PenType.BOTTOM:
                direction = Direction.UP
                length = end_point.price - start_point.price
            else:
                direction = Direction.DOWN
                length = start_point.price - end_point.price
            
            pen = Pen(
                start_point=start_point,
                end_point=end_point,
                direction=direction,
                length=length,
                start_time=start_point.timestamp,
                end_time=end_point.timestamp,
                confirmed=True
            )
            
            self.pens.append(pen)
    
    def _update_pens(self):
        """Update pens with new fractional points"""
        # For simplicity, rebuild all pens
        # In a production system, you might want to optimize this
        self.pens.clear()
        self._form_pens()
    
    def _form_segments(self):
        """Form segments (线段) from pens"""
        if len(self.pens) < self.min_segment_pens:
            return
        
        # Group consecutive pens of the same direction into segments
        current_segment_pens = []
        current_direction = Direction.UNKNOWN
        
        for pen in self.pens:
            if current_direction == Direction.UNKNOWN:
                current_direction = pen.direction
                current_segment_pens = [pen]
            elif pen.direction == current_direction:
                current_segment_pens.append(pen)
            else:
                # Direction changed, finalize current segment
                if len(current_segment_pens) >= self.min_segment_pens:
                    segment = Segment(
                        start_pen=current_segment_pens[0],
                        end_pen=current_segment_pens[-1],
                        pens=current_segment_pens.copy(),
                        confirmed=True
                    )
                    self.segments.append(segment)
                
                # Start new segment
                current_direction = pen.direction
                current_segment_pens = [pen]
        
        # Handle the last segment
        if len(current_segment_pens) >= self.min_segment_pens:
            segment = Segment(
                start_pen=current_segment_pens[0],
                end_pen=current_segment_pens[-1],
                pens=current_segment_pens.copy(),
                confirmed=False  # Last segment is not confirmed
            )
            self.segments.append(segment)
    
    def _update_segments(self):
        """Update segments with new pens"""
        # For simplicity, rebuild all segments
        self.segments.clear()
        self._form_segments()
    
    def _identify_central_areas(self):
        """Identify central areas (中枢) from segments"""
        if len(self.segments) < 3:
            return
        
        for i in range(len(self.segments) - 2):
            seg1 = self.segments[i]
            seg2 = self.segments[i + 1]
            seg3 = self.segments[i + 2]
            
            # Check if segments can form a central area
            # Need alternating directions and overlap
            if (seg1.direction != seg2.direction and 
                seg2.direction != seg3.direction and
                seg1.direction == seg3.direction):
                
                # Calculate potential central area bounds
                if seg1.direction == Direction.UP:
                    # UP-DOWN-UP pattern
                    high = min(seg1.high, seg3.high)
                    low = seg2.low
                else:
                    # DOWN-UP-DOWN pattern  
                    high = seg2.high
                    low = max(seg1.low, seg3.low)
                
                # Validate central area
                if high > low and (high - low) > 0:
                    central_area = CentralArea(
                        high=high,
                        low=low,
                        start_time=seg1.start_pen.start_time,
                        end_time=seg3.end_pen.end_time,
                        segments=[seg1, seg2, seg3],
                        confirmed=True
                    )
                    self.central_areas.append(central_area)
    
    def _update_central_areas(self):
        """Update central areas with new segments"""
        # For simplicity, rebuild all central areas
        self.central_areas.clear()
        self._identify_central_areas()
    
    def _adjust_indices_after_removal(self, removed_count: int):
        """Adjust indices in analysis structures after removing old K-bars"""
        # Adjust fractional points
        self.fractional_points = [
            point for point in self.fractional_points 
            if point.index >= removed_count
        ]
        for point in self.fractional_points:
            point.index -= removed_count
        
        # Note: Pens, segments, and central areas reference fractional points,
        # so they are automatically updated
    
    def _get_current_status(self) -> Dict[str, Any]:
        """Get current analysis status"""
        latest_kbar = self.kbars[-1] if self.kbars else None
        latest_pen = self.pens[-1] if self.pens else None
        latest_segment = self.segments[-1] if self.segments else None
        latest_central = self.central_areas[-1] if self.central_areas else None
        
        return {
            'latest_kbar': {
                'timestamp': latest_kbar.timestamp if latest_kbar else None,
                'close': latest_kbar.close if latest_kbar else None,
                'high': latest_kbar.high if latest_kbar else None,
                'low': latest_kbar.low if latest_kbar else None,
            } if latest_kbar else None,
            
            'latest_pen': {
                'direction': latest_pen.direction.name if latest_pen else None,
                'length': latest_pen.length if latest_pen else None,
                'start_price': latest_pen.start_point.price if latest_pen else None,
                'end_price': latest_pen.end_point.price if latest_pen else None,
                'confirmed': latest_pen.confirmed if latest_pen else None,
            } if latest_pen else None,
            
            'latest_segment': {
                'direction': latest_segment.direction.name if latest_segment else None,
                'high': latest_segment.high if latest_segment else None,
                'low': latest_segment.low if latest_segment else None,
                'pen_count': len(latest_segment.pens) if latest_segment else None,
                'confirmed': latest_segment.confirmed if latest_segment else None,
            } if latest_segment else None,
            
            'latest_central_area': {
                'high': latest_central.high if latest_central else None,
                'low': latest_central.low if latest_central else None,
                'center': latest_central.center_price if latest_central else None,
                'range_height': latest_central.range_height if latest_central else None,
                'confirmed': latest_central.confirmed if latest_central else None,
            } if latest_central else None,
            
            'current_trend': self.current_trend.name,
        }
    
    def _get_data_summary(self) -> Dict[str, Any]:
        """Get summary of all analysis data"""
        return {
            'total_kbars': len(self.kbars),
            'total_fractional_points': len(self.fractional_points),
            'total_pens': len(self.pens),
            'total_segments': len(self.segments),
            'total_central_areas': len(self.central_areas),
            'confirmed_pens': sum(1 for pen in self.pens if pen.confirmed),
            'confirmed_segments': sum(1 for seg in self.segments if seg.confirmed),
            'confirmed_central_areas': sum(1 for ca in self.central_areas if ca.confirmed),
        }
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """
        Get complete analysis results
        
        Returns:
            Dictionary containing all analysis data
        """
        return {
            'symbol': self.symbol,
            'exchange': self.exchange,
            'period': self.period,
            'data_summary': self._get_data_summary(),
            'current_status': self._get_current_status(),
            'fractional_points': [
                {
                    'index': point.index,
                    'timestamp': point.timestamp,
                    'price': point.price,
                    'type': point.point_type.name,
                    'confirmed': point.confirmed
                } for point in self.fractional_points[-10:]  # Last 10 points
            ],
            'pens': [
                {
                    'direction': pen.direction.name,
                    'length': pen.length,
                    'start_price': pen.start_point.price,
                    'end_price': pen.end_point.price,
                    'start_time': pen.start_time,
                    'end_time': pen.end_time,
                    'duration_bars': pen.duration_bars,
                    'confirmed': pen.confirmed
                } for pen in self.pens[-5:]  # Last 5 pens
            ],
            'segments': [
                {
                    'direction': seg.direction.name,
                    'high': seg.high,
                    'low': seg.low,
                    'pen_count': len(seg.pens),
                    'confirmed': seg.confirmed
                } for seg in self.segments[-3:]  # Last 3 segments
            ],
            'central_areas': [
                {
                    'high': ca.high,
                    'low': ca.low,
                    'center': ca.center_price,
                    'range_height': ca.range_height,
                    'start_time': ca.start_time,
                    'end_time': ca.end_time,
                    'level': ca.level,
                    'confirmed': ca.confirmed
                } for ca in self.central_areas[-2:]  # Last 2 central areas
            ]
        }
    
    def reset_analysis(self):
        """Reset all analysis data"""
        self.fractional_points.clear()
        self.pens.clear()
        self.segments.clear()
        self.central_areas.clear()
        self.last_processed_index = -1
        self.current_trend = Direction.UNKNOWN
        
        self.logger.info("Analysis data reset")
    
    def set_parameters(self, **kwargs):
        """
        Set analysis parameters
        
        Args:
            **kwargs: Parameter name-value pairs
        """
        if 'min_pen_bars' in kwargs:
            self.min_pen_bars = int(kwargs['min_pen_bars'])
        if 'min_segment_pens' in kwargs:
            self.min_segment_pens = int(kwargs['min_segment_pens'])
        if 'central_area_threshold' in kwargs:
            self.central_area_threshold = float(kwargs['central_area_threshold'])
        if 'max_history' in kwargs:
            self.max_history = int(kwargs['max_history'])
        
        self.logger.info(f"Parameters updated: {kwargs}")
