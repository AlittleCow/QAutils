# Database Wrapper System for Stock Data

This module provides a unified database interface for managing stock market data using two specialized databases:

- **TDengine**: For time-series K-bar data (OHLCV data) storage
- **SQLite**: For relational meta data storage (stock info, exchanges, dividends, etc.)

## Architecture

```
db.py (Generic Wrapper)
├── kbar_db.py (TDengine Interface)
└── meta_db.py (SQLite Interface)
```

## Features

### K-bar Data (TDengine)
- High-performance time-series data storage
- Support for multiple time periods (1min, 5min, 15min, 30min, 1hour, 1day)
- Efficient querying with time range filters
- Automatic table creation for new symbols
- Batch data insertion support

### Meta Data (SQLite)
- Stock information and metadata
- Exchange details
- Dividend and split history
- Data synchronization status tracking
- Foreign key relationships for data integrity

## Installation

1. Install TDengine server and client
2. Install Python dependencies:

```bash
pip install pandas taospy
```

## Quick Start

```python
from db import create_database_manager

# Configure databases
kbar_config = {
    'host': 'localhost',
    'port': 6030,
    'user': 'root',
    'password': 'taosdata',
    'database': 'stock_kbar'
}

meta_config = {
    'database_path': 'data/stock_meta.db'
}

# Create database manager
with create_database_manager(kbar_config, meta_config) as db:
    
    # Setup a stock
    stock_id = db.setup_stock(
        symbol='000001',
        exchange='SH',
        name='平安银行',
        sector='Banking'
    )
    
    # Store K-bar data
    kbar_data = [{
        'timestamp': '2024-01-01 09:30:00',
        'open': 10.0,
        'high': 10.1,
        'low': 9.9,
        'close': 10.05,
        'volume': 1000000
    }]
    
    db.store_kbar_data('000001', 'SH', '1min', kbar_data)
    
    # Query data
    df = db.get_kbar_data('000001', 'SH', '1min', limit=100)
    print(df.head())
```

## Configuration

### TDengine Configuration
```python
kbar_config = {
    'host': 'localhost',      # TDengine server host
    'port': 6030,             # TDengine server port
    'user': 'root',           # Database username
    'password': 'taosdata',   # Database password
    'database': 'stock_kbar'  # Database name
}
```

### SQLite Configuration
```python
meta_config = {
    'database_path': 'data/stock_meta.db',  # SQLite file path
    'timeout': 30.0,                        # Connection timeout
    'check_same_thread': False              # Threading mode
}
```

## Data Models

### K-bar Data Schema (TDengine)
```sql
CREATE TABLE kbar_data (
    ts TIMESTAMP,           -- Timestamp
    open FLOAT,            -- Open price
    high FLOAT,            -- High price
    low FLOAT,             -- Low price
    close FLOAT,           -- Close price
    volume BIGINT,         -- Volume
    amount DOUBLE,         -- Amount
    pre_close FLOAT,       -- Previous close
    change_rate FLOAT      -- Change rate
) TAGS (
    symbol NCHAR(20),      -- Stock symbol
    exchange NCHAR(10),    -- Exchange code
    period NCHAR(10)       -- Time period
)
```

### Meta Data Schema (SQLite)

#### Stocks Table
```sql
CREATE TABLE stocks (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    exchange_id INTEGER,
    name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    market_cap REAL,
    shares_outstanding BIGINT,
    currency TEXT DEFAULT 'CNY',
    is_active BOOLEAN DEFAULT 1,
    list_date DATE,
    delist_date DATE
);
```

## API Reference

### DatabaseManager

#### Setup and Configuration
- `setup_stock(symbol, exchange, name, **kwargs)` - Setup stock in both databases
- `get_stock_info(symbol, exchange)` - Get stock metadata
- `get_all_stocks()` - Get all stocks

#### K-bar Data Operations
- `store_kbar_data(symbol, exchange, period, data)` - Store K-bar data
- `get_kbar_data(symbol, exchange, period, start_time, end_time, limit)` - Query K-bar data
- `get_latest_timestamp(symbol, exchange, period)` - Get latest data timestamp
- `delete_kbar_data(symbol, exchange, period, start_time, end_time)` - Delete K-bar data

#### Meta Data Operations
- `store_dividend(symbol, exchange, ex_date, amount, **kwargs)` - Store dividend info
- `store_split(symbol, exchange, ex_date, ratio)` - Store split info
- `get_sync_status(symbol, exchange, data_type, period)` - Get sync status

#### Utility Functions
- `get_database_stats()` - Get database statistics
- `backup_meta_database(backup_path)` - Backup meta database
- `execute_meta_query(sql, params)` - Execute custom SQL query

## Examples

See `example_usage.py` for comprehensive usage examples.

## Performance Considerations

1. **Batch Operations**: Use batch insertion for better performance
2. **Time Indexing**: TDengine automatically optimizes time-based queries
3. **Connection Pooling**: Use context managers to properly handle connections
4. **Data Retention**: Configure TDengine retention policies based on your needs

## Error Handling

The system includes comprehensive error handling and logging:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Database operations will log errors and warnings
```

## Dependencies

- `pandas`: Data manipulation and analysis
- `taospy`: TDengine Python connector
- `sqlite3`: Built-in SQLite interface
- `logging`: Built-in logging module

## License

This module is part of the QAutils project. 