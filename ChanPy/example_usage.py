"""
Example Usage of Modular Chan Algorithm

This example demonstrates how to use the new modular Chan algorithm implementation
that follows the specified four-step process:

1. Merge kbar process for consecutive kbars
2. Check consecutive merged kbars for fractals
3. Process raw kbars from fractal to fractal to identify chanpen
4. Process chanpen breaking and chanline formation

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
- chan_step_by_step.log: Detailed step-by-step processing logs
- chan_components.log: Individual component usage logs
- chan_market_analysis.log: Market analysis logs
- chan_multiple_symbols.log: Multiple symbol analysis logs
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
    # Absolute path to the database
    db_path = os.path.join(parent_dir, 'Server', 'tdx_db', 'stock_kbar.db')
    meta_db_path = os.path.join(parent_dir, 'Server', 'tdx_db', 'stock_meta.db')
    
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
DEFAULT_LIMIT = 20


def configure_analysis_parameters(symbol: Optional[str] = None, exchange: Optional[str] = None, 
                                period: Optional[str] = None, limit: Optional[int] = None):
    """
    Configure the default analysis parameters
    
    Args:
        symbol: Stock symbol (e.g., "002120", "000001")
        exchange: Exchange code (e.g., "SZ", "SH")
        period: Time period (e.g., "daily", "1min", "5min")
        limit: Maximum number of kbars to load
    """
    global DEFAULT_SYMBOL, DEFAULT_EXCHANGE, DEFAULT_PERIOD, DEFAULT_LIMIT
    
    if symbol is not None:
        DEFAULT_SYMBOL = symbol
    if exchange is not None:
        DEFAULT_EXCHANGE = exchange
    if period is not None:
        DEFAULT_PERIOD = period
    if limit is not None:
        DEFAULT_LIMIT = limit
    
    print(f"Analysis parameters configured: {DEFAULT_SYMBOL}.{DEFAULT_EXCHANGE} ({DEFAULT_PERIOD}), limit={DEFAULT_LIMIT}")


def get_current_configuration() -> dict:
    """Get the current configuration parameters"""
    return {
        'symbol': DEFAULT_SYMBOL,
        'exchange': DEFAULT_EXCHANGE,
        'period': DEFAULT_PERIOD,
        'limit': DEFAULT_LIMIT
    }

def load_kbar_data_from_database(symbol: str = "000001", exchange: str = "SH", 
                                period: str = "1min", limit: int = 50) -> List[Kbar]:
    """
    Load kbar data from database using DatabaseManager
    
    Args:
        symbol: Stock symbol
        exchange: Exchange code
        period: Time period
        limit: Maximum number of kbars to load
        
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
        print(f"Loading kbar data for {symbol}.{exchange} ({period}) from database...")
        df = db_manager.get_kbar_data(
            symbol=symbol,
            exchange=exchange,
            period=period,
            limit=limit
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
                                file_prefix: str = "chan", include_timestamp: bool = True):
    """
    Configure logging parameters globally
    
    Args:
        log_level: Logging level ("DEBUG", "INFO", "WARNING", "ERROR")
        log_dir: Directory for log files (relative to current directory)
        file_prefix: Prefix for log file names
        include_timestamp: Whether to include timestamp in log filenames
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
        'timestamp_suffix': timestamp_suffix
    }
    
    print(f"Logging configured: Level={log_level.upper()}, Dir={log_dir}, "
          f"Prefix={file_prefix}, Timestamp={include_timestamp}")


def setup_logging(log_file: str = "chan_analysis.log", log_level: int = logging.DEBUG):
    """
    Setup logging to both console and file
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
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
    
    # Create file handler with same simple format as console
    # To restore detailed file logging, uncomment the next line and comment the one after:
    # file_handler.setFormatter(detailed_formatter)
    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
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
    logger.info(f"Logging setup complete - File: {log_file_path}, Level: {logging.getLevelName(log_level)}")
    
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
    
    # Load data from database or use synthetic data
    print("Loading kbar data...")
    kbars = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=limit)
    print(f"Using {len(kbars)} kbars for analysis")
    
    # Initialize processors
    processor = ChanProcessor(
        strict_fractal_mode=True,
        min_pen_length=0.5,
        min_kbar_count=3,
        min_line_pens=3,
        symbol=symbol,
        exchange=exchange, 
        period=period
    )
    
    # Process kbars through the complete pipeline
    print("\nProcessing kbars through Chan algorithm pipeline...")
    results = processor.process_kbars(kbars)
    
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
    
    # Load data from database or use synthetic data
    kbars = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=limit)
    
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
    
    # Create processor
    processor = ChanProcessor(
        symbol=symbol,
        exchange=exchange,
        period=period
    )
    
    # Load data from database or use synthetic data
    kbars = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=limit)
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
        kbars = load_kbar_data_from_database(symbol=symbol, exchange=exchange, period=period, limit=20)
        
        if not kbars:
            print(f"No data available for {symbol}.{exchange}")
            continue
        
        # Create processor and analyze
        processor = ChanProcessor(
            symbol=symbol,
            exchange=exchange,
            period=period
        )
        results = processor.process_kbars(kbars)
        
        if results['status'] == 'Success':
            summary = results['summary']
            print(f"  Data: {summary['raw_kbars']} kbars -> {summary['merged_kbars']} merged")
            print(f"  Structures: {summary['fractals']} fractals, {summary['pens']} pens, {summary['lines']} lines")
            print(f"  Global line active: {summary['global_line_active']}")
        else:
            print(f"  Analysis failed: {results['status']}")


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
        # Run demonstrations
        demonstrate_step_by_step_processing()
        # demonstrate_individual_components()
        # demonstrate_market_analysis()
        
        # # Only run multiple symbols demo if database is available
        # if DATABASE_AVAILABLE:
        #     demonstrate_multiple_symbols()
        
        # print("\n=== Demo Complete ===")
        # print("The modular Chan algorithm implementation successfully:")
        # print("1. ✓ Merged consecutive kbars based on inclusion relationships")
        # print("2. ✓ Identified fractals from merged kbar patterns")  
        # print("3. ✓ Validated pens using raw kbar data")
        # print("4. ✓ Formed lines and analyzed breaking patterns")
        # print("5. ✓ Maintained global line state for ongoing analysis")
        
        if DATABASE_AVAILABLE:
            print("6. ✓ Loaded real market data from database")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 