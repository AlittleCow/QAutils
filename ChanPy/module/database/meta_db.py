"""
SQLite Database Module for Meta Data Storage

This module provides a SQLite database interface for storing and retrieving
meta data such as stock information, exchange details, and other relational data.
"""

import logging
import sqlite3
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import os


class MetaDatabase:
    """SQLite database interface for meta data storage."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SQLite connection for meta data.
        
        Args:
            config: Database configuration dictionary containing:
                - database_path: Path to SQLite database file
                - timeout: Connection timeout (default: 30.0)
                - check_same_thread: SQLite threading mode (default: False)
        """
        self.config = config
        self.database_path = config.get('database_path', 'meta_data.db')
        self.timeout = config.get('timeout', 30.0)
        self.check_same_thread = config.get('check_same_thread', False)
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        db_dir = os.path.dirname(self.database_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        # Connect to SQLite
        self._connect()
        
    def _connect(self):
        """Establish connection to SQLite."""
        try:
            self.conn = sqlite3.connect(
                self.database_path,
                timeout=self.timeout,
                check_same_thread=self.check_same_thread
            )
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            self.cursor = self.conn.cursor()
            
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            self.logger.debug(f"Connected to SQLite database: {self.database_path}")
            
            # Create tables
            self._create_tables()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to SQLite: {str(e)}")
            raise
            
    def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            # Exchanges table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchanges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    country TEXT,
                    timezone TEXT,
                    trading_hours TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Stocks table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    exchange_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    sector TEXT,
                    industry TEXT,
                    market_cap REAL,
                    shares_outstanding BIGINT,
                    currency TEXT DEFAULT 'CNY',
                    is_active BOOLEAN DEFAULT 1,
                    list_date DATE,
                    delist_date DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exchange_id) REFERENCES exchanges (id),
                    UNIQUE(symbol, exchange_id)
                )
            """)
            
            # Indices table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS indices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    exchange_id INTEGER NOT NULL,
                    type TEXT,
                    base_date DATE,
                    base_value REAL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exchange_id) REFERENCES exchanges (id)
                )
            """)
            
            # Stock dividends table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_dividends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER NOT NULL,
                    ex_date DATE NOT NULL,
                    record_date DATE,
                    pay_date DATE,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'CNY',
                    type TEXT DEFAULT 'cash',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_id) REFERENCES stocks (id),
                    UNIQUE(stock_id, ex_date, type)
                )
            """)
            
            # Stock splits table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_splits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER NOT NULL,
                    ex_date DATE NOT NULL,
                    ratio REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_id) REFERENCES stocks (id),
                    UNIQUE(stock_id, ex_date)
                )
            """)
            
            # Data sources table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    base_url TEXT,
                    api_key TEXT,
                    rate_limit INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Data sync status table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sync_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER NOT NULL,
                    data_type TEXT NOT NULL,
                    period TEXT NOT NULL,
                    last_sync_time DATETIME,
                    last_sync_date DATE,
                    sync_status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_id) REFERENCES stocks (id),
                    UNIQUE(stock_id, data_type, period)
                )
            """)
            
            # Create indexes for better performance
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_stocks_exchange ON stocks(exchange_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_dividends_stock ON stock_dividends(stock_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_splits_stock ON stock_splits(stock_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_status ON data_sync_status(stock_id, data_type, period)")
            
            self.conn.commit()
            self.logger.debug("Database tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create tables: {str(e)}")
            raise
            
    def insert_exchange(self, code: str, name: str, **kwargs) -> int:
        """Insert or update exchange information."""
        try:
            sql = """
                INSERT OR REPLACE INTO exchanges (code, name, country, timezone, trading_hours, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(sql, (
                code,
                name,
                kwargs.get('country'),
                kwargs.get('timezone'),
                kwargs.get('trading_hours')
            ))
            self.conn.commit()
            
            # Get the ID
            self.cursor.execute("SELECT id FROM exchanges WHERE code = ?", (code,))
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to insert exchange {code}: {str(e)}")
            raise
            
    def insert_stock(self, symbol: str, exchange_code: str, name: str, **kwargs) -> int:
        """Insert or update stock information."""
        try:
            # Get exchange ID
            exchange_id = self.get_exchange_id(exchange_code)
            if not exchange_id:
                raise ValueError(f"Exchange {exchange_code} not found")
                
            sql = """
                INSERT OR REPLACE INTO stocks 
                (symbol, exchange_id, name, sector, industry, market_cap, shares_outstanding, 
                 currency, is_active, list_date, delist_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(sql, (
                symbol,
                exchange_id,
                name,
                kwargs.get('sector'),
                kwargs.get('industry'),
                kwargs.get('market_cap'),
                kwargs.get('shares_outstanding'),
                kwargs.get('currency', 'CNY'),
                kwargs.get('is_active', 1),
                kwargs.get('list_date'),
                kwargs.get('delist_date')
            ))
            self.conn.commit()
            
            # Get the ID
            self.cursor.execute("SELECT id FROM stocks WHERE symbol = ? AND exchange_id = ?", 
                              (symbol, exchange_id))
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to insert stock {symbol}: {str(e)}")
            raise
            
    def get_exchange_id(self, exchange_code: str) -> Optional[int]:
        """Get exchange ID by code."""
        try:
            self.cursor.execute("SELECT id FROM exchanges WHERE code = ?", (exchange_code,))
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to get exchange ID for {exchange_code}: {str(e)}")
            return None
            
    def get_stock_id(self, symbol: str, exchange_code: str) -> Optional[int]:
        """Get stock ID by symbol and exchange."""
        try:
            sql = """
                SELECT s.id FROM stocks s
                JOIN exchanges e ON s.exchange_id = e.id
                WHERE s.symbol = ? AND e.code = ?
            """
            self.cursor.execute(sql, (symbol, exchange_code))
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to get stock ID for {symbol}.{exchange_code}: {str(e)}")
            return None
            
    def get_stock_info(self, symbol: str, exchange_code: str) -> Optional[Dict]:
        """Get complete stock information."""
        try:
            sql = """
                SELECT s.*, e.code as exchange_code, e.name as exchange_name
                FROM stocks s
                JOIN exchanges e ON s.exchange_id = e.id
                WHERE s.symbol = ? AND e.code = ?
            """
            self.cursor.execute(sql, (symbol, exchange_code))
            result = self.cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to get stock info for {symbol}.{exchange_code}: {str(e)}")
            return None
            
    def get_all_stocks(self, exchange_code: Optional[str] = None, 
                      is_active: Optional[bool] = None) -> List[Dict]:
        """Get all stocks with optional filtering."""
        try:
            sql = """
                SELECT s.*, e.code as exchange_code, e.name as exchange_name
                FROM stocks s
                JOIN exchanges e ON s.exchange_id = e.id
            """
            params = []
            conditions = []
            
            if exchange_code:
                conditions.append("e.code = ?")
                params.append(exchange_code)
                
            if is_active is not None:
                conditions.append("s.is_active = ?")
                params.append(is_active)
                
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
                
            sql += " ORDER BY s.symbol"
            
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Failed to get all stocks: {str(e)}")
            return []
            
    def update_sync_status(self, stock_id: int, data_type: str, period: str, 
                          status: str = 'completed', error_message: str = None,
                          last_sync_date: datetime = None):
        """Update data synchronization status."""
        try:
            if last_sync_date is None:
                last_sync_date = datetime.now().date()
                
            sql = """
                INSERT OR REPLACE INTO data_sync_status 
                (stock_id, data_type, period, last_sync_time, last_sync_date, 
                 sync_status, error_message, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(sql, (
                stock_id, data_type, period, last_sync_date, status, error_message
            ))
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to update sync status: {str(e)}")
            raise
            
    def get_sync_status(self, stock_id: int, data_type: str, period: str) -> Optional[Dict]:
        """Get synchronization status for a stock."""
        try:
            sql = """
                SELECT * FROM data_sync_status
                WHERE stock_id = ? AND data_type = ? AND period = ?
            """
            self.cursor.execute(sql, (stock_id, data_type, period))
            result = self.cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to get sync status: {str(e)}")
            return None
            
    def insert_dividend(self, stock_id: int, ex_date: str, amount: float, **kwargs):
        """Insert dividend information."""
        try:
            sql = """
                INSERT OR REPLACE INTO stock_dividends 
                (stock_id, ex_date, record_date, pay_date, amount, currency, type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (
                stock_id,
                ex_date,
                kwargs.get('record_date'),
                kwargs.get('pay_date'),
                amount,
                kwargs.get('currency', 'CNY'),
                kwargs.get('type', 'cash')
            ))
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to insert dividend: {str(e)}")
            raise
            
    def insert_split(self, stock_id: int, ex_date: str, ratio: float):
        """Insert stock split information."""
        try:
            sql = """
                INSERT OR REPLACE INTO stock_splits (stock_id, ex_date, ratio)
                VALUES (?, ?, ?)
            """
            self.cursor.execute(sql, (stock_id, ex_date, ratio))
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to insert split: {str(e)}")
            raise
            
    def execute_query(self, sql: str, params: Tuple = None) -> List[Dict]:
        """Execute custom query and return results."""
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
                
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Failed to execute query: {str(e)}")
            raise
            
    def execute_non_query(self, sql: str, params: Tuple = None) -> int:
        """Execute non-query (INSERT, UPDATE, DELETE) and return affected rows."""
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
                
            self.conn.commit()
            return self.cursor.rowcount
            
        except Exception as e:
            self.logger.error(f"Failed to execute non-query: {str(e)}")
            raise
            
    def backup_database(self, backup_path: str):
        """Create a backup of the database."""
        try:
            with sqlite3.connect(backup_path) as backup_conn:
                self.conn.backup(backup_conn)
            self.logger.info(f"Database backed up to: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to backup database: {str(e)}")
            raise
            
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