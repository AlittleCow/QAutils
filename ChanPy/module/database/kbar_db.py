"""
TDengine Database Module for K-bar Data Storage

This module provides a TDengine database interface for storing and retrieving
stock K-bar data (OHLCV data) with time-series optimization.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import pandas as pd

try:
    import taos
    TDENGINE_AVAILABLE = True
except ImportError as e:
    taos = None
    TDENGINE_AVAILABLE = False
    logging.warning(f"TDengine client (taospy) not available: {e}. Install with: pip install taospy")
except Exception as e:
    taos = None
    TDENGINE_AVAILABLE = False
    logging.warning(f"TDengine client library not available: {e}")


class KbarDatabase:
    """TDengine database interface for K-bar data storage."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize TDengine connection for K-bar data.
        
        Args:
            config: Database configuration dictionary containing:
                - host: TDengine server host
                - port: TDengine server port (default: 6030)
                - user: Database username
                - password: Database password
                - database: Database name
        """
        if not TDENGINE_AVAILABLE or taos is None:
            raise ImportError("TDengine client not available. Install TDengine client library and taospy package.")
            
        self.config = config
        self.conn = None
        self.cursor = None
        self.database_name = config.get('database', 'kbar_db')
        self.logger = logging.getLogger(__name__)
        
        # Connect to TDengine
        self._connect()
        
    def _connect(self):
        """Establish connection to TDengine."""
        try:
            self.conn = taos.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 6030),
                user=self.config.get('user', 'root'),
                password=self.config.get('password', 'taosdata'),
                database=self.database_name
            )
            self.cursor = self.conn.cursor()
            self.logger.info(f"Connected to TDengine database: {self.database_name}")
            
            # Create database if not exists
            self._create_database()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to TDengine: {str(e)}")
            raise
            
    def _create_database(self):
        """Create database and tables if they don't exist."""
        try:
            # Create database with appropriate settings for time-series data
            self.cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS {self.database_name} 
                PRECISION 'ms' 
                KEEP 3650 
                DAYS 30 
                BLOCKS 6 
                CACHE 16 
                COMP 2
            """)
            
            # Use the database
            self.cursor.execute(f"USE {self.database_name}")
            
            # Create stable (super table) for K-bar data
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS kbar_data (
                    ts TIMESTAMP,
                    open FLOAT,
                    high FLOAT,
                    low FLOAT,
                    close FLOAT,
                    volume BIGINT,
                    amount DOUBLE,
                    pre_close FLOAT,
                    change_rate FLOAT
                ) TAGS (
                    symbol NCHAR(20),
                    exchange NCHAR(10),
                    period NCHAR(10)
                )
            """)
            
            self.logger.info("Database and tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create database/tables: {str(e)}")
            raise
            
    def create_table_for_symbol(self, symbol: str, exchange: str = "SH", period: str = "1min"):
        """
        Create a subtable for a specific symbol.
        
        Args:
            symbol: Stock symbol (e.g., '000001')
            exchange: Exchange code (e.g., 'SH', 'SZ')
            period: Time period (e.g., '1min', '5min', '15min', '30min', '1hour', '1day')
        """
        table_name = f"{symbol}_{exchange}_{period}".lower()
        
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} USING kbar_data TAGS (
                    '{symbol}', '{exchange}', '{period}'
                )
            """)
            self.logger.debug(f"Created table for {symbol}.{exchange} ({period})")
            
        except Exception as e:
            self.logger.error(f"Failed to create table for {symbol}: {str(e)}")
            raise
            
    def insert_kbar_data(self, data: Union[Dict, List[Dict], pd.DataFrame], 
                        symbol: str, exchange: str = "SH", period: str = "1min"):
        """
        Insert K-bar data into TDengine.
        
        Args:
            data: K-bar data as dict, list of dicts, or pandas DataFrame
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
        """
        table_name = f"{symbol}_{exchange}_{period}".lower()
        
        # Ensure table exists
        self.create_table_for_symbol(symbol, exchange, period)
        
        try:
            if isinstance(data, pd.DataFrame):
                self._insert_dataframe(data, table_name)
            elif isinstance(data, list):
                self._insert_batch(data, table_name)
            elif isinstance(data, dict):
                self._insert_single(data, table_name)
            else:
                raise ValueError("Data must be dict, list of dicts, or pandas DataFrame")
                
            self.logger.debug(f"Inserted data for {symbol}.{exchange} ({period})")
            
        except Exception as e:
            self.logger.error(f"Failed to insert data for {symbol}: {str(e)}")
            raise
            
    def _insert_dataframe(self, df: pd.DataFrame, table_name: str):
        """Insert pandas DataFrame into TDengine."""
        # Convert DataFrame to list of tuples
        data_tuples = []
        for _, row in df.iterrows():
            data_tuples.append((
                row.get('timestamp', row.name),
                row.get('open'),
                row.get('high'),
                row.get('low'),
                row.get('close'),
                row.get('volume', 0),
                row.get('amount', 0.0),
                row.get('pre_close'),
                row.get('change_rate', 0.0)
            ))
            
        # Batch insert
        sql = f"""
            INSERT INTO {table_name} 
            (ts, open, high, low, close, volume, amount, pre_close, change_rate) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.executemany(sql, data_tuples)
        
    def _insert_batch(self, data_list: List[Dict], table_name: str):
        """Insert batch data into TDengine."""
        data_tuples = []
        for data in data_list:
            data_tuples.append((
                data.get('timestamp'),
                data.get('open'),
                data.get('high'),
                data.get('low'),
                data.get('close'),
                data.get('volume', 0),
                data.get('amount', 0.0),
                data.get('pre_close'),
                data.get('change_rate', 0.0)
            ))
            
        sql = f"""
            INSERT INTO {table_name} 
            (ts, open, high, low, close, volume, amount, pre_close, change_rate) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.executemany(sql, data_tuples)
        
    def _insert_single(self, data: Dict, table_name: str):
        """Insert single record into TDengine."""
        sql = f"""
            INSERT INTO {table_name} 
            (ts, open, high, low, close, volume, amount, pre_close, change_rate) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(sql, (
            data.get('timestamp'),
            data.get('open'),
            data.get('high'),
            data.get('low'),
            data.get('close'),
            data.get('volume', 0),
            data.get('amount', 0.0),
            data.get('pre_close'),
            data.get('change_rate', 0.0)
        ))
        
    def query_kbar_data(self, symbol: str, exchange: str = "SH", period: str = "1min",
                       start_time: Optional[datetime] = None, 
                       end_time: Optional[datetime] = None,
                       limit: Optional[int] = None) -> pd.DataFrame:
        """
        Query K-bar data from TDengine.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            start_time: Start time for query
            end_time: End time for query
            limit: Maximum number of records to return
            
        Returns:
            pandas DataFrame with K-bar data
        """
        table_name = f"{symbol}_{exchange}_{period}".lower()
        
        # Build query
        sql = f"SELECT * FROM {table_name}"
        params = []
        
        conditions = []
        if start_time:
            conditions.append("ts >= ?")
            params.append(start_time)
        if end_time:
            conditions.append("ts <= ?")
            params.append(end_time)
            
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        sql += " ORDER BY ts"
        
        if limit:
            sql += f" LIMIT {limit}"
            
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
                
            results = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            
            return pd.DataFrame(results, columns=columns)
            
        except Exception as e:
            self.logger.error(f"Failed to query data for {symbol}: {str(e)}")
            raise
            
    def get_latest_timestamp(self, symbol: str, exchange: str = "SH", period: str = "1min") -> Optional[datetime]:
        """Get the latest timestamp for a symbol."""
        table_name = f"{symbol}_{exchange}_{period}".lower()
        
        try:
            self.cursor.execute(f"SELECT LAST(ts) FROM {table_name}")
            result = self.cursor.fetchone()
            return result[0] if result and result[0] else None
            
        except Exception as e:
            self.logger.error(f"Failed to get latest timestamp for {symbol}: {str(e)}")
            return None
            
    def delete_data(self, symbol: str, exchange: str = "SH", period: str = "1min",
                   start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None):
        """Delete K-bar data from TDengine."""
        table_name = f"{symbol}_{exchange}_{period}".lower()
        
        sql = f"DELETE FROM {table_name}"
        params = []
        
        conditions = []
        if start_time:
            conditions.append("ts >= ?")
            params.append(start_time)
        if end_time:
            conditions.append("ts <= ?")
            params.append(end_time)
            
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
                
            self.logger.debug(f"Deleted data for {symbol}.{exchange} ({period})")
            
        except Exception as e:
            self.logger.error(f"Failed to delete data for {symbol}: {str(e)}")
            raise
            
    def get_symbols(self) -> List[Dict[str, str]]:
        """Get all symbols stored in the database."""
        try:
            self.cursor.execute("SHOW TABLES")
            tables = self.cursor.fetchall()
            
            symbols = []
            for table in tables:
                table_name = table[0]
                if '_' in table_name:
                    parts = table_name.split('_')
                    if len(parts) >= 3:
                        symbols.append({
                            'symbol': parts[0],
                            'exchange': parts[1],
                            'period': parts[2]
                        })
                        
            return symbols
            
        except Exception as e:
            self.logger.error(f"Failed to get symbols: {str(e)}")
            return []
            
    def close(self):
        """Close database connection."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            self.logger.info("TDengine connection closed")
            
        except Exception as e:
            self.logger.error(f"Error closing connection: {str(e)}")
            
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 