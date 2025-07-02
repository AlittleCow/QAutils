# K-bar Database Comparison: TDengine vs SQLite

This document compares the TDengine and SQLite implementations of the K-bar database module.

## Overview

Both implementations provide the same API interface for storing and retrieving stock K-bar data (OHLCV data), making them drop-in replacements for each other.

## Configuration Differences

### TDengine Configuration (`kbar_db.py`)
```python
config = {
    'host': 'localhost',           # TDengine server host
    'port': 6030,                 # TDengine server port
    'user': 'root',               # Database username  
    'password': 'taosdata',       # Database password
    'database': 'kbar_db'         # Database name
}
```

### SQLite Configuration (`kbar_db_sqlite.py`)
```python
config = {
    'database_path': 'data/kbar_data.db',  # SQLite database file path
    'create_dir': True                      # Create directory if it doesn't exist
}
```

## Feature Comparison

| Feature | TDengine | SQLite | Notes |
|---------|----------|--------|-------|
| **Installation** | Requires TDengine server + taospy | Built-in Python sqlite3 | SQLite has no external dependencies |
| **Platform Support** | Linux/Enterprise Windows | All platforms | SQLite works on all platforms |
| **Performance** | Optimized for time-series | Good for moderate datasets | TDengine better for large datasets |
| **Scalability** | Excellent horizontal scaling | Single file, vertical scaling | TDengine better for distributed systems |
| **Storage** | Compressed time-series storage | Standard relational storage | TDengine more efficient for time-series |
| **Setup Complexity** | Requires server setup | Zero setup | SQLite is file-based |
| **Backup** | Server-based backup tools | Simple file copy | SQLite easier to backup |
| **Concurrent Access** | Excellent | Good with WAL mode | Both support concurrent reads |

## API Compatibility

Both implementations provide identical methods:

```python
# Initialize (only configuration differs)
db = KbarDatabase(config)

# All other methods are identical
db.insert_kbar_data(data, symbol, exchange, period)
db.query_kbar_data(symbol, exchange, period, start_time, end_time, limit)
db.get_latest_timestamp(symbol, exchange, period)
db.delete_data(symbol, exchange, period, start_time, end_time)
db.get_symbols()
db.close()
```

## Additional Features in SQLite Version

The SQLite version includes some extra utility methods:

```python
# Get record count for a symbol
count = db.get_data_count(symbol, exchange, period)

# Get database statistics
info = db.get_database_info()
```

## When to Use Each

### Use TDengine (`kbar_db.py`) when:
- You have very large datasets (millions+ records)
- You need distributed storage
- You require maximum time-series performance
- You have TDengine server infrastructure
- You're on Linux or have TDengine Enterprise

### Use SQLite (`kbar_db_sqlite.py`) when:
- You're on Windows without TDengine Enterprise
- You want zero-setup deployment
- You have moderate dataset sizes
- You need simple backup/migration (just copy the .db file)
- You're prototyping or developing locally
- You want minimal dependencies

## Migration Between Versions

To migrate from TDengine to SQLite (or vice versa):

```python
# Export from TDengine
with KbarDatabase(tdengine_config) as td_db:
    symbols = td_db.get_symbols()
    
    with KbarDatabase(sqlite_config) as sqlite_db:
        for symbol_info in symbols:
            # Query all data for this symbol
            data = td_db.query_kbar_data(
                symbol_info['symbol'], 
                symbol_info['exchange'], 
                symbol_info['period']
            )
            
            # Insert into SQLite
            if not data.empty:
                sqlite_db.insert_kbar_data(
                    data, 
                    symbol_info['symbol'], 
                    symbol_info['exchange'], 
                    symbol_info['period']
                )
```

## Performance Considerations

### SQLite Optimizations Applied
- WAL (Write-Ahead Logging) mode for better concurrency
- Proper indexes on frequently queried columns
- INSERT OR REPLACE for handling duplicates
- Transaction batching for bulk inserts

### TDengine Optimizations Applied
- Optimized for time-series data compression
- Automatic partitioning by time
- Efficient tag-based querying
- Built-in data retention policies

## Example Usage

Both versions can be used identically in your application:

```python
# Just change the import and config
from kbar_db_sqlite import KbarDatabase  # or from kbar_db import KbarDatabase

config = {'database_path': 'kbar_data.db'}  # SQLite config
# config = {'host': 'localhost', ...}       # TDengine config

with KbarDatabase(config) as db:
    # Rest of the code is identical
    db.insert_kbar_data(data, 'AAPL', 'NASDAQ', '1min')
    result = db.query_kbar_data('AAPL', 'NASDAQ', '1min')
```

## Conclusion

The SQLite version provides an excellent alternative to TDengine for Windows users or those who prefer a simpler setup. Both implementations maintain API compatibility, making it easy to switch between them based on your deployment requirements. 