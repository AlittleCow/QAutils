"""
Generic Database Wrapper for QAutils

This module provides a unified interface for accessing both TDengine (kbar data)
and SQLite (meta data) databases. It manages connections and provides high-level
operations for stock data storage and retrieval.
"""

import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd

# Make TDengine import optional
try:
    from kbar_db import KbarDatabase
    TDENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"TDengine not available: {e}")
    KbarDatabase = None
    TDENGINE_AVAILABLE = False

from meta_db import MetaDatabase


class DatabaseManager:
    """
    Unified database manager for both time-series K-bar data and relational meta data.
    
    This class provides a single interface to manage both TDengine (for K-bar data)
    and SQLite (for meta data) databases.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database manager with configuration for both databases.
        
        Args:
            config: Configuration dictionary containing:
                - kbar_config: TDengine configuration for K-bar data
                - meta_config: SQLite configuration for meta data
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize databases
        self.kbar_db = None
        self.meta_db = None
        
        # Connect to databases
        self._connect_databases()
        
    def _connect_databases(self):
        """Connect to both databases."""
        try:
            # Connect to TDengine for K-bar data
            kbar_config = self.config.get('kbar_config', {})
            if kbar_config and TDENGINE_AVAILABLE and KbarDatabase:
                try:
                    self.kbar_db = KbarDatabase(kbar_config)
                    self.logger.info("Connected to TDengine for K-bar data")
                except Exception as e:
                    self.logger.warning(f"Failed to connect to TDengine: {e}")
                    self.logger.warning("Continuing without TDengine (K-bar data will not be available)")
                    self.kbar_db = None
            else:
                if not TDENGINE_AVAILABLE:
                    self.logger.warning("TDengine client not available")
                else:
                    self.logger.warning("No TDengine configuration provided")
                
            # Connect to SQLite for meta data
            meta_config = self.config.get('meta_config', {})
            if meta_config:
                self.meta_db = MetaDatabase(meta_config)
                self.logger.info("Connected to SQLite for meta data")
            else:
                self.logger.warning("No SQLite configuration provided")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to databases: {str(e)}")
            raise
            
    def setup_stock(self, symbol: str, exchange: str, name: str, **kwargs) -> int:
        """
        Setup a stock in both databases (meta info and K-bar table).
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            name: Stock name
            **kwargs: Additional stock metadata
            
        Returns:
            Stock ID from meta database
        """
        if not self.meta_db:
            raise RuntimeError("Meta database not available")
            
        try:
            # First ensure exchange exists
            exchange_id = self.meta_db.get_exchange_id(exchange)
            if not exchange_id:
                # Create exchange if it doesn't exist
                exchange_name = kwargs.get('exchange_name', exchange)
                exchange_id = self.meta_db.insert_exchange(
                    exchange, 
                    exchange_name,
                    country=kwargs.get('country', 'CN'),
                    timezone=kwargs.get('timezone', 'Asia/Shanghai')
                )
                
            # Insert stock metadata
            stock_id = self.meta_db.insert_stock(symbol, exchange, name, **kwargs)
            
            # Create K-bar table if TDengine is available
            if self.kbar_db:
                periods = kwargs.get('periods', ['1min', '5min', '15min', '30min', '1hour', '1day'])
                for period in periods:
                    self.kbar_db.create_table_for_symbol(symbol, exchange, period)
                    
            self.logger.info(f"Stock {symbol}.{exchange} setup completed")
            return stock_id
            
        except Exception as e:
            self.logger.error(f"Failed to setup stock {symbol}.{exchange}: {str(e)}")
            raise
            
    def store_kbar_data(self, symbol: str, exchange: str, period: str, 
                       data: Union[Dict, List[Dict], pd.DataFrame]):
        """
        Store K-bar data in TDengine.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            data: K-bar data
        """
        if not self.kbar_db:
            raise RuntimeError("K-bar database not available")
            
        try:
            self.kbar_db.insert_kbar_data(data, symbol, exchange, period)
            
            # Update sync status in meta database
            if self.meta_db:
                stock_id = self.meta_db.get_stock_id(symbol, exchange)
                if stock_id:
                    self.meta_db.update_sync_status(
                        stock_id, 'kbar', period, 'completed'
                    )
                    
            self.logger.debug(f"Stored K-bar data for {symbol}.{exchange} ({period})")
            
        except Exception as e:
            self.logger.error(f"Failed to store K-bar data: {str(e)}")
            # Update sync status with error
            if self.meta_db:
                stock_id = self.meta_db.get_stock_id(symbol, exchange)
                if stock_id:
                    self.meta_db.update_sync_status(
                        stock_id, 'kbar', period, 'failed', str(e)
                    )
            raise
            
    def get_kbar_data(self, symbol: str, exchange: str = "SH", period: str = "1min",
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     limit: Optional[int] = None) -> pd.DataFrame:
        """
        Retrieve K-bar data from TDengine.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            start_time: Start time for query
            end_time: End time for query
            limit: Maximum number of records
            
        Returns:
            pandas DataFrame with K-bar data
        """
        if not self.kbar_db:
            raise RuntimeError("K-bar database not available")
            
        return self.kbar_db.query_kbar_data(
            symbol, exchange, period, start_time, end_time, limit
        )
        
    def get_stock_info(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Get stock metadata from SQLite."""
        if not self.meta_db:
            raise RuntimeError("Meta database not available")
            
        return self.meta_db.get_stock_info(symbol, exchange)
        
    def get_all_stocks(self, exchange: Optional[str] = None, 
                      is_active: Optional[bool] = None) -> List[Dict]:
        """Get all stocks from meta database."""
        if not self.meta_db:
            raise RuntimeError("Meta database not available")
            
        return self.meta_db.get_all_stocks(exchange, is_active)
        
    def get_symbols_with_data(self) -> List[Dict]:
        """Get all symbols that have K-bar data."""
        if not self.kbar_db:
            return []
            
        return self.kbar_db.get_symbols()
        
    def get_latest_timestamp(self, symbol: str, exchange: str = "SH", 
                           period: str = "1min") -> Optional[datetime]:
        """Get the latest timestamp for a symbol's K-bar data."""
        if not self.kbar_db:
            return None
            
        return self.kbar_db.get_latest_timestamp(symbol, exchange, period)
        
    def get_sync_status(self, symbol: str, exchange: str, data_type: str, 
                       period: str) -> Optional[Dict]:
        """Get synchronization status for a stock."""
        if not self.meta_db:
            return None
            
        stock_id = self.meta_db.get_stock_id(symbol, exchange)
        if not stock_id:
            return None
            
        return self.meta_db.get_sync_status(stock_id, data_type, period)
        
    def delete_kbar_data(self, symbol: str, exchange: str = "SH", period: str = "1min",
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None):
        """Delete K-bar data from TDengine."""
        if not self.kbar_db:
            raise RuntimeError("K-bar database not available")
            
        self.kbar_db.delete_data(symbol, exchange, period, start_time, end_time)
        
    def store_dividend(self, symbol: str, exchange: str, ex_date: str, 
                      amount: float, **kwargs):
        """Store dividend information."""
        if not self.meta_db:
            raise RuntimeError("Meta database not available")
            
        stock_id = self.meta_db.get_stock_id(symbol, exchange)
        if not stock_id:
            raise ValueError(f"Stock {symbol}.{exchange} not found")
            
        self.meta_db.insert_dividend(stock_id, ex_date, amount, **kwargs)
        
    def store_split(self, symbol: str, exchange: str, ex_date: str, ratio: float):
        """Store stock split information."""
        if not self.meta_db:
            raise RuntimeError("Meta database not available")
            
        stock_id = self.meta_db.get_stock_id(symbol, exchange)
        if not stock_id:
            raise ValueError(f"Stock {symbol}.{exchange} not found")
            
        self.meta_db.insert_split(stock_id, ex_date, ratio)
        
    def backup_meta_database(self, backup_path: str):
        """Backup the meta database."""
        if not self.meta_db:
            raise RuntimeError("Meta database not available")
            
        self.meta_db.backup_database(backup_path)
        
    def execute_meta_query(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict]:
        """Execute custom query on meta database."""
        if not self.meta_db:
            raise RuntimeError("Meta database not available")
            
        return self.meta_db.execute_query(sql, params or ())
        
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about both databases."""
        stats = {
            'kbar_db_available': self.kbar_db is not None,
            'meta_db_available': self.meta_db is not None,
            'total_stocks': 0,
            'total_symbols_with_data': 0,
            'exchanges': []
        }
        
        if self.meta_db:
            try:
                stocks = self.meta_db.get_all_stocks()
                stats['total_stocks'] = len(stocks)
                
                exchanges = self.meta_db.execute_query("SELECT code, name FROM exchanges")
                stats['exchanges'] = exchanges
                
            except Exception as e:
                self.logger.error(f"Failed to get meta database stats: {str(e)}")
                
        if self.kbar_db:
            try:
                symbols = self.kbar_db.get_symbols()
                stats['total_symbols_with_data'] = len(set(
                    f"{s['symbol']}.{s['exchange']}" for s in symbols
                ))
                
            except Exception as e:
                self.logger.error(f"Failed to get K-bar database stats: {str(e)}")
                
        return stats
        
    def close(self):
        """Close all database connections."""
        try:
            if self.kbar_db:
                self.kbar_db.close()
                self.kbar_db = None
                
            if self.meta_db:
                self.meta_db.close()
                self.meta_db = None
                
            self.logger.info("All database connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing database connections: {str(e)}")
            
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Factory function for easier instantiation
def create_database_manager(kbar_config: Optional[Dict[str, Any]] = None, 
                          meta_config: Optional[Dict[str, Any]] = None) -> DatabaseManager:
    """
    Factory function to create a DatabaseManager instance.
    
    Args:
        kbar_config: TDengine configuration for K-bar data
        meta_config: SQLite configuration for meta data
        
    Returns:
        DatabaseManager instance
    """
    config = {
        'kbar_config': kbar_config or {},
        'meta_config': meta_config or {}
    }
    
    return DatabaseManager(config)


# Default configuration templates
DEFAULT_KBAR_CONFIG = {
    'host': 'localhost',
    'port': 6030,
    'user': 'root',
    'password': 'taosdata',
    'database': 'stock_kbar'
}

DEFAULT_META_CONFIG = {
    'database_path': 'data/stock_meta.db',
    'timeout': 30.0,
    'check_same_thread': False
}
