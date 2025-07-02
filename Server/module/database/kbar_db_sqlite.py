"""
SQLite Database Module for K-bar Data Storage

This module provides a SQLite database interface for storing and retrieving
stock K-bar data (OHLCV data) with efficient indexing and querying.
"""

import logging
import sqlite3
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import pandas as pd
import os
from pathlib import Path


class KbarDatabase:
    """SQLite database interface for K-bar data storage."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SQLite connection for K-bar data.
        
        Args:
            config: Database configuration dictionary containing:
                - database_path: Path to SQLite database file (default: 'kbar_data.db')
                - create_dir: Whether to create directory if it doesn't exist (default: True)
        """
        self.config = config
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.database_path = config.get('database_path', 'kbar_data.db')
        self.logger = logging.getLogger(__name__)
        
        # Create directory if needed
        if config.get('create_dir', True):
            db_dir = os.path.dirname(self.database_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        
        # Connect to SQLite
        self._connect()
        
    def _connect(self):
        """Establish connection to SQLite."""
        try:
            self.conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=30.0
            )
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            self.cursor = self.conn.cursor()
            
            # Enable WAL mode for better concurrency
            self.cursor.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys=ON")
            
            self.logger.info(f"Connected to SQLite database: {self.database_path}")
            
            # Create database schema
            self._create_database()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to SQLite: {str(e)}")
            raise
            
    def _convert_timestamp(self, timestamp: Any) -> Optional[str]:
        """Convert various timestamp formats to ISO string format."""
        if timestamp is None:
            return None
        
        if isinstance(timestamp, str):
            return timestamp
        elif isinstance(timestamp, datetime):
            return timestamp.isoformat()
        elif hasattr(timestamp, 'to_pydatetime'):  # pandas Timestamp
            return timestamp.to_pydatetime().isoformat()
        elif hasattr(timestamp, 'isoformat'):  # datetime-like object
            return timestamp.isoformat()
        else:
            # Try to convert to string
            return str(timestamp)
            
    def _create_database(self):
        """Create database tables if they don't exist."""
        if not self.cursor or not self.conn:
            raise RuntimeError("Database connection not established")
            
        try:
            # Create symbols table to track all symbols
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    period TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, exchange, period)
                )
            """)
            
            # Create main kbar_data table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS kbar_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    period TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    amount REAL,
                    pre_close REAL,
                    change_rate REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, exchange, period, ts)
                )
            """)
            
            # Create indexes for efficient querying
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_kbar_symbol_exchange_period ON kbar_data(symbol, exchange, period)",
                "CREATE INDEX IF NOT EXISTS idx_kbar_ts ON kbar_data(ts)",
                "CREATE INDEX IF NOT EXISTS idx_kbar_symbol_ts ON kbar_data(symbol, exchange, period, ts)",
            ]
            
            for index_sql in indexes:
                self.cursor.execute(index_sql)
            
            self.conn.commit()
            self.logger.info("Database schema created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create database schema: {str(e)}")
            raise
            
    def create_table_for_symbol(self, symbol: str, exchange: str = "SH", period: str = "1min"):
        """
        Register a symbol in the symbols table.
        
        Args:
            symbol: Stock symbol (e.g., '000001')
            exchange: Exchange code (e.g., 'SH', 'SZ')
            period: Time period (e.g., '1min', '5min', '15min', '30min', '1hour', '1day')
        """
        if not self.cursor or not self.conn:
            raise RuntimeError("Database connection not established")
            
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO symbols (symbol, exchange, period) 
                VALUES (?, ?, ?)
            """, (symbol, exchange, period))
            self.conn.commit()
            self.logger.debug(f"Registered symbol {symbol}.{exchange} ({period})")
            
        except Exception as e:
            self.logger.error(f"Failed to register symbol {symbol}: {str(e)}")
            raise
            
    def insert_kbar_data(self, data: Union[Dict, List[Dict], pd.DataFrame], 
                        symbol: str, exchange: str = "SH", period: str = "1min"):
        """
        Insert K-bar data into SQLite.
        
        Args:
            data: K-bar data as dict, list of dicts, or pandas DataFrame
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
        """
        if not self.cursor or not self.conn:
            raise RuntimeError("Database connection not established")
            
        # Ensure symbol is registered
        self.create_table_for_symbol(symbol, exchange, period)
        
        try:
            if isinstance(data, pd.DataFrame):
                self._insert_dataframe(data, symbol, exchange, period)
            elif isinstance(data, list):
                self._insert_batch(data, symbol, exchange, period)
            elif isinstance(data, dict):
                self._insert_single(data, symbol, exchange, period)
            else:
                raise ValueError("Data must be dict, list of dicts, or pandas DataFrame")
                
            self.conn.commit()
            self.logger.debug(f"Inserted data for {symbol}.{exchange} ({period})")
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to insert data for {symbol}: {str(e)}")
            raise
            
    def _insert_dataframe(self, df: pd.DataFrame, symbol: str, exchange: str, period: str):
        """Insert pandas DataFrame into SQLite."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
            
        data_tuples = []
        for _, row in df.iterrows():
            # Handle timestamp - could be index or column
            timestamp = row.get('timestamp', row.name if hasattr(row, 'name') else None)
            if timestamp is None:
                continue
                
            data_tuples.append((
                symbol,
                exchange,
                period,
                self._convert_timestamp(timestamp),
                row.get('open'),
                row.get('high'),
                row.get('low'),
                row.get('close'),
                row.get('volume', 0),
                row.get('amount', 0.0),
                row.get('pre_close'),
                row.get('change_rate', 0.0)
            ))
            
        # Batch insert with REPLACE to handle duplicates
        sql = """
            INSERT OR REPLACE INTO kbar_data 
            (symbol, exchange, period, ts, open, high, low, close, volume, amount, pre_close, change_rate) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.executemany(sql, data_tuples)
        
    def _insert_batch(self, data_list: List[Dict], symbol: str, exchange: str, period: str):
        """Insert batch data into SQLite."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
            
        data_tuples = []
        for data in data_list:
            if 'timestamp' not in data:
                continue
                
            data_tuples.append((
                symbol,
                exchange,
                period,
                self._convert_timestamp(data.get('timestamp')),
                data.get('open'),
                data.get('high'),
                data.get('low'),
                data.get('close'),
                data.get('volume', 0),
                data.get('amount', 0.0),
                data.get('pre_close'),
                data.get('change_rate', 0.0)
            ))
            
        sql = """
            INSERT OR REPLACE INTO kbar_data 
            (symbol, exchange, period, ts, open, high, low, close, volume, amount, pre_close, change_rate) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.executemany(sql, data_tuples)
        
    def _insert_single(self, data: Dict, symbol: str, exchange: str, period: str):
        """Insert single record into SQLite."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
            
        if 'timestamp' not in data:
            raise ValueError("Data must contain 'timestamp' field")
            
        sql = """
            INSERT OR REPLACE INTO kbar_data 
            (symbol, exchange, period, ts, open, high, low, close, volume, amount, pre_close, change_rate) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(sql, (
            symbol,
            exchange,
            period,
            self._convert_timestamp(data.get('timestamp')),
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
        Query K-bar data from SQLite.
        
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
        if not self.cursor:
            raise RuntimeError("Database connection not established")
            
        # Build query
        sql = """
            SELECT ts, open, high, low, close, volume, amount, pre_close, change_rate 
            FROM kbar_data 
            WHERE symbol = ? AND exchange = ? AND period = ?
        """
        params: List[Any] = [symbol, exchange, period]
        
        if start_time:
            sql += " AND ts >= ?"
            params.append(self._convert_timestamp(start_time))
        if end_time:
            sql += " AND ts <= ?"
            params.append(self._convert_timestamp(end_time))
            
        sql += " ORDER BY ts"
        
        if limit:
            sql += f" LIMIT {limit}"
            
        try:
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            
            # Convert to DataFrame
            if results:
                columns = [description[0] for description in self.cursor.description]
                df_data = [dict(row) for row in results]
                df = pd.DataFrame(df_data)
                
                # Convert timestamp column back to datetime
                if 'ts' in df.columns:
                    df['ts'] = pd.to_datetime(df['ts'])
                
                return df
            else:
                # Return empty DataFrame with correct columns
                return pd.DataFrame(columns=pd.Index([
                    'ts', 'open', 'high', 'low', 'close', 
                    'volume', 'amount', 'pre_close', 'change_rate'
                ]))
            
        except Exception as e:
            self.logger.error(f"Failed to query data for {symbol}: {str(e)}")
            raise
            
    def get_latest_timestamp(self, symbol: str, exchange: str = "SH", period: str = "1min") -> Optional[datetime]:
        """Get the latest timestamp for a symbol."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
            
        try:
            self.cursor.execute("""
                SELECT MAX(ts) FROM kbar_data 
                WHERE symbol = ? AND exchange = ? AND period = ?
            """, (symbol, exchange, period))
            result = self.cursor.fetchone()
            if result and result[0]:
                return pd.to_datetime(result[0]).to_pydatetime()
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get latest timestamp for {symbol}: {str(e)}")
            return None
            
    def delete_data(self, symbol: str, exchange: str = "SH", period: str = "1min",
                   start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None):
        """Delete K-bar data from SQLite."""
        if not self.cursor or not self.conn:
            raise RuntimeError("Database connection not established")
            
        sql = "DELETE FROM kbar_data WHERE symbol = ? AND exchange = ? AND period = ?"
        params: List[Any] = [symbol, exchange, period]
        
        if start_time:
            sql += " AND ts >= ?"
            params.append(self._convert_timestamp(start_time))
        if end_time:
            sql += " AND ts <= ?"
            params.append(self._convert_timestamp(end_time))
            
        try:
            self.cursor.execute(sql, params)
            self.conn.commit()
            self.logger.debug(f"Deleted data for {symbol}.{exchange} ({period})")
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to delete data for {symbol}: {str(e)}")
            raise
            
    def get_symbols(self) -> List[Dict[str, str]]:
        """Get all symbols stored in the database."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
            
        try:
            self.cursor.execute("SELECT DISTINCT symbol, exchange, period FROM symbols ORDER BY symbol, exchange, period")
            results = self.cursor.fetchall()
            
            symbols = []
            for row in results:
                symbols.append({
                    'symbol': row['symbol'],
                    'exchange': row['exchange'],
                    'period': row['period']
                })
                        
            return symbols
            
        except Exception as e:
            self.logger.error(f"Failed to get symbols: {str(e)}")
            return []
    
    def get_data_count(self, symbol: str, exchange: str = "SH", period: str = "1min") -> int:
        """Get the count of records for a symbol."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
            
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM kbar_data 
                WHERE symbol = ? AND exchange = ? AND period = ?
            """, (symbol, exchange, period))
            result = self.cursor.fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            self.logger.error(f"Failed to get data count for {symbol}: {str(e)}")
            return 0
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
            
        try:
            # Get total records count
            self.cursor.execute("SELECT COUNT(*) FROM kbar_data")
            total_records = self.cursor.fetchone()[0]
            
            # Get total symbols count
            self.cursor.execute("SELECT COUNT(*) FROM symbols")
            total_symbols = self.cursor.fetchone()[0]
            
            # Get database file size
            db_size = os.path.getsize(self.database_path) if os.path.exists(self.database_path) else 0
            
            # Get date range
            self.cursor.execute("SELECT MIN(ts), MAX(ts) FROM kbar_data")
            date_range = self.cursor.fetchone()
            
            return {
                'database_path': self.database_path,
                'total_records': total_records,
                'total_symbols': total_symbols,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'earliest_date': date_range[0],
                'latest_date': date_range[1]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get database info: {str(e)}")
            return {}
            
    def close(self):
        """Close database connection."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            self.logger.info("SQLite connection closed")
            
        except Exception as e:
            self.logger.error(f"Error closing connection: {str(e)}")
            
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 