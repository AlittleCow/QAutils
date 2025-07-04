"""
Chan Lines Database (SQLite)

This module provides SQLite-based storage and retrieval operations for Chan lines.
It handles the persistence of ChanLine objects and related data for analysis.
"""

import logging
import sqlite3
import json
import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager
from dataclasses import asdict

# Import Chan line related classes
from ...line import ChanLine, LineDirection, LineStatus, LineBreakType
from ...pen import ChanPen


class ChanDatabase:
    """
    SQLite database for Chan lines storage and retrieval.
    
    This class manages the chan_lines table and provides methods for storing,
    querying, and managing Chan line data for different symbols and periods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Chan database connection.
        
        Args:
            config: Database configuration dictionary containing:
                - database_path: Path to SQLite database file
                - timeout: Connection timeout (default: 30.0)
                - create_dir: Whether to create directory if not exists (default: True)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get database path
        self.db_path = config.get('database_path', 'data/chan_db.db')
        
        # Create directory if needed
        if config.get('create_dir', True):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Connection settings
        self.timeout = config.get('timeout', 30.0)
        self.check_same_thread = config.get('check_same_thread', False)
        
        # Initialize database
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize database and create tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create chan_lines table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chan_lines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        exchange TEXT NOT NULL,
                        period TEXT NOT NULL,
                        line_index INTEGER NOT NULL,
                        
                        -- Time and price info
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        start_price REAL NOT NULL,
                        end_price REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        length REAL NOT NULL,
                        
                        -- Line properties
                        direction INTEGER NOT NULL,
                        status INTEGER NOT NULL,
                        break_type INTEGER NOT NULL,
                        
                        -- Break info
                        break_price REAL,
                        break_pen_info TEXT,
                        
                        -- Flags
                        is_global BOOLEAN DEFAULT FALSE,
                        confirmed BOOLEAN DEFAULT FALSE,
                        
                        -- Pen info (serialized as JSON)
                        start_pen_info TEXT,
                        end_pen_info TEXT,
                        pens_info TEXT,
                        pen_count INTEGER DEFAULT 0,
                        
                        -- Metadata
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Content-based uniqueness constraint
                        UNIQUE(symbol, exchange, period, start_time, end_time, start_price, end_price, direction),
                        -- Keep sequence-based constraint for backward compatibility
                        UNIQUE(symbol, exchange, period, line_index)
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chan_lines_symbol_exchange_period 
                    ON chan_lines(symbol, exchange, period)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chan_lines_time 
                    ON chan_lines(start_time, end_time)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chan_lines_global 
                    ON chan_lines(is_global) WHERE is_global = TRUE
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chan_lines_content_unique 
                    ON chan_lines(symbol, exchange, period, start_time, end_time, direction)
                """)
                
                conn.commit()
                self.logger.debug("Chan database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize chan database: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=self.check_same_thread
            )
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _serialize_pen(self, pen: ChanPen) -> str:
        """Serialize pen object to JSON string."""
        if pen is None:
            return None
        
        pen_data = {
            'start_time': pen.start_time,
            'end_time': pen.end_time,
            'start_price': pen.start_price,
            'end_price': pen.end_price,
            'high': pen.high,
            'low': pen.low,
            'direction': pen.direction.value if pen.direction else None,
            'kbar_count': pen.kbar_count,
            'confirmed': pen.confirmed
        }
        return json.dumps(pen_data)
    
    def _serialize_pens(self, pens: List[ChanPen]) -> str:
        """Serialize list of pens to JSON string."""
        if not pens:
            return json.dumps([])
        
        pens_data = []
        for pen in pens:
            pen_data = {
                'start_time': pen.start_time,
                'end_time': pen.end_time,
                'start_price': pen.start_price,
                'end_price': pen.end_price,
                'high': pen.high,
                'low': pen.low,
                'direction': pen.direction.value if pen.direction else None,
                'kbar_count': pen.kbar_count,
                'confirmed': pen.confirmed
            }
            pens_data.append(pen_data)
        
        return json.dumps(pens_data)
    
    def store_chan_line(self, line: ChanLine, symbol: str, exchange: str, 
                       period: str, line_index: int) -> int:
        """
        Store a Chan line in the database.
        
        Args:
            line: ChanLine object to store
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            line_index: Line sequence index for this symbol/period
            
        Returns:
            Database ID of the stored line
            
        Raises:
            ValueError: If a duplicate line already exists
        """
        try:
            # Check for duplicate first
            if self.check_duplicate_exists(line, symbol, exchange, period):
                duplicate_id = self.get_duplicate_line_id(line, symbol, exchange, period)
                error_msg = (f"Duplicate ChanLine already exists for {symbol}.{exchange} ({period}). "
                           f"Existing line ID: {duplicate_id}. "
                           f"Line details: {line.start_time} to {line.end_time}, "
                           f"direction: {line.direction.name}, "
                           f"price range: {line.start_price} to {line.end_price}")
                self.logger.warning(error_msg)
                raise ValueError(error_msg)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare break pen info
                break_pen_info = None
                if line.break_pen:
                    break_pen_info = self._serialize_pen(line.break_pen)
                
                # Insert line data (changed from INSERT OR REPLACE to INSERT)
                cursor.execute("""
                    INSERT INTO chan_lines (
                        symbol, exchange, period, line_index,
                        start_time, end_time, start_price, end_price,
                        high, low, length, direction, status, break_type,
                        break_price, break_pen_info, is_global, confirmed,
                        start_pen_info, end_pen_info, pens_info, pen_count,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, exchange, period, line_index,
                    line.start_time, line.end_time, line.start_price, line.end_price,
                    line.high, line.low, line.length,
                    line.direction.value, line.status.value, line.break_type.value,
                    line.break_price, break_pen_info, line.is_global, line.confirmed,
                    self._serialize_pen(line.start_pen),
                    self._serialize_pen(line.end_pen),
                    self._serialize_pens(line.pens),
                    line.pen_count,
                    datetime.now().isoformat()
                ))
                
                line_id = cursor.lastrowid
                if line_id is None:
                    raise RuntimeError("Failed to get inserted line ID")
                conn.commit()
                
                self.logger.debug(f"Stored Chan line {line_index} for {symbol}.{exchange} ({period}) with DB ID {line_id}")
                return line_id
                
        except ValueError:
            # Re-raise ValueError for duplicate detection
            raise
        except Exception as e:
            self.logger.error(f"Failed to store Chan line: {str(e)}")
            raise
    
    def store_chan_line_safe(self, line: ChanLine, symbol: str, exchange: str, 
                           period: str, line_index: int, skip_duplicates: bool = True) -> Optional[int]:
        """
        Store a Chan line in the database with safe duplicate handling.
        
        Args:
            line: ChanLine object to store
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            line_index: Line sequence index for this symbol/period
            skip_duplicates: If True, skip duplicates; if False, raise error
            
        Returns:
            Database ID of the stored line, or None if skipped due to duplicate
        """
        try:
            return self.store_chan_line(line, symbol, exchange, period, line_index)
        except ValueError as e:
            if skip_duplicates:
                self.logger.info(f"Skipping duplicate ChanLine for {symbol}.{exchange} ({period})")
                return None
            else:
                raise e
    
    def store_chan_lines(self, lines: List[ChanLine], symbol: str, exchange: str, 
                        period: str, clear_existing: bool = True) -> List[int]:
        """
        Store multiple Chan lines for a symbol/period.
        
        Args:
            lines: List of ChanLine objects to store
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            clear_existing: Whether to clear existing lines first
            
        Returns:
            List of database IDs for stored lines (excludes None values for skipped duplicates)
        """
        if clear_existing:
            self.clear_chan_lines(symbol, exchange, period)
        
        line_ids = []
        skipped_count = 0
        
        for i, line in enumerate(lines):
            try:
                line_id = self.store_chan_line_safe(line, symbol, exchange, period, i, skip_duplicates=True)
                if line_id is not None:
                    line_ids.append(line_id)
                else:
                    skipped_count += 1
            except Exception as e:
                self.logger.error(f"Failed to store line {i} for {symbol}.{exchange} ({period}): {str(e)}")
                continue
        
        stored_count = len(line_ids)
        total_count = len(lines)
        
        if skipped_count > 0:
            self.logger.info(f"Stored {stored_count} Chan lines for {symbol}.{exchange} ({period}). "
                           f"Skipped {skipped_count} duplicates out of {total_count} total lines.")
        else:
            self.logger.info(f"Stored {stored_count} Chan lines for {symbol}.{exchange} ({period})")
        
        return line_ids
    
    def get_chan_lines(self, symbol: str, exchange: str, period: str,
                      start_time: Optional[str] = None, end_time: Optional[str] = None,
                      status: Optional[LineStatus] = None,
                      direction: Optional[LineDirection] = None,
                      is_global: Optional[bool] = None,
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve Chan lines from database.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            start_time: Filter by start time (inclusive)
            end_time: Filter by end time (inclusive)
            status: Filter by line status
            direction: Filter by line direction
            is_global: Filter by global flag
            limit: Maximum number of records to return
            
        Returns:
            List of line data dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query
                query = """
                    SELECT * FROM chan_lines 
                    WHERE symbol = ? AND exchange = ? AND period = ?
                """
                params: List[Any] = [symbol, exchange, period]
                
                if start_time:
                    query += " AND start_time >= ?"
                    params.append(start_time)
                
                if end_time:
                    query += " AND end_time <= ?"
                    params.append(end_time)
                
                if status is not None:
                    query += " AND status = ?"
                    params.append(status.value)
                
                if direction is not None:
                    query += " AND direction = ?"
                    params.append(direction.value)
                
                if is_global is not None:
                    query += " AND is_global = ?"
                    params.append(1 if is_global else 0)
                
                query += " ORDER BY line_index"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to dictionaries
                lines = []
                for row in rows:
                    line_data = dict(row)
                    lines.append(line_data)
                
                return lines
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve Chan lines: {str(e)}")
            raise
    
    def get_latest_chan_line(self, symbol: str, exchange: str, period: str) -> Optional[Dict[str, Any]]:
        """Get the most recent Chan line for a symbol/period."""
        lines = self.get_chan_lines(symbol, exchange, period, limit=1)
        return lines[0] if lines else None
    
    def get_global_chan_line(self, symbol: str, exchange: str, period: str) -> Optional[Dict[str, Any]]:
        """Get the current global Chan line for a symbol/period."""
        lines = self.get_chan_lines(symbol, exchange, period, is_global=True, limit=1)
        return lines[0] if lines else None
    
    def update_chan_line_status(self, line_id: int, status: LineStatus,
                               break_type: Optional[LineBreakType] = None,
                               break_price: Optional[float] = None) -> bool:
        """
        Update Chan line status and break information.
        
        Args:
            line_id: Database ID of the line
            status: New line status
            break_type: New break type (optional)
            break_price: Break price (optional)
            
        Returns:
            True if update was successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                update_query = "UPDATE chan_lines SET status = ?, updated_at = ?"
                params: List[Any] = [status.value, datetime.now().isoformat()]
                
                if break_type is not None:
                    update_query += ", break_type = ?"
                    params.append(break_type.value)
                
                if break_price is not None:
                    update_query += ", break_price = ?"
                    params.append(break_price)
                
                update_query += " WHERE id = ?"
                params.append(line_id)
                
                cursor.execute(update_query, params)
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to update Chan line status: {str(e)}")
            return False
    
    def delete_chan_line(self, line_id: int) -> bool:
        """Delete a specific Chan line by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chan_lines WHERE id = ?", (line_id,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to delete Chan line: {str(e)}")
            return False
    
    def clear_chan_lines(self, symbol: str, exchange: str, period: str) -> int:
        """
        Clear all Chan lines for a specific symbol/exchange/period.
        
        Returns:
            Number of lines deleted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM chan_lines 
                    WHERE symbol = ? AND exchange = ? AND period = ?
                """, (symbol, exchange, period))
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleared {deleted_count} Chan lines for {symbol}.{exchange} ({period})")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to clear Chan lines: {str(e)}")
            return 0
    
    def get_symbols_with_lines(self) -> List[Dict[str, str]]:
        """Get all symbol/exchange/period combinations that have Chan lines."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT symbol, exchange, period, COUNT(*) as line_count
                    FROM chan_lines 
                    GROUP BY symbol, exchange, period
                    ORDER BY symbol, exchange, period
                """)
                
                symbols = []
                for row in cursor.fetchall():
                    symbols.append({
                        'symbol': row['symbol'],
                        'exchange': row['exchange'],
                        'period': row['period'],
                        'line_count': row['line_count']
                    })
                
                return symbols
                
        except Exception as e:
            self.logger.error(f"Failed to get symbols with lines: {str(e)}")
            return []
    
    def get_line_statistics(self, symbol: str, exchange: str, period: str) -> Dict[str, Any]:
        """Get statistics about Chan lines for a symbol/period."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_lines,
                        SUM(CASE WHEN direction = 1 THEN 1 ELSE 0 END) as up_lines,
                        SUM(CASE WHEN direction = -1 THEN 1 ELSE 0 END) as down_lines,
                        SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as broken_lines,
                        SUM(CASE WHEN is_global = 1 THEN 1 ELSE 0 END) as global_lines,
                        AVG(length) as avg_length,
                        MAX(length) as max_length,
                        MIN(length) as min_length,
                        AVG(pen_count) as avg_pen_count
                    FROM chan_lines 
                    WHERE symbol = ? AND exchange = ? AND period = ?
                """, (symbol, exchange, period))
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                else:
                    return {
                        'total_lines': 0,
                        'up_lines': 0,
                        'down_lines': 0,
                        'broken_lines': 0,
                        'global_lines': 0,
                        'avg_length': 0.0,
                        'max_length': 0.0,
                        'min_length': 0.0,
                        'avg_pen_count': 0.0
                    }
                
        except Exception as e:
            self.logger.error(f"Failed to get line statistics: {str(e)}")
            return {}
    
    def backup_database(self, backup_path: str):
        """Create a backup of the database."""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to backup database: {str(e)}")
            raise
    
    def execute_query(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """Execute a custom SQL query and return results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                
                # For SELECT queries, return results
                if sql.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    # For other queries, commit and return empty list
                    conn.commit()
                    return []
                    
        except Exception as e:
            self.logger.error(f"Failed to execute query: {str(e)}")
            raise
    
    def close(self):
        """Close database connection (for compatibility with connection manager)."""
        # SQLite connections are managed by context manager, so nothing to do here
        self.logger.debug("Chan database connection closed")
    
    def reset_auto_increment(self) -> bool:
        """
        Reset the auto-increment counter for chan_lines table.
        
        This will make the next inserted record have ID = 1 (if table is empty)
        or ID = max(current_id) + 1 (if table has records).
        
        Returns:
            True if reset was successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Reset the sqlite_sequence table entry for chan_lines
                cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'chan_lines'")
                
                # If there are existing records, set the sequence to the max ID
                cursor.execute("SELECT MAX(id) FROM chan_lines")
                max_id = cursor.fetchone()[0]
                
                if max_id is not None:
                    cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('chan_lines', ?)", (max_id,))
                
                conn.commit()
                self.logger.info("Auto-increment counter reset for chan_lines table")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to reset auto-increment counter: {str(e)}")
            return False
    
    def get_next_id(self) -> int:
        """
        Get the next ID that would be assigned to a new record.
        
        Returns:
            Next auto-increment ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check sqlite_sequence table
                cursor.execute("SELECT seq FROM sqlite_sequence WHERE name = 'chan_lines'")
                result = cursor.fetchone()
                
                if result:
                    return result[0] + 1
                else:
                    # If no sequence entry, check if table has records
                    cursor.execute("SELECT MAX(id) FROM chan_lines")
                    max_id = cursor.fetchone()[0]
                    return (max_id + 1) if max_id else 1
                    
        except Exception as e:
            self.logger.error(f"Failed to get next ID: {str(e)}")
            return 1
    
    def check_duplicate_exists(self, line: ChanLine, symbol: str, exchange: str, period: str) -> bool:
        """
        Check if a ChanLine with the same content already exists in the database.
        
        Args:
            line: ChanLine object to check
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            
        Returns:
            True if duplicate exists, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check for content-based duplicate
                cursor.execute("""
                    SELECT COUNT(*) FROM chan_lines 
                    WHERE symbol = ? AND exchange = ? AND period = ? 
                    AND start_time = ? AND end_time = ? 
                    AND start_price = ? AND end_price = ? 
                    AND direction = ?
                """, (
                    symbol, exchange, period,
                    line.start_time, line.end_time,
                    line.start_price, line.end_price,
                    line.direction.value
                ))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"Failed to check for duplicates: {str(e)}")
            return False
    
    def get_duplicate_line_id(self, line: ChanLine, symbol: str, exchange: str, period: str) -> Optional[int]:
        """
        Get the ID of a duplicate ChanLine if it exists.
        
        Args:
            line: ChanLine object to check
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            
        Returns:
            Database ID of duplicate line if found, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check for content-based duplicate
                cursor.execute("""
                    SELECT id FROM chan_lines 
                    WHERE symbol = ? AND exchange = ? AND period = ? 
                    AND start_time = ? AND end_time = ? 
                    AND start_price = ? AND end_price = ? 
                    AND direction = ?
                    LIMIT 1
                """, (
                    symbol, exchange, period,
                    line.start_time, line.end_time,
                    line.start_price, line.end_price,
                    line.direction.value
                ))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            self.logger.error(f"Failed to get duplicate line ID: {str(e)}")
            return None
    
    def get_duplicate_statistics(self, symbol: str, exchange: str, period: str) -> Dict[str, Any]:
        """
        Get statistics about potential duplicates for a symbol/period.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            
        Returns:
            Dictionary with duplicate statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find groups of lines that might be duplicates
                cursor.execute("""
                    SELECT 
                        start_time, end_time, start_price, end_price, direction,
                        COUNT(*) as duplicate_count,
                        GROUP_CONCAT(id) as line_ids
                    FROM chan_lines 
                    WHERE symbol = ? AND exchange = ? AND period = ?
                    GROUP BY start_time, end_time, start_price, end_price, direction
                    HAVING COUNT(*) > 1
                    ORDER BY duplicate_count DESC
                """, (symbol, exchange, period))
                
                duplicate_groups = []
                total_duplicates = 0
                
                for row in cursor.fetchall():
                    group_info = {
                        'start_time': row['start_time'],
                        'end_time': row['end_time'],
                        'start_price': row['start_price'],
                        'end_price': row['end_price'],
                        'direction': row['direction'],
                        'duplicate_count': row['duplicate_count'],
                        'line_ids': [int(id_str) for id_str in row['line_ids'].split(',')]
                    }
                    duplicate_groups.append(group_info)
                    total_duplicates += row['duplicate_count'] - 1  # Subtract 1 to count only extras
                
                # Get total line count
                cursor.execute("""
                    SELECT COUNT(*) as total_lines FROM chan_lines 
                    WHERE symbol = ? AND exchange = ? AND period = ?
                """, (symbol, exchange, period))
                
                total_lines = cursor.fetchone()['total_lines']
                
                return {
                    'symbol': symbol,
                    'exchange': exchange,
                    'period': period,
                    'total_lines': total_lines,
                    'duplicate_groups': len(duplicate_groups),
                    'total_duplicates': total_duplicates,
                    'duplicate_percentage': (total_duplicates / total_lines * 100) if total_lines > 0 else 0,
                    'duplicate_details': duplicate_groups
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get duplicate statistics: {str(e)}")
            return {
                'symbol': symbol,
                'exchange': exchange,
                'period': period,
                'total_lines': 0,
                'duplicate_groups': 0,
                'total_duplicates': 0,
                'duplicate_percentage': 0,
                'duplicate_details': []
            }
    
    def remove_duplicates(self, symbol: str, exchange: str, period: str, keep_first: bool = True) -> int:
        """
        Remove duplicate lines for a symbol/period, keeping only one instance of each.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            keep_first: If True, keep the first occurrence; if False, keep the last
            
        Returns:
            Number of duplicate lines removed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find duplicate groups
                duplicate_stats = self.get_duplicate_statistics(symbol, exchange, period)
                removed_count = 0
                
                for group in duplicate_stats['duplicate_details']:
                    line_ids = group['line_ids']
                    if len(line_ids) > 1:
                        # Keep the first or last ID, delete the rest
                        if keep_first:
                            ids_to_delete = line_ids[1:]
                        else:
                            ids_to_delete = line_ids[:-1]
                        
                        # Delete the duplicate IDs
                        placeholders = ','.join(['?' for _ in ids_to_delete])
                        cursor.execute(f"DELETE FROM chan_lines WHERE id IN ({placeholders})", ids_to_delete)
                        removed_count += len(ids_to_delete)
                
                conn.commit()
                
                if removed_count > 0:
                    self.logger.info(f"Removed {removed_count} duplicate lines for {symbol}.{exchange} ({period})")
                
                return removed_count
                
        except Exception as e:
            self.logger.error(f"Failed to remove duplicates: {str(e)}")
            return 0
