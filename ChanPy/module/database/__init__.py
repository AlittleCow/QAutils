"""
Database module for ChanPy

Provides database access functionality for K-bar and meta data.
"""

# Import main classes for easy access
from .db import DatabaseManager, create_database_manager
from .kbar_db_sqlite import KbarDatabase as SQLiteKbarDatabase
from .meta_db import MetaDatabase

__all__ = [
    'DatabaseManager', 'create_database_manager',
    'SQLiteKbarDatabase', 'MetaDatabase'
] 