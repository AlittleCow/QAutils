"""
Example Usage of Modular Chan Algorithm

This example demonstrates how to use the improved modular Chan algorithm implementation
that eliminates duplicate data loading and provides multiple usage patterns.

=== KEY IMPROVEMENTS ===

1. **Eliminated Duplicate Data Loading**
   - Before: Data loaded twice (context initialization + manual loading)
   - After: Single efficient loading with configurable options

2. **Multiple Usage Patterns**
   - Simple auto-loading (recommended for most cases)
   - Manual data loading (for custom data sources)
   - Context-based data reuse

3. **Better Performance**
   - 50% reduction in database queries
   - Lower memory usage
   - Faster initialization

=== USAGE PATTERNS ===

**Pattern 1: Simple Auto-Loading (Recommended)**
```python
processor = ChanProcessor(symbol='002120', exchange='SZ', period='daily')
results = processor.process_kbars_auto()
processor.close()
```

**Pattern 2: Manual Data Loading (For Custom Data)**
```python
processor = ChanProcessor(symbol='002120', exchange='SZ', period='daily', auto_load_data=False)
kbars = load_custom_data()  # Your custom data loading
results = processor.process_kbars(kbars)
processor.close()
```

**Pattern 3: Context Manager (Auto Cleanup)**
```python
with ChanProcessor(symbol='002120', exchange='SZ', period='daily') as processor:
    results = processor.process_kbars_auto()
    # Automatic cleanup when exiting
```

=== CONFIGURATION OPTIONS ===

- `auto_load_data`: Whether to automatically load data during initialization (default: True)
- `kbar_limit`: Maximum number of K-bars to load (default: 1000)
- `start_time`, `end_time`: Time range filtering (format: "YYYY-MM-DD HH:MM:SS")
- Processing parameters: `strict_fractal_mode`, `min_pen_length`, `min_kbar_count`, `min_line_pens`

=== LOGGING FEATURES ===

This script includes comprehensive logging to both console and file:

1. Automatic file logging: Logs are automatically written to files in the 'logs' directory
2. Multiple log files: Different functions create separate log files for better organization
3. Configurable logging: Use configure_logging_parameters() to customize:
   - Log level (DEBUG, INFO, WARNING, ERROR)
   - Log directory location
   - Log file prefix
   - Include timestamp in filenames

Usage examples:
- Basic: Just run the script - logs will be created automatically
- Custom: Call configure_logging_parameters() before running demonstrations
- Advanced: Modify setup_logging() calls in individual functions for fine-grained control

Log files created:
- chan_main.log: Main application log
- chan_simple.log: Simple usage example log
- chan_comparison.log: Loading approach comparison log
- chan_improved.log: Improved processing workflow log
- chan_step_by_step.log: Detailed step-by-step processing logs
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional

# Add paths to allow imports when running directly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # QAutils
grandparent_dir = os.path.dirname(parent_dir)  # qautil root

# Add paths for imports
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now we can import from the ChanPy package
try:
    # Try relative imports first (works when run as module)
    from .chan_processor import ChanProcessor
    from .chan import Kbar
except ImportError:
    # Fall back to absolute imports (works when run directly)
    from QAutils.ChanPy.chan_processor import ChanProcessor
    from QAutils.ChanPy.chan import Kbar

# Import database modules from local module directory
try:
    # Try relative imports first (works when run as module)
    from .module.database.kbar_db_sqlite import KbarDatabase as SQLiteKbarDatabase
    from .module.database.meta_db import MetaDatabase  
    from .module.database.db import DatabaseManager
except ImportError:
    # Fall back to absolute imports (works when run directly)
    from QAutils.ChanPy.module.database.kbar_db_sqlite import KbarDatabase as SQLiteKbarDatabase
    from QAutils.ChanPy.module.database.meta_db import MetaDatabase
    from QAutils.ChanPy.module.database.db import DatabaseManager

# Create a custom database manager configuration for SQLite
def create_sqlite_database_manager():
    """Create a database manager configured for SQLite with the correct path."""
    # Absolute path to the databases - using the correct database files
    db_path = os.path.join(parent_dir, 'Server', 'tdx_db', 'stock_kbar.db')
    meta_db_path = os.path.join(parent_dir, 'Server', 'tdx_db', 'stock_meta.db')
    chan_db_path = os.path.join(parent_dir, 'Server', 'tdx_db', 'chan_db.db')
    
    # Check if the database files exist
    missing_files = []
    if not os.path.exists(db_path):
        missing_files.append(f"stock_kbar.db at {db_path}")
    else:
        print(f"✓ Found kbar database: {db_path}")
        
    if not os.path.exists(meta_db_path):
        missing_files.append(f"stock_meta.db at {meta_db_path}")
    else:
        print(f"✓ Found meta database: {meta_db_path}")
        
    if not os.path.exists(chan_db_path):
        missing_files.append(f"chan_db.db at {chan_db_path}")
    else:
        print(f"✓ Found chan database: {chan_db_path}")
    
    if missing_files:
        print(f"Warning: Missing database files: {', '.join(missing_files)}")
        # Don't return None, let the system try to work with available files
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    config = {
        'kbar_config': {
            'enabled': True,
            'type': 'sqlite',
            'sqlite': {
                'enabled': True,
                'database_path': db_path,
                'create_dir': True
            }
        },
        'meta_config': {
            'enabled': True,
            'database_path': meta_db_path,
            'timeout': 30.0,
            'check_same_thread': False
        },
        'chan_config': {
            'enabled': True,
            'database_path': chan_db_path,
            'timeout': 30.0,
            'check_same_thread': False,
            'create_dir': True
        },
        'kbar_type': 'sqlite'
    }
    
    try:
        return DatabaseManager(config)
    except Exception as e:
        print(f"Failed to create database manager: {e}")
        return None

# Set up database availability
try:
    db_manager_factory = create_sqlite_database_manager
    DATABASE_AVAILABLE = True
    print("✓ SQLite database configuration loaded successfully")
except Exception as e:
    print(f"Warning: Database module not available: {e}")
    print("Using synthetic data.")
    DATABASE_AVAILABLE = False

# Shared configuration variables
DEFAULT_SYMBOL = "002120"
DEFAULT_EXCHANGE = "SZ"
DEFAULT_PERIOD = "daily"
DEFAULT_LIMIT = 1000
DEFAULT_START_TIME = "2018-07-30 00:00:00"
DEFAULT_END_TIME = "2019-06-01 00:00:00"


def configure_analysis_parameters(symbol: Optional[str] = None, exchange: Optional[str] = None, 
                                period: Optional[str] = None, limit: Optional[int] = None,
                                start_time: Optional[str] = None, end_time: Optional[str] = None):
    """
    Configure the default analysis parameters
    
    Args:
        symbol: Stock symbol (e.g., "002120", "000001")
        exchange: Exchange code (e.g., "SZ", "SH")
        period: Time period (e.g., "daily", "1min", "5min")
        limit: Maximum number of kbars to load
        start_time: Start time for data range (format: "YYYY-MM-DD HH:MM:SS")
        end_time: End time for data range (format: "YYYY-MM-DD HH:MM:SS")
    """
    global DEFAULT_SYMBOL, DEFAULT_EXCHANGE, DEFAULT_PERIOD, DEFAULT_LIMIT, DEFAULT_START_TIME, DEFAULT_END_TIME
    
    if symbol is not None:
        DEFAULT_SYMBOL = symbol
    if exchange is not None:
        DEFAULT_EXCHANGE = exchange
    if period is not None:
        DEFAULT_PERIOD = period
    if limit is not None:
        DEFAULT_LIMIT = limit
    if start_time is not None:
        DEFAULT_START_TIME = start_time
    if end_time is not None:
        DEFAULT_END_TIME = end_time
    
    time_range = ""
    if DEFAULT_START_TIME or DEFAULT_END_TIME:
        time_range = f", time_range={DEFAULT_START_TIME or 'unlimited'} to {DEFAULT_END_TIME or 'unlimited'}"
    
    print(f"Analysis parameters configured: {DEFAULT_SYMBOL}.{DEFAULT_EXCHANGE} ({DEFAULT_PERIOD}), limit={DEFAULT_LIMIT}{time_range}")


def get_current_configuration() -> dict:
    """Get the current configuration parameters"""
    return {
        'symbol': DEFAULT_SYMBOL,
        'exchange': DEFAULT_EXCHANGE,
        'period': DEFAULT_PERIOD,
        'limit': DEFAULT_LIMIT,
        'start_time': DEFAULT_START_TIME,
        'end_time': DEFAULT_END_TIME
    }

def load_kbar_data_from_database(symbol: str = "000001", exchange: str = "SH", 
                                period: str = "1min", limit: int = 50,
                                start_time: Optional[str] = None, end_time: Optional[str] = None) -> List[Kbar]:
    """
    Load kbar data from database using DatabaseManager
    
    Args:
        symbol: Stock symbol
        exchange: Exchange code
        period: Time period
        limit: Maximum number of kbars to load
        start_time: Start time for data range (format: "YYYY-MM-DD HH:MM:SS")
        end_time: End time for data range (format: "YYYY-MM-DD HH:MM:SS")
        
    Returns:
        List of Kbar objects loaded from database
    """
    if not DATABASE_AVAILABLE:
        print("Database not available, falling back to synthetic data")
        return create_sample_kbars(limit)
    
    try:
        # Create database manager with SQLite configuration
        db_manager = db_manager_factory()
        if db_manager is None:
            print("Failed to create database manager, falling back to synthetic data")
            return create_sample_kbars(limit)
        
        # Check if database is available
        stats = db_manager.get_database_stats()
        if not stats['kbar_db_available']:
            print("K-bar database not available, falling back to synthetic data")
            db_manager.close()
            return create_sample_kbars(limit)
        
        # Get kbar data from database
        time_range_info = ""
        if start_time or end_time:
            time_range_info = f" (time range: {start_time or 'unlimited'} to {end_time or 'unlimited'})"
        
        print(f"Loading kbar data for {symbol}.{exchange} ({period}) from database{time_range_info}...")
        
        # Convert string datetime parameters to datetime objects if provided
        start_datetime = None
        end_datetime = None
        
        if start_time:
            try:
                start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"Warning: Invalid start_time format '{start_time}', expected 'YYYY-MM-DD HH:MM:SS'")
        
        if end_time:
            try:
                end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"Warning: Invalid end_time format '{end_time}', expected 'YYYY-MM-DD HH:MM:SS'")
        
        df = db_manager.get_kbar_data(
            symbol=symbol,
            exchange=exchange,
            period=period,
            limit=limit,
            start_time=start_datetime,
            end_time=end_datetime
        )
        
        if df.empty:
            print(f"No data found for {symbol}.{exchange}, falling back to synthetic data")
            db_manager.close()
            return create_sample_kbars(limit)
        
        # Convert DataFrame to Kbar objects
        kbars = []
        for _, row in df.iterrows():
            # Use 'ts' column name as returned by database
            timestamp_col = 'ts' if 'ts' in row else 'timestamp'
            kbar = Kbar(
                timestamp=str(row[timestamp_col]),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume'])
            )
            kbars.append(kbar)
        
        print(f"Loaded {len(kbars)} kbars from database")
        db_manager.close()
        return kbars
        
    except Exception as e:
        print(f"Error loading data from database: {e}")
        print("Falling back to synthetic data")
        return create_sample_kbars(limit)


def get_available_symbols() -> List[dict]:
    """
    Get list of available symbols from database
    
    Returns:
        List of symbol dictionaries with symbol, exchange, period info
    """
    if not DATABASE_AVAILABLE:
        return [{'symbol': '000001', 'exchange': 'SH', 'period': '1min'}]
    
    try:
        db_manager = db_manager_factory()
        if db_manager is None:
            return [{'symbol': '000001', 'exchange': 'SH', 'period': '1min'}]
            
        symbols = db_manager.get_symbols_with_data()
        db_manager.close()
        return symbols if symbols else [{'symbol': '000001', 'exchange': 'SH', 'period': '1min'}]
    except Exception as e:
        print(f"Error getting symbols from database: {e}")
        return [{'symbol': '000001', 'exchange': 'SH', 'period': '1min'}]


def create_sample_kbars(count: int = 50) -> List[Kbar]:
    """
    Create sample kbar data for demonstration (fallback when database not available)
    
    Args:
        count: Number of kbars to create
        
    Returns:
        List of sample kbars with simulated price movement
    """
    import random
    kbars = []
    base_price = 100.0
    current_price = base_price
    
    for i in range(count):
        # Simulate price movement with some volatility
        if i % 7 == 0:  # Create some trend changes
            direction = 1 if i % 14 == 0 else -1
        else:
            direction = 1 if current_price < base_price + 5 else -1
        
        # Random price movement
        price_change = random.uniform(-0.5, 0.5) + direction * 0.1
        current_price += price_change
        
        # Ensure positive prices
        current_price = max(current_price, 50.0)
        
        # Create valid OHLC data
        open_price = current_price + random.uniform(-0.2, 0.2)
        close_price = current_price + random.uniform(-0.3, 0.3)
        
        # Ensure high is at least the maximum of open and close
        high = max(open_price, close_price) + random.uniform(0, 0.3)
        
        # Ensure low is at most the minimum of open and close
        low = min(open_price, close_price) - random.uniform(0, 0.3)
        
        # Ensure all prices are positive
        low = max(low, 10.0)
        
        timestamp = (datetime.now() + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S")
        
        kbar = Kbar(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=1000 + random.randint(0, 500)
        )
        
        kbars.append(kbar)
    
    return kbars


def configure_logging_parameters(log_level: str = "INFO", log_dir: str = "logs", 
                                file_prefix: str = "chan", include_timestamp: bool = True,
                                overwrite_log: bool = True):
    """
    Configure logging parameters globally
    
    Args:
        log_level: Logging level ("DEBUG", "INFO", "WARNING", "ERROR")
        log_dir: Directory for log files (relative to current directory)
        file_prefix: Prefix for log file names
        include_timestamp: Whether to include timestamp in log filenames
        overwrite_log: Whether to overwrite existing log files (True) or append to them (False)
    """
    global LOGGING_CONFIG
    
    # Convert string level to logging constant
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    numeric_level = level_mapping.get(log_level.upper(), logging.INFO)
    
    # Create timestamp suffix if requested
    timestamp_suffix = ""
    if include_timestamp:
        timestamp_suffix = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    LOGGING_CONFIG = {
        'level': numeric_level,
        'log_dir': log_dir,
        'file_prefix': file_prefix,
        'timestamp_suffix': timestamp_suffix,
        'overwrite_log': overwrite_log
    }
    
    overwrite_desc = "overwrite" if overwrite_log else "append"
    print(f"Logging configured: Level={log_level.upper()}, Dir={log_dir}, "
          f"Prefix={file_prefix}, Timestamp={include_timestamp}, Mode={overwrite_desc}")


def setup_logging(log_file: str = "chan_analysis.log", log_level: int = logging.DEBUG, overwrite_log: bool = True):
    """
    Setup logging to both console and file
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        overwrite_log: If True, overwrite existing log file; if False, append to it
    """
    # Use global config if available
    if 'LOGGING_CONFIG' in globals():
        config = LOGGING_CONFIG
        log_level = config['level']
        log_dir = os.path.join(current_dir, config['log_dir'])
        
        # Create filename with prefix and timestamp
        base_name = log_file.replace('.log', '')
        log_file = f"{config['file_prefix']}_{base_name}{config['timestamp_suffix']}.log"
    else:
        # Default log directory
        log_dir = os.path.join(current_dir, 'logs')
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Full path to log file
    log_file_path = os.path.join(log_dir, log_file)
    
    # Clear existing handlers
    logging.getLogger().handlers.clear()
    
    # Create formatters - simplified file format to match console format
    # Detailed formatter (commented out - uncomment to restore detailed logging):
    # detailed_formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    # )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Create file handler with configurable mode (overwrite or append)
    file_mode = 'w' if overwrite_log else 'a'
    # To restore detailed file logging, uncomment the next line and comment the one after:
    # file_handler.setFormatter(detailed_formatter)
    file_handler = logging.FileHandler(log_file_path, mode=file_mode, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(simple_formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log the setup
    mode_desc = "overwrite" if overwrite_log else "append"
    logger.info(f"Logging setup complete - File: {log_file_path}, Level: {logging.getLevelName(log_level)}, Mode: {mode_desc}")
    
    return log_file_path


def demonstrate_step_by_step_processing():
    """Demonstrate step-by-step Chan algorithm processing"""
    print("\n=== Step-by-Step Chan Algorithm Processing ===")
    
    # Setup logging to both console and file
    log_file_path = setup_logging("chan_step_by_step.log", logging.DEBUG)
    print(f"Logging to file: {log_file_path}")
    
    # Use shared configuration variables
    symbol = DEFAULT_SYMBOL
    exchange = DEFAULT_EXCHANGE
    period = DEFAULT_PERIOD
    limit = DEFAULT_LIMIT
    start_time = DEFAULT_START_TIME
    end_time = DEFAULT_END_TIME
    
    print(f"Processing {symbol}.{exchange} ({period}) with limit={limit}")
    if start_time or end_time:
        print(f"Time range: {start_time or 'unlimited'} to {end_time or 'unlimited'}")
    
    # Initialize processor with auto-loading to avoid duplicate data loading
    print("\nInitializing Chan processor with auto-loading...")
    processor = ChanProcessor(
        strict_fractal_mode=True,
        min_pen_length=0.5,
        min_kbar_count=3,
        min_line_pens=3,
        symbol=symbol,
        exchange=exchange, 
        period=period,
        start_time=start_time,
        end_time=end_time,
        auto_load_data=True,  # Auto-load to avoid duplicate loading
        auto_clear_chan_db=True,
        kbar_limit=limit
    )
    
    # Process kbars through the complete pipeline using auto-loaded data
    print("\nProcessing K-bars through Chan algorithm pipeline...")
    results = processor.process_kbars_auto()
    
    # Process a single new kbar incrementally
    print("\nProcessing a single new K-bar incrementally...")
    # Create a simulated new K-bar for incremental processing
    # Get the last raw kbar from the processor
    last_raw_kbar = processor.get_current_rawkbar()
    
    if last_raw_kbar:
        # Create a simulated new kbar by copying the last one and updating timestamp and close
        from datetime import datetime, timedelta
        import random
        
        # Parse the timestamp string to datetime object
        # Assuming timestamp format is "YYYY-MM-DD HH:MM:SS"
        try:
            last_timestamp = datetime.strptime(last_raw_kbar.timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Try alternative format without seconds
            try:
                last_timestamp = datetime.strptime(last_raw_kbar.timestamp, "%Y-%m-%d %H:%M")
            except ValueError:
                # Try ISO format
                try:
                    last_timestamp = datetime.fromisoformat(last_raw_kbar.timestamp.replace('T', ' '))
                except ValueError:
                    # If all parsing fails, just use current time
                    print(f"Warning: Could not parse timestamp '{last_raw_kbar.timestamp}', using current time")
                    last_timestamp = datetime.now()
        
        # Update timestamp to next period (assuming 1-minute periods)
        new_timestamp = last_timestamp + timedelta(days=1)
        new_timestamp_str = new_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Simulate a new close price (small random change)
        price_change = random.uniform(-0.5, 0.5)  # Random change between -0.5 and +0.5
        new_close = last_raw_kbar.close + price_change
        
        # Create new kbar with updated timestamp and close, keeping other values from last kbar
        new_kbar = Kbar(
            timestamp=new_timestamp_str,
            open=last_raw_kbar.open,
            high=last_raw_kbar.high,
            low=last_raw_kbar.low,
            close=new_close,
            volume=last_raw_kbar.volume
        )
        
        print(f"Created simulated K-bar: {new_kbar.timestamp} - O:{new_kbar.open:.2f} H:{new_kbar.high:.2f} L:{new_kbar.low:.2f} C:{new_kbar.close:.2f} V:{new_kbar.volume}")
        
        # Process the new K-bar incrementally
        incremental_results = processor.process_new_kbar(new_kbar)
        
        print(f"Incremental processing status: {incremental_results['status']}")
        print(f"Changes made: {incremental_results.get('changes_made', False)}")
        
        # Show what changed in the incremental processing
        if 'incremental_processing' in incremental_results:
            steps = incremental_results['incremental_processing']
            print("\nIncremental Processing Changes:")
            
            for step_name, step_data in steps.items():
                if step_name == 'step1_merge':
                    print(f"  {step_name}: {step_data.get('action', 'unknown')} - {step_data.get('merged_kbar_count', 0)} merged K-bars")
                elif step_name == 'step2_fractals':
                    print(f"  {step_name}: {step_data.get('new_fractals', 0)} new fractals (total: {step_data.get('total_fractals', 0)})")
                elif step_name == 'step3_pens':
                    print(f"  {step_name}: {step_data.get('new_pens', 0)} new pens (total: {step_data.get('total_pens', 0)})")
                elif step_name == 'step4_lines':
                    print(f"  {step_name}: {step_data.get('new_lines', 0)} new lines (total: {step_data.get('total_lines', 0)})")
                elif step_name == 'line_breaking':
                    print(f"  Line breaking detected: {len(step_data)} instances")
                    for break_info in step_data:
                        print(f"    - {break_info['line_direction']} line: {break_info['break_type']} at price {break_info['current_price']:.2f}")
    else:
        print("No raw K-bar data available for incremental processing simulation")
    
    # Display results
    print(f"\nProcessing Status: {results['status']}")
    # print(f"Summary: {results['summary']}")
    
    # # Show step-by-step results
    # if 'processing_steps' in results:
    #     steps = results['processing_steps']
        
    #     if 'step1_merge' in steps:
    #         merge_info = steps['step1_merge']
    #         print(f"\nStep 1 - Kbar Merging:")
    #         print(f"  Original kbars: {merge_info['original_kbars']}")
    #         print(f"  Merged kbars: {merge_info['merged_kbars']}")
    #         print(f"  Compression ratio: {merge_info['compression_ratio']:.2f}")
        
    #     if 'step2_fractals' in steps:
    #         fractal_info = steps['step2_fractals']
    #         print(f"\nStep 2 - Fractal Identification:")
    #         print(f"  Total fractals: {fractal_info['total_fractals']}")
    #         print(f"  Top fractals: {fractal_info['top_fractals']}")
    #         print(f"  Bottom fractals: {fractal_info['bottom_fractals']}")
        
    #     if 'step3_pens' in steps:
    #         pen_info = steps['step3_pens']
    #         print(f"\nStep 3 - Pen Formation:")
    #         print(f"  Total pens: {pen_info['total_pens']}")
    #         print(f"  Upward pens: {pen_info['upward_pens']}")
    #         print(f"  Downward pens: {pen_info['downward_pens']}")
        
    #     if 'step4_lines' in steps:
    #         line_info = steps['step4_lines']
    #         print(f"\nStep 4 - Line Formation:")
    #         print(f"  Total lines: {line_info['total_lines']}")
    #         print(f"  Upward lines: {line_info['upward_lines']}")
    #         print(f"  Downward lines: {line_info['downward_lines']}")
    #         print(f"  Broken lines: {line_info['broken_lines']}")
            
    #         if line_info['global_line_info']['exists']:
    #             global_info = line_info['global_line_info']
    #             print(f"  Global line: {global_info['direction']} ({global_info['status']})")
    
    # # Show latest structures
    # if 'latest_structures' in results:
    #     structures = results['latest_structures']
    #     print(f"\nLatest Structures:")
        
    #     if structures['latest_fractal']:
    #         fractal = structures['latest_fractal']
    #         print(f"  Latest Fractal: {fractal['type']} at {fractal['price']:.2f} "
    #               f"(strength: {fractal['strength']:.4f})")
        
    #     if structures['latest_pen']:
    #         pen = structures['latest_pen']
    #         print(f"  Latest Pen: {pen['direction']} length {pen['length']:.2f} "
    #               f"({pen['kbar_count']} kbars)")
        
    #     if structures['latest_line']:
    #         line = structures['latest_line']
    #         print(f"  Latest Line: {line['direction']} with {line['pen_count']} pens "
    #               f"({line['status']})")
    
    # Close processor
    processor.close()


def demonstrate_individual_components():
    """Demonstrate individual component usage"""
    print("\n=== Individual Component Usage ===")
    
    # Setup logging for individual components
    log_file_path = setup_logging("chan_components.log", logging.INFO)
    print(f"Logging to file: {log_file_path}")
    
    # Import individual components with fallback handling
    try:
        from .mergekbar import KbarMerger
        from .fractal import FractalIdentifier
        from .pen import PenProcessor
        from .line import LineProcessor
    except ImportError:
        from QAutils.ChanPy.mergekbar import KbarMerger
        from QAutils.ChanPy.fractal import FractalIdentifier
        from QAutils.ChanPy.pen import PenProcessor
        from QAutils.ChanPy.line import LineProcessor
    
    # Use shared configuration variables (with smaller limit for component demo)
    symbol = DEFAULT_SYMBOL
    exchange = DEFAULT_EXCHANGE
    period = DEFAULT_PERIOD
    limit = 20  # Smaller limit for component demo
    start_time = DEFAULT_START_TIME
    end_time = DEFAULT_END_TIME
    
    # Load data from database or use synthetic data
    kbars = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=limit, start_time=start_time, end_time=end_time)
    
    # Step 1: Kbar Merging
    print("\n1. Kbar Merging:")
    merger = KbarMerger()
    merged_kbars = merger.process_kbar_sequence(kbars)
    print(f"   Merged {len(kbars)} kbars into {len(merged_kbars)} merged kbars")
    
    # Step 2: Fractal Identification
    print("\n2. Fractal Identification:")
    fractal_id = FractalIdentifier(strict_mode=True)
    fractals = fractal_id.process_merged_kbars(merged_kbars)
    print(f"   Identified {len(fractals)} fractals")
    print(f"   Fractal summary: {fractal_id.get_fractal_summary()}")
    
    # Step 3: Pen Processing
    print("\n3. Pen Processing:")
    pen_proc = PenProcessor(min_pen_length=0.3, min_kbar_count=3)
    pen_proc.set_raw_kbars(kbars)
    pens = pen_proc.process_fractals(fractals)
    print(f"   Created {len(pens)} pens")
    print(f"   Pen statistics: {pen_proc.get_pen_statistics()}")
    
    # Step 4: Line Processing  
    if len(pens) >= 3:
        print("\n4. Line Processing:")
        line_proc = LineProcessor(min_line_pens=3)
        lines = line_proc.process_pens(pens)
        print(f"   Created {len(lines)} lines")
        print(f"   Line statistics: {line_proc.get_line_statistics()}")
        
        global_line = line_proc.get_global_line()
        if global_line:
            print(f"   Global line: {global_line.direction.name} "
                  f"({global_line.status.name})")


def demonstrate_market_analysis():
    """Demonstrate real-time market analysis"""
    print("\n=== Market Analysis Demo ===")
    
    # Setup logging for market analysis
    log_file_path = setup_logging("chan_market_analysis.log", logging.INFO)
    print(f"Logging to file: {log_file_path}")
    
    # Use shared configuration variables
    symbol = DEFAULT_SYMBOL
    exchange = DEFAULT_EXCHANGE
    period = DEFAULT_PERIOD
    limit = 25  # Smaller limit for market analysis demo
    start_time = DEFAULT_START_TIME
    end_time = DEFAULT_END_TIME
    
    # Create processor
    processor = ChanProcessor(
        symbol=symbol,
        exchange=exchange,
        period=period,
        start_time=start_time,
        end_time=end_time
    )
    
    # Load data from database or use synthetic data
    kbars = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=limit, start_time=start_time, end_time=end_time)
    results = processor.process_kbars(kbars)
    
    if results['status'] == 'Success':
        # Get price range from loaded data for realistic test prices
        prices = [kbar.close for kbar in kbars]
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        
        # Analyze current market state with different prices
        test_prices = [
            min_price - price_range * 0.1,  # Below range
            min_price + price_range * 0.3,  # Lower range
            max_price - price_range * 0.3,  # Upper range
            max_price + price_range * 0.1   # Above range
        ]
        
        for price in test_prices:
            print(f"\nAnalyzing market at price {price:.2f}:")
            analysis = processor.analyze_current_market_state(price)
            
            print(f"  Current price: {analysis['current_price']}")
            
            if analysis['latest_fractal']:
                fractal = analysis['latest_fractal']
                print(f"  Latest fractal: {fractal['type']} at {fractal['price']:.2f}")
            
            if analysis['latest_pen']:
                pen = analysis['latest_pen']
                print(f"  Latest pen: {pen['direction']} "
                      f"({pen['start_price']:.2f} -> {pen['end_price']:.2f})")
            
            if 'pen_breaking' in analysis['breaking_analysis']:
                breaking = analysis['breaking_analysis']['pen_breaking']
                print(f"  Pen breaking status: {breaking}")
            
            if analysis['global_line']:
                global_line = analysis['global_line']
                print(f"  Global line: {global_line['direction']} "
                      f"({'BROKEN' if global_line['broken'] else 'ACTIVE'})")


def demonstrate_multiple_symbols():
    """Demonstrate analysis with multiple symbols from database"""
    print("\n=== Multiple Symbols Analysis ===")
    
    # Setup logging for multiple symbols analysis
    log_file_path = setup_logging("chan_multiple_symbols.log", logging.INFO)
    print(f"Logging to file: {log_file_path}")
    
    # Get available symbols from database
    available_symbols = get_available_symbols()
    print(f"Available symbols: {len(available_symbols)}")
    
    # Analyze up to 3 symbols
    for i, symbol_info in enumerate(available_symbols[:3]):
        symbol = symbol_info['symbol']
        exchange = symbol_info['exchange']
        period = symbol_info.get('period', '1min')
        
        print(f"\n--- Analyzing {symbol}.{exchange} ({period}) ---")
        
        # Load data for this symbol
        kbars = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=20, start_time=DEFAULT_START_TIME, end_time=DEFAULT_END_TIME)
        
        if not kbars:
            print(f"No data available for {symbol}.{exchange}")
            continue
        
        # Create processor and analyze
        processor = ChanProcessor(
            symbol=symbol,
            exchange=exchange,
            period=period,
            start_time=DEFAULT_START_TIME,
            end_time=DEFAULT_END_TIME
        )
        results = processor.process_kbars(kbars)
        
        if results['status'] == 'Success':
            summary = results['summary']
            print(f"  Data: {summary['raw_kbars']} kbars -> {summary['merged_kbars']} merged")
            print(f"  Structures: {summary['fractals']} fractals, {summary['pens']} pens, {summary['lines']} lines")
            print(f"  Global line active: {summary['global_line_active']}")
        else:
            print(f"  Analysis failed: {results['status']}")


def demonstrate_time_range_filtering():
    """Demonstrate how to use time range filtering for kbar data"""
    print("\n=== Time Range Filtering Demo ===")
    
    # Setup logging for time range demo
    log_file_path = setup_logging("chan_time_range.log", logging.INFO)
    print(f"Logging to file: {log_file_path}")
    
    # Example 1: Configure time range using global parameters
    print("\n1. Using global configuration:")
    configure_analysis_parameters(
        symbol="000001",
        exchange="SH",
        period="1min",
        limit=100,
        start_time="2023-01-01 09:30:00",
        end_time="2023-01-01 15:00:00"
    )
    
    # Load data using global configuration
    config = get_current_configuration()
    print(f"Current configuration: {config}")
    
    kbars = load_kbar_data_from_database(
        symbol=config['symbol'],
        exchange=config['exchange'],
        period=config['period'],
        limit=config['limit'],
        start_time=config['start_time'],
        end_time=config['end_time']
    )
    print(f"Loaded {len(kbars)} kbars for the specified time range")
    
    # Example 2: Direct function call with time range
    print("\n2. Direct function call with time range:")
    kbars2 = load_kbar_data_from_database(
        symbol="002120",
        exchange="SZ",
        period="5min",
        limit=50,
        start_time="2023-06-01 10:00:00",
        end_time="2023-06-01 14:30:00"
    )
    print(f"Loaded {len(kbars2)} kbars for direct time range query")
    
    # Example 3: Open-ended time range (only start time)
    print("\n3. Open-ended time range (only start time):")
    kbars3 = load_kbar_data_from_database(
        symbol="000001",
        exchange="SH",
        period="daily",
        limit=30,
        start_time="2023-01-01 00:00:00",
        end_time=None
    )
    print(f"Loaded {len(kbars3)} kbars from start time onwards")
    
    # Example 4: No time range (use limit only)
    print("\n4. No time range (use limit only):")
    kbars4 = load_kbar_data_from_database(
        symbol="000001",
        exchange="SH",
        period="1min",
        limit=20,
        start_time=None,
        end_time=None
    )
    print(f"Loaded {len(kbars4)} kbars using limit only")
    
    # Example 5: Using time range with ChanProcessor
    print("\n5. Using time range with ChanProcessor:")
    processor = ChanProcessor(
        symbol="000001",
        exchange="SH",
        period="1min",
        start_time="2023-01-01 09:30:00",
        end_time="2023-01-01 15:00:00"
    )
    
    # Get time range from processor
    time_range = processor.get_time_range()
    print(f"Processor time range: {time_range}")
    
    # Process kbars with time range context
    results = processor.process_kbars(kbars)
    print(f"Processed {len(kbars)} kbars with ChanProcessor (time range: {time_range['start_time']} to {time_range['end_time']})")
    
    # Example 6: Update time range dynamically
    print("\n6. Update time range dynamically:")
    processor.set_time_range(
        start_time="2023-06-01 10:00:00",
        end_time="2023-06-01 16:00:00"
    )
    updated_range = processor.get_time_range()
    print(f"Updated processor time range: {updated_range}")


def demonstrate_improved_processing():
    """Demonstrate the improved Chan processing without duplicate data loading"""
    print("\n=== Improved Chan Processing (No Duplicate Loading) ===")
    
    # Setup logging
    log_file_path = setup_logging("chan_improved.log", logging.DEBUG)
    print(f"Logging to file: {log_file_path}")
    
    # Use shared configuration variables
    symbol = DEFAULT_SYMBOL
    exchange = DEFAULT_EXCHANGE
    period = DEFAULT_PERIOD
    limit = DEFAULT_LIMIT
    start_time = DEFAULT_START_TIME
    end_time = DEFAULT_END_TIME
    
    print(f"Processing {symbol}.{exchange} ({period}) with limit={limit}")
    if start_time or end_time:
        print(f"Time range: {start_time or 'unlimited'} to {end_time or 'unlimited'}")
    
    # Method 1: Auto-loading (recommended approach)
    print("\n--- Method 1: Auto-loading from Database ---")
    processor = ChanProcessor(
        strict_fractal_mode=True,
        min_pen_length=0.5,
        min_kbar_count=3,
        min_line_pens=3,
        symbol=symbol,
        exchange=exchange, 
        period=period,
        start_time=start_time,
        end_time=end_time,
        auto_load_data=True,  # This will load data automatically
        kbar_limit=limit
    )
    
    # Process data that was automatically loaded
    results = processor.process_kbars_auto()
    print(f"Auto-processing Status: {results['status']}")
    if results['status'] == 'Success':
        summary = results['summary']
        print(f"  Data: {summary['raw_kbars']} kbars -> {summary['merged_kbars']} merged")
        print(f"  Structures: {summary['fractals']} fractals, {summary['pens']} pens, {summary['lines']} lines")
    
    # Method 2: Manual data loading (for when you need custom data)
    print("\n--- Method 2: Manual Data Loading ---")
    processor2 = ChanProcessor(
        strict_fractal_mode=True,
        min_pen_length=0.5,
        min_kbar_count=3,
        min_line_pens=3,
        symbol=symbol,
        exchange=exchange, 
        period=period,
        start_time=start_time,
        end_time=end_time,
        auto_load_data=False,  # Don't auto-load, we'll provide data manually
        kbar_limit=limit
    )
    
    # Load data manually when you need custom logic
    print("Loading K-bar data manually...")
    kbars = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=limit, start_time=start_time, end_time=end_time)
    print(f"Loaded {len(kbars)} K-bars manually")
    
    # Process manually loaded data
    results2 = processor2.process_kbars(kbars)
    print(f"Manual processing Status: {results2['status']}")
    if results2['status'] == 'Success':
        summary2 = results2['summary']
        print(f"  Data: {summary2['raw_kbars']} kbars -> {summary2['merged_kbars']} merged")
        print(f"  Structures: {summary2['fractals']} fractals, {summary2['pens']} pens, {summary2['lines']} lines")
    
    # Method 3: Using existing data from context
    print("\n--- Method 3: Using Context Data ---")
    if processor.context and all([symbol, exchange, period]):
        context_kbars = processor.load_kbars_from_context(limit=50)
        print(f"Loaded {len(context_kbars)} K-bars from context")
        
        # Process context data
        results3 = processor.process_kbars(context_kbars)
        print(f"Context processing Status: {results3['status']}")
    
    # Close processors
    processor.close()
    processor2.close()
    
    print("\n--- Benefits of Improved Approach ---")
    print("✓ No duplicate data loading")
    print("✓ Consistent data across all components")
    print("✓ Configurable auto-loading vs manual loading")
    print("✓ Proper resource management with context")
    print("✓ Better performance and reduced database queries")


def demonstrate_loading_comparison():
    """Compare the old (duplicate loading) vs new (efficient loading) approaches"""
    print("\n=== Loading Approach Comparison ===")
    
    # Setup logging
    log_file_path = setup_logging("chan_comparison.log", logging.DEBUG)
    print(f"Logging to file: {log_file_path}")
    
    # Use shared configuration variables
    symbol = DEFAULT_SYMBOL
    exchange = DEFAULT_EXCHANGE
    period = DEFAULT_PERIOD
    limit = 50  # Smaller limit for comparison demo
    start_time = DEFAULT_START_TIME
    end_time = DEFAULT_END_TIME
    
    print(f"\nComparing loading approaches for {symbol}.{exchange} ({period}) with limit={limit}")
    
    # === OLD APPROACH (Duplicate Loading) ===
    print("\n--- OLD APPROACH (Duplicate Loading) ---")
    print("❌ This approach loads data twice:")
    print("   1. Context initialization loads data from database")
    print("   2. Manual loading loads data again")
    print("   3. process_kbars() updates context with manually loaded data")
    
    # Simulate old approach (but with auto_load_data=False to avoid actual duplication)
    print("\nStep 1: Manual data loading...")
    kbars_manual = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=limit, start_time=start_time, end_time=end_time)
    print(f"   Loaded {len(kbars_manual)} K-bars manually")
    
    print("\nStep 2: Creating processor with context initialization...")
    processor_old = ChanProcessor(
        strict_fractal_mode=True,
        min_pen_length=0.5,
        min_kbar_count=3,
        min_line_pens=3,
        symbol=symbol,
        exchange=exchange, 
        period=period,
        start_time=start_time,
        end_time=end_time,
        auto_load_data=False,  # Disable to simulate old approach
        kbar_limit=limit
    )
    print("   Context initialized (would load data if auto_load_data=True)")
    
    print("\nStep 3: Processing manually loaded data...")
    results_old = processor_old.process_kbars(kbars_manual)
    print(f"   Processing status: {results_old['status']}")
    if results_old['status'] == 'Success':
        print(f"   Result: {results_old['summary']['raw_kbars']} K-bars processed")
    
    # === NEW APPROACH (Efficient Loading) ===
    print("\n--- NEW APPROACH (Efficient Loading) ---")
    print("✅ This approach loads data once:")
    print("   1. Context initialization loads data from database")
    print("   2. process_kbars_auto() uses the already loaded data")
    print("   3. No duplicate loading or context updates")
    
    print("\nStep 1: Creating processor with auto-loading...")
    processor_new = ChanProcessor(
        strict_fractal_mode=True,
        min_pen_length=0.5,
        min_kbar_count=3,
        min_line_pens=3,
        symbol=symbol,
        exchange=exchange, 
        period=period,
        start_time=start_time,
        end_time=end_time,
        auto_load_data=True,  # Auto-load data during initialization
        kbar_limit=limit
    )
    print("   Processor initialized with auto-loaded data")
    
    print("\nStep 2: Processing auto-loaded data...")
    results_new = processor_new.process_kbars_auto()
    print(f"   Processing status: {results_new['status']}")
    if results_new['status'] == 'Success':
        print(f"   Result: {results_new['summary']['raw_kbars']} K-bars processed")
    
    # === COMPARISON SUMMARY ===
    print("\n--- COMPARISON SUMMARY ---")
    print("Old Approach Issues:")
    print("  ❌ Duplicate database queries")
    print("  ❌ Potential data inconsistency")
    print("  ❌ Slower performance")
    print("  ❌ More memory usage")
    print("  ❌ Complex initialization flow")
    
    print("\nNew Approach Benefits:")
    print("  ✅ Single database query")
    print("  ✅ Consistent data throughout")
    print("  ✅ Better performance")
    print("  ✅ Lower memory usage")
    print("  ✅ Simpler initialization")
    print("  ✅ Configurable loading behavior")
    
    # Clean up
    processor_old.close()
    processor_new.close()


def demonstrate_simple_usage():
    """Simple usage example for new users"""
    print("\n=== Simple Usage Example ===")
    
    # Setup logging
    log_file_path = setup_logging("chan_simple.log", logging.INFO)
    print(f"Logging to file: {log_file_path}")
    
    print("\nSimple Chan Analysis in 3 lines of code:")
    print("```python")
    print("# 1. Create processor with auto-loading")
    print("processor = ChanProcessor(symbol='002120', exchange='SZ', period='daily')")
    print("")
    print("# 2. Process data")
    print("results = processor.process_kbars_auto()")
    print("")
    print("# 3. Use results")
    print("print(f'Status: {results[\"status\"]}')") 
    print("```")
    
    # Demonstrate the actual usage
    print("\nActual demonstration:")
    try:
        # 1. Create processor with auto-loading
        processor = ChanProcessor(
            symbol=DEFAULT_SYMBOL, 
            exchange=DEFAULT_EXCHANGE, 
            period=DEFAULT_PERIOD,
            kbar_limit=50
        )
        
        # 2. Process data  
        results = processor.process_kbars_auto()
        
        # 3. Use results
        print(f"Status: {results['status']}")
        if results['status'] == 'Success':
            summary = results['summary']
            print(f"Processed {summary['raw_kbars']} K-bars -> {summary['merged_kbars']} merged K-bars")
            print(f"Found {summary['fractals']} fractals, {summary['pens']} pens, {summary['lines']} lines")
        
        # Clean up
        processor.close()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nFor advanced usage, you can:")
    print("- Set custom parameters (time ranges, limits, thresholds)")
    print("- Use manual data loading for custom data sources")
    print("- Access individual analysis components")
    print("- Perform incremental updates with new data")


def main():
    """Main demonstration function"""
    print("Chan Algorithm Modular Implementation Demo")
    print("==========================================")
    
    # Example: Configure logging parameters (optional)
    # Uncomment and modify as needed:
    # configure_logging_parameters(
    #     log_level="DEBUG",      # Options: DEBUG, INFO, WARNING, ERROR
    #     log_dir="custom_logs",  # Custom log directory
    #     file_prefix="trading",  # Custom prefix for log files
    #     include_timestamp=True  # Include timestamp in filename
    # )
    
    # Setup main logging (will use global config if set above)
    log_file_path = setup_logging("chan_main.log", logging.INFO)
    print(f"Main logging to file: {log_file_path}")
    
    # Show database status
    if DATABASE_AVAILABLE:
        print("✓ Database module available - will use real data when possible")
    else:
        print("⚠ Database module not available - using synthetic data only")
    
    try:
        # Start with simple usage example for new users
        # demonstrate_simple_usage()
        
        # # Show the improvement in data loading
        # demonstrate_loading_comparison()
        
        # # Show the complete improved processing workflow
        # demonstrate_improved_processing()
        
        # # Show detailed step-by-step processing
        demonstrate_step_by_step_processing()
        
        # Additional demonstrations (commented out to focus on the main improvements)
        # demonstrate_individual_components()
        # demonstrate_market_analysis()
        # demonstrate_time_range_filtering()
        
        # # Only run multiple symbols demo if database is available
        # if DATABASE_AVAILABLE:
        #     demonstrate_multiple_symbols()
        
        print("\n" + "="*50)
        print("SUMMARY OF IMPROVEMENTS")
        print("="*50)
        
        print("\n🎯 KEY IMPROVEMENT: Eliminated Duplicate Data Loading")
        print("   • Before: Data loaded twice (context + manual loading)")
        print("   • After: Single efficient loading with configurable options")
        
        print("\n📈 PERFORMANCE BENEFITS:")
        print("   ✅ Reduced database queries by 50%")
        print("   ✅ Lower memory usage")
        print("   ✅ Faster initialization")
        print("   ✅ Consistent data across all components")
        
        print("\n🔧 API IMPROVEMENTS:")
        print("   ✅ Simple 3-line usage for beginners")
        print("   ✅ Auto-loading vs manual loading options")
        print("   ✅ Better resource management")
        print("   ✅ Configurable K-bar limits and time ranges")
        
        print("\n📊 RELIABILITY IMPROVEMENTS:")
        print("   ✅ No more data consistency issues")
        print("   ✅ Proper context management")
        print("   ✅ Automatic cleanup with context managers")
        
        if DATABASE_AVAILABLE:
            print("\n💾 DATABASE INTEGRATION:")
            print("   ✅ Efficient real market data loading")
            print("   ✅ Configurable time range filtering")
            print("   ✅ Automatic data persistence")
        
        print("\n🚀 RECOMMENDED USAGE:")
        print("   • Use ChanProcessor with auto_load_data=True for most cases")
        print("   • Use manual loading only for custom data sources")
        print("   • Always call processor.close() or use context managers")
        print("   • Configure time ranges and limits as needed")
        
        print(f"\n📁 Log files created in: {os.path.dirname(log_file_path)}")
        print("   Check the log files for detailed execution traces")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 