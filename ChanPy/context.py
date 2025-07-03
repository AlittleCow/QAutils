"""
Chan Context Module

This module provides a context class that manages the current state of Chan analysis,
including K-bars, fractals, pens, and lines. It integrates with the database system
for persistence and retrieval of Chan analysis data.
"""

import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime

# Import Chan components
from .mergekbar import MergedKbar
from .fractal import Fractal, FractalType
from .pen import ChanPen, PenDirection
from .line import ChanLine, LineDirection, LineStatus

# Import database
from .module.database.db import DatabaseManager, create_database_manager

if TYPE_CHECKING:
    from .chan import Kbar


def convert_df_to_kbars(kbar_df) -> List['Kbar']:
    """
    Convert a DataFrame of K-bar data to a list of Kbar objects.
    
    Args:
        kbar_df: Pandas DataFrame containing K-bar data with columns:
                - ts: timestamp (string)
                - open: open price (float)
                - high: high price (float)
                - low: low price (float)
                - close: close price (float)
                - volume: volume (int)
                
    Returns:
        List of Kbar objects
    """
    from .chantypes import Kbar
    
    kbars = []
    for _, row in kbar_df.iterrows():
        kbar = Kbar(
            timestamp=str(row['ts']),
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=int(row['volume'])
        )
        kbars.append(kbar)
    
    return kbars


@dataclass
class ChanState:
    """
    Current state of Chan analysis for a specific symbol/period.
    
    This class holds the current analysis state including the most recent
    K-bars, fractals, pens, and lines.
    """
    # Current data
    current_kbars: List['Kbar'] = field(default_factory=list)
    current_merged_kbars: List[MergedKbar] = field(default_factory=list)
    current_fractals: List[Fractal] = field(default_factory=list)
    current_pens: List[ChanPen] = field(default_factory=list)
    current_lines: List[ChanLine] = field(default_factory=list)
    
    # Latest items
    latest_kbar: Optional['Kbar'] = None
    latest_merged_kbar: Optional[MergedKbar] = None
    latest_fractal: Optional[Fractal] = None
    latest_pen: Optional[ChanPen] = None
    latest_line: Optional[ChanLine] = None
    
    # Global line (most important line for trend analysis)
    global_line: Optional[ChanLine] = None
    
    # Analysis flags
    is_initialized: bool = False
    last_update_time: Optional[str] = None
    
    def update_timestamp(self):
        """Update the last update timestamp."""
        self.last_update_time = datetime.now().isoformat()


class ChanContext:
    """
    Chan Analysis Context Manager
    
    This class manages the current state of Chan analysis for multiple symbols
    and periods. It provides methods to initialize, update, and persist the
    analysis state using the database system.
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize Chan context.
        
        Args:
            db_manager: Database manager instance. If None, creates a default one.
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize database manager
        if db_manager is None:
            try:
                self.db_manager = create_database_manager()
                self.logger.debug("Created default database manager for Chan context")
            except Exception as e:
                self.logger.warning(f"Failed to create database manager: {e}")
                self.db_manager = None
        else:
            self.db_manager = db_manager
        
        # State storage: {(symbol, exchange, period): ChanState}
        self.states: Dict[tuple, ChanState] = {}
        
        # Current active context
        self.current_symbol: Optional[str] = None
        self.current_exchange: Optional[str] = None
        self.current_period: Optional[str] = None
    
    def get_context_key(self, symbol: str, exchange: str, period: str) -> tuple:
        """Get the context key for a symbol/exchange/period combination."""
        return (symbol, exchange, period)
    
    def set_current_context(self, symbol: str, exchange: str, period: str):
        """
        Set the current active context.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
        """
        self.current_symbol = symbol
        self.current_exchange = exchange
        self.current_period = period
        
        # Initialize state if it doesn't exist
        context_key = self.get_context_key(symbol, exchange, period)
        if context_key not in self.states:
            self.states[context_key] = ChanState()
            self.logger.debug(f"Initialized new Chan state for {symbol}.{exchange} ({period})")
    
    def get_current_state(self) -> Optional[ChanState]:
        """Get the current active Chan state."""
        if not all([self.current_symbol, self.current_exchange, self.current_period]):
            return None
        
        # Type guard: we know these are not None after the check above
        assert self.current_symbol is not None
        assert self.current_exchange is not None  
        assert self.current_period is not None
        
        context_key = self.get_context_key(
            self.current_symbol, self.current_exchange, self.current_period
        )
        return self.states.get(context_key)
    
    def get_state(self, symbol: str, exchange: str, period: str) -> ChanState:
        """
        Get Chan state for a specific symbol/exchange/period.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            
        Returns:
            ChanState object (creates new if doesn't exist)
        """
        context_key = self.get_context_key(symbol, exchange, period)
        if context_key not in self.states:
            self.states[context_key] = ChanState()
            self.logger.debug(f"Created new Chan state for {symbol}.{exchange} ({period})")
        
        return self.states[context_key]
    
    def initialize_from_database(self, symbol: str, exchange: str, period: str,
                                limit: Optional[int] = 100,
                                start_time: Optional[str] = None,
                                end_time: Optional[str] = None) -> bool:
        """
        Initialize Chan state from database.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            limit: Maximum number of records to load
            start_time: Start time for data range (format: "YYYY-MM-DD HH:MM:SS")
            end_time: End time for data range (format: "YYYY-MM-DD HH:MM:SS")
            
        Returns:
            True if initialization was successful
        """
        if not self.db_manager:
            self.logger.warning("No database manager available for initialization")
            return False
        
        try:
            # Get or create state
            state = self.get_state(symbol, exchange, period)
            
            # Log time range information
            time_range_info = ""
            if start_time or end_time:
                time_range_info = f" (time range: {start_time or 'unlimited'} to {end_time or 'unlimited'})"
            
            self.logger.info(f"Initializing Chan state from database for {symbol}.{exchange} ({period}){time_range_info}")
            
            # Load Chan lines from database
            if hasattr(self.db_manager, 'get_chan_lines'):
                lines_data = self.db_manager.get_chan_lines(
                    symbol, exchange, period, start_time=start_time, end_time=end_time, limit=limit
                )
                
                if lines_data:
                    # Convert database records to ChanLine objects (simplified)
                    # In a full implementation, you'd need proper deserialization
                    state.current_lines = []  # Would populate with actual ChanLine objects
                    
                    # Set latest and global lines
                    if lines_data:
                        # Find latest line
                        latest_line_data = max(lines_data, key=lambda x: x.get('line_index', 0))
                        # state.latest_line = convert_to_chan_line(latest_line_data)
                        
                        # Find global line
                        global_lines = [line for line in lines_data if line.get('is_global')]
                        if global_lines:
                            # state.global_line = convert_to_chan_line(global_lines[0])
                            pass
                    
                    self.logger.info(f"Loaded {len(lines_data)} Chan lines from database for {symbol}.{exchange} ({period})")
            
            # Load K-bar data if available
            if hasattr(self.db_manager, 'get_kbar_data'):
                try:
                    # Convert string datetime parameters to datetime objects if provided
                    start_datetime = None
                    end_datetime = None
                    
                    if start_time:
                        try:
                            start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            self.logger.warning(f"Invalid start_time format '{start_time}', expected 'YYYY-MM-DD HH:MM:SS'")
                    
                    if end_time:
                        try:
                            end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            self.logger.warning(f"Invalid end_time format '{end_time}', expected 'YYYY-MM-DD HH:MM:SS'")
                    
                    kbar_df = self.db_manager.get_kbar_data(
                        symbol, exchange, period, 
                        limit=limit,
                        start_time=start_datetime,
                        end_time=end_datetime
                    )
                    if not kbar_df.empty:
                        # Convert DataFrame to Kbar objects
                        state.current_kbars = convert_df_to_kbars(kbar_df)
                        state.latest_kbar = state.current_kbars[-1] if state.current_kbars else None
                        self.logger.info(f"Loaded {len(kbar_df)} K-bars from database{time_range_info}")
                except Exception as e:
                    self.logger.debug(f"K-bar data not available: {e}")
            
            state.is_initialized = True
            state.update_timestamp()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize from database: {str(e)}")
            return False
    
    def update_kbars(self, kbars: List['Kbar'], symbol: Optional[str] = None,
                    exchange: Optional[str] = None, period: Optional[str] = None):
        """
        Update K-bars in the context.
        
        Args:
            kbars: List of K-bar objects
            symbol: Stock symbol (uses current if None)
            exchange: Exchange code (uses current if None)
            period: Time period (uses current if None)
        """
        # Use current context if not specified
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            raise ValueError("Symbol, exchange, and period must be specified")
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        state.current_kbars = kbars
        state.latest_kbar = kbars[-1] if kbars else None
        state.update_timestamp()
        
        self.logger.debug(f"Updated {len(kbars)} K-bars for {symbol}.{exchange} ({period})")
    
    def update_merged_kbars(self, merged_kbars: List[MergedKbar], 
                           symbol: Optional[str] = None, exchange: Optional[str] = None, 
                           period: Optional[str] = None):
        """Update merged K-bars in the context."""
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            raise ValueError("Symbol, exchange, and period must be specified")
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        state.current_merged_kbars = merged_kbars
        state.latest_merged_kbar = merged_kbars[-1] if merged_kbars else None
        state.update_timestamp()
        
        self.logger.debug(f"Updated {len(merged_kbars)} merged K-bars for {symbol}.{exchange} ({period})")
    
    def update_fractals(self, fractals: List[Fractal], symbol: Optional[str] = None,
                       exchange: Optional[str] = None, period: Optional[str] = None):
        """Update fractals in the context."""
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            raise ValueError("Symbol, exchange, and period must be specified")
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        state.current_fractals = fractals
        state.latest_fractal = fractals[-1] if fractals else None
        state.update_timestamp()
        
        self.logger.debug(f"Updated {len(fractals)} fractals for {symbol}.{exchange} ({period})")
    
    def update_pens(self, pens: List[ChanPen], symbol: Optional[str] = None,
                   exchange: Optional[str] = None, period: Optional[str] = None):
        """Update pens in the context."""
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            raise ValueError("Symbol, exchange, and period must be specified")
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        state.current_pens = pens
        state.latest_pen = pens[-1] if pens else None
        state.update_timestamp()
        
        self.logger.debug(f"Updated {len(pens)} pens for {symbol}.{exchange} ({period})")
    
    def update_lines(self, lines: List[ChanLine], symbol: Optional[str] = None,
                    exchange: Optional[str] = None, period: Optional[str] = None,
                    save_to_db: bool = True):
        """
        Update lines in the context and optionally save to database.
        
        Args:
            lines: List of ChanLine objects
            symbol: Stock symbol (uses current if None)
            exchange: Exchange code (uses current if None)
            period: Time period (uses current if None)
            save_to_db: Whether to save lines to database
        """
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            raise ValueError("Symbol, exchange, and period must be specified")
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        state.current_lines = lines
        state.latest_line = lines[-1] if lines else None
        
        # Update global line
        global_lines = [line for line in lines if line.is_global]
        state.global_line = global_lines[0] if global_lines else None
        
        state.update_timestamp()
        
        # Save to database if requested and available
        if save_to_db and self.db_manager and hasattr(self.db_manager, 'store_chan_lines'):
            try:
                self.db_manager.store_chan_lines(lines, symbol, exchange, period)
                self.logger.info(f"Saved {len(lines)} Chan lines to database for {symbol}.{exchange} ({period})")
            except Exception as e:
                self.logger.error(f"Failed to save Chan lines to database: {str(e)}")
        
        self.logger.debug(f"Updated {len(lines)} lines for {symbol}.{exchange} ({period})")
    
    def get_latest_kbar(self, symbol: Optional[str] = None, exchange: Optional[str] = None,
                       period: Optional[str] = None) -> Optional['Kbar']:
        """Get the latest K-bar."""
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            return None
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        return state.latest_kbar
    
    def get_latest_fractal(self, symbol: Optional[str] = None, exchange: Optional[str] = None,
                          period: Optional[str] = None) -> Optional[Fractal]:
        """Get the latest fractal."""
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            return None
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        return state.latest_fractal
    
    def get_latest_pen(self, symbol: Optional[str] = None, exchange: Optional[str] = None,
                      period: Optional[str] = None) -> Optional[ChanPen]:
        """Get the latest pen."""
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            return None
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        return state.latest_pen
    
    def get_latest_line(self, symbol: Optional[str] = None, exchange: Optional[str] = None,
                       period: Optional[str] = None) -> Optional[ChanLine]:
        """Get the latest line."""
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            return None
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        return state.latest_line
    
    def get_global_line(self, symbol: Optional[str] = None, exchange: Optional[str] = None,
                       period: Optional[str] = None) -> Optional[ChanLine]:
        """Get the global line."""
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            return None
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        return state.global_line
    
    def load_lines_from_database(self, symbol: str, exchange: str, period: str,
                                start_time: Optional[str] = None, end_time: Optional[str] = None,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load Chan lines from database.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of records
            
        Returns:
            List of line data dictionaries
        """
        if not self.db_manager or not hasattr(self.db_manager, 'get_chan_lines'):
            self.logger.warning("Database manager not available for loading lines")
            return []
        
        try:
            lines_data = self.db_manager.get_chan_lines(
                symbol, exchange, period, start_time, end_time, limit=limit
            )
            self.logger.info(f"Loaded {len(lines_data)} Chan lines from database")
            return lines_data
        except Exception as e:
            self.logger.error(f"Failed to load Chan lines from database: {str(e)}")
            return []
    
    def get_context_summary(self, symbol: Optional[str] = None, exchange: Optional[str] = None,
                           period: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of the current context state.
        
        Returns:
            Dictionary with context summary information
        """
        symbol = symbol or self.current_symbol
        exchange = exchange or self.current_exchange
        period = period or self.current_period
        
        if not all([symbol, exchange, period]):
            return {
                'error': 'No active context set',
                'current_symbol': self.current_symbol,
                'current_exchange': self.current_exchange,
                'current_period': self.current_period
            }
        
        # Type guard: we know these are not None after the check above
        assert symbol is not None
        assert exchange is not None
        assert period is not None
        
        state = self.get_state(symbol, exchange, period)
        
        return {
            'symbol': symbol,
            'exchange': exchange,
            'period': period,
            'is_initialized': state.is_initialized,
            'last_update_time': state.last_update_time,
            'kbar_count': len(state.current_kbars),
            'merged_kbar_count': len(state.current_merged_kbars),
            'fractal_count': len(state.current_fractals),
            'pen_count': len(state.current_pens),
            'line_count': len(state.current_lines),
            'has_latest_kbar': state.latest_kbar is not None,
            'has_latest_fractal': state.latest_fractal is not None,
            'has_latest_pen': state.latest_pen is not None,
            'has_latest_line': state.latest_line is not None,
            'has_global_line': state.global_line is not None,
            'global_line_direction': state.global_line.direction.name if state.global_line else None,
            'global_line_status': state.global_line.status.name if state.global_line else None
        }
    
    def clear_context(self, symbol: str, exchange: str, period: str):
        """Clear the context for a specific symbol/exchange/period."""
        context_key = self.get_context_key(symbol, exchange, period)
        if context_key in self.states:
            del self.states[context_key]
            self.logger.info(f"Cleared context for {symbol}.{exchange} ({period})")
    
    def clear_all_contexts(self):
        """Clear all contexts."""
        self.states.clear()
        self.current_symbol = None
        self.current_exchange = None
        self.current_period = None
        self.logger.info("Cleared all contexts")
    
    def get_all_contexts(self) -> List[Dict[str, str]]:
        """Get list of all available contexts."""
        contexts = []
        for (symbol, exchange, period) in self.states.keys():
            contexts.append({
                'symbol': symbol,
                'exchange': exchange,
                'period': period
            })
        return contexts
    
    def close(self):
        """Close the context and database connections."""
        if self.db_manager:
            self.db_manager.close()
        self.clear_all_contexts()
        self.logger.info("Chan context closed")

    def load_kbars_from_database(self, symbol: str, exchange: str, period: str,
                                limit: Optional[int] = 100,
                                start_time: Optional[str] = None,
                                end_time: Optional[str] = None) -> List['Kbar']:
        """
        Load K-bar data from database with time range filtering.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            limit: Maximum number of records to load
            start_time: Start time for data range (format: "YYYY-MM-DD HH:MM:SS")
            end_time: End time for data range (format: "YYYY-MM-DD HH:MM:SS")
            
        Returns:
            List of Kbar objects
        """
        if not self.db_manager or not hasattr(self.db_manager, 'get_kbar_data'):
            self.logger.warning("Database manager not available for loading K-bars")
            return []
        
        try:
            # Log time range information
            time_range_info = ""
            if start_time or end_time:
                time_range_info = f" (time range: {start_time or 'unlimited'} to {end_time or 'unlimited'})"
            
            self.logger.info(f"Loading K-bar data from database for {symbol}.{exchange} ({period}){time_range_info}")
            
            # Convert string datetime parameters to datetime objects if provided
            start_datetime = None
            end_datetime = None
            
            if start_time:
                try:
                    start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    self.logger.warning(f"Invalid start_time format '{start_time}', expected 'YYYY-MM-DD HH:MM:SS'")
            
            if end_time:
                try:
                    end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    self.logger.warning(f"Invalid end_time format '{end_time}', expected 'YYYY-MM-DD HH:MM:SS'")
            
            # Load K-bar data from database
            kbar_df = self.db_manager.get_kbar_data(
                symbol, exchange, period,
                limit=limit,
                start_time=start_datetime,
                end_time=end_datetime
            )
            
            if kbar_df.empty:
                self.logger.warning(f"No K-bar data found for {symbol}.{exchange} ({period}){time_range_info}")
                return []
            
            # Convert DataFrame to Kbar objects
            kbars = convert_df_to_kbars(kbar_df)
            self.logger.info(f"Loaded {len(kbars)} K-bars from database{time_range_info}")
            
            return kbars
            
        except Exception as e:
            self.logger.error(f"Failed to load K-bar data from database: {str(e)}")
            return []
