"""
Generic Database Wrapper for QAutils

This module provides a unified interface for accessing both TDengine/SQLite (kbar data)
and SQLite (for meta data) databases. It manages connections and provides high-level
operations for stock data storage and retrieval.
"""

import logging
import json
import os
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd

# Make TDengine import optional
try:
    from kbar_db import KbarDatabase as TDengineKbarDatabase
    TDENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"TDengine not available: {e}")
    TDengineKbarDatabase = None
    TDENGINE_AVAILABLE = False

# Import SQLite K-bar database
try:
    from kbar_db_sqlite import KbarDatabase as SQLiteKbarDatabase
    SQLITE_KBAR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SQLite K-bar database not available: {e}")
    SQLiteKbarDatabase = None
    SQLITE_KBAR_AVAILABLE = False

from meta_db import MetaDatabase


class DatabaseManager:
    """
    Unified database manager for both time-series K-bar data and relational meta data.
    
    This class provides a single interface to manage both TDengine/SQLite (for K-bar data)
    and SQLite (for meta data) databases.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database manager with configuration for both databases.
        
        Args:
            config: Configuration dictionary containing:
                - kbar_config: K-bar database configuration
                - kbar_type: Type of K-bar database ('tdengine' or 'sqlite', default: 'sqlite')
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
            # Connect to K-bar database (TDengine or SQLite)
            kbar_config = self.config.get('kbar_config', {})
            kbar_type = self.config.get('kbar_type', 'sqlite').lower()
            
            # Check if K-bar database is enabled
            kbar_enabled = kbar_config.get('enabled', True)
            
            if kbar_config and kbar_enabled:
                if kbar_type == 'tdengine':
                    self._connect_tdengine_kbar(kbar_config)
                elif kbar_type == 'sqlite':
                    self._connect_sqlite_kbar(kbar_config)
                else:
                    self.logger.warning(f"Unknown K-bar database type: {kbar_type}. Supported types: 'tdengine', 'sqlite'")
            elif not kbar_enabled:
                self.logger.info("K-bar database is disabled in configuration")
            else:
                self.logger.warning("No K-bar database configuration provided")
                
            # Connect to SQLite for meta data
            meta_config = self.config.get('meta_config', {})
            meta_enabled = meta_config.get('enabled', True)
            
            if meta_config and meta_enabled:
                self.meta_db = MetaDatabase(meta_config)
                self.logger.info("Connected to SQLite for meta data")
            elif not meta_enabled:
                self.logger.info("Meta database is disabled in configuration")
            else:
                self.logger.warning("No SQLite configuration provided")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to databases: {str(e)}")
            raise
            
    def _connect_tdengine_kbar(self, kbar_config: Dict[str, Any]):
        """Connect to TDengine for K-bar data."""
        tdengine_config = kbar_config.get('tdengine', {})
        tdengine_enabled = tdengine_config.get('enabled', True)
        
        if not tdengine_enabled:
            self.logger.info("TDengine is disabled in configuration")
            return
            
        if TDENGINE_AVAILABLE and TDengineKbarDatabase:
            try:
                self.kbar_db = TDengineKbarDatabase(tdengine_config)
                self.logger.info("Connected to TDengine for K-bar data")
            except Exception as e:
                self.logger.warning(f"Failed to connect to TDengine: {e}")
                self.logger.warning("Continuing without TDengine (K-bar data will not be available)")
                self.kbar_db = None
        else:
            if not TDENGINE_AVAILABLE:
                self.logger.warning("TDengine client not available")
            else:
                self.logger.warning("TDengine KbarDatabase class not available")
                
    def _connect_sqlite_kbar(self, kbar_config: Dict[str, Any]):
        """Connect to SQLite for K-bar data."""
        sqlite_config = kbar_config.get('sqlite', {})
        sqlite_enabled = sqlite_config.get('enabled', True)
        
        if not sqlite_enabled:
            self.logger.info("SQLite K-bar database is disabled in configuration")
            return
            
        if SQLITE_KBAR_AVAILABLE and SQLiteKbarDatabase:
            try:
                self.kbar_db = SQLiteKbarDatabase(sqlite_config)
                self.logger.info("Connected to SQLite for K-bar data")
            except Exception as e:
                self.logger.warning(f"Failed to connect to SQLite K-bar database: {e}")
                self.logger.warning("Continuing without SQLite K-bar database (K-bar data will not be available)")
                self.kbar_db = None
        else:
            self.logger.warning("SQLite K-bar database not available")
            
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
                          meta_config: Optional[Dict[str, Any]] = None,
                          kbar_type: Optional[str] = None,
                          config_path: Optional[str] = None) -> DatabaseManager:
    """
    Factory function to create a DatabaseManager instance.
    
    Args:
        kbar_config: K-bar database configuration. If None, loads from JSON.
        meta_config: SQLite configuration for meta data. If None, loads from JSON.
        kbar_type: Type of K-bar database ('tdengine' or 'sqlite'). If None, uses type from JSON config.
        config_path: Path to configuration file. If None, uses default path.
        
    Returns:
        DatabaseManager instance
    """
    # Load default configurations if not provided
    if kbar_config is None:
        kbar_config = get_full_kbar_config(config_path)
    
    if meta_config is None:
        meta_config = get_default_meta_config(config_path)
    
    # Determine kbar_type from configuration if not specified
    if kbar_type is None:
        kbar_type = kbar_config.get('type', 'sqlite')
    
    config = {
        'kbar_config': kbar_config,
        'meta_config': meta_config,
        'kbar_type': kbar_type
    }
    
    return DatabaseManager(config)


def load_database_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load database configuration from JSON file.
    
    Args:
        config_path: Path to configuration file. If None, uses default path.
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Default to the setting directory relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'setting', 'db.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.warning(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in configuration file: {config_path}")
        return {}


def get_default_kbar_config_tdengine(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Get default TDengine K-bar configuration from JSON file."""
    config = load_database_config(config_path)
    return config.get('kbar_config', {}).get('tdengine', {
        'enabled': True,
        'host': 'localhost',
        'port': 6030,
        'user': 'root',
        'password': 'taosdata',
        'database': 'stock_kbar'
    })


def get_default_kbar_config_sqlite(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Get default SQLite K-bar configuration from JSON file."""
    config = load_database_config(config_path)
    return config.get('kbar_config', {}).get('sqlite', {
        'enabled': True,
        'database_path': 'data/stock_kbar.db',
        'create_dir': True
    })


def get_default_meta_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Get default meta database configuration from JSON file."""
    config = load_database_config(config_path)
    return config.get('meta_config', {
        'enabled': True,
        'database_path': 'data/stock_meta.db',
        'timeout': 30.0,
        'check_same_thread': False
    })


def get_full_kbar_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Get the full K-bar configuration including both TDengine and SQLite settings."""
    config = load_database_config(config_path)
    return config.get('kbar_config', {
        'enabled': True,
        'type': 'sqlite',
        'tdengine': get_default_kbar_config_tdengine(config_path),
        'sqlite': get_default_kbar_config_sqlite(config_path)
    })


# Backward compatibility - keep the old names as function calls
def get_default_kbar_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Get default K-bar configuration (TDengine for backward compatibility)."""
    return get_default_kbar_config_tdengine(config_path)
