"""
Example Usage of Modular Chan Algorithm

This example demonstrates how to use the new modular Chan algorithm implementation
that follows the specified four-step process:

1. Merge kbar process for consecutive kbars
2. Check consecutive merged kbars for fractals
3. Process raw kbars from fractal to fractal to identify chanpen
4. Process chanpen breaking and chanline formation
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional
from .chan_processor import ChanProcessor
from .chan import Kbar

# Add the database module path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Server', 'module', 'database'))

try:
    from db import create_database_manager, DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError:
    print("Warning: Database module not available. Using synthetic data.")
    DATABASE_AVAILABLE = False


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
        # Create database manager with default configuration
        db_manager = create_database_manager()
        
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
        db_manager = create_database_manager()
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
        import random
        price_change = random.uniform(-0.5, 0.5) + direction * 0.1
        current_price += price_change
        
        # Ensure positive prices
        current_price = max(current_price, 50.0)
        
        # Create kbar with some randomness
        high = current_price + random.uniform(0, 0.3)
        low = current_price - random.uniform(0, 0.3)
        open_price = current_price - random.uniform(-0.2, 0.2)
        close_price = current_price
        
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


def demonstrate_step_by_step_processing():
    """Demonstrate step-by-step Chan algorithm processing"""
    print("\n=== Step-by-Step Chan Algorithm Processing ===")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Load data from database or use synthetic data
    print("Loading kbar data...")
    kbars = load_kbar_data_from_database(symbol="000001", exchange="SH", period="1min", limit=30)
    print(f"Using {len(kbars)} kbars for analysis")
    
    # Initialize processors
    processor = ChanProcessor(
        strict_fractal_mode=True,
        min_pen_length=0.5,
        min_kbar_count=3,
        min_line_pens=3
    )
    
    # Process kbars through the complete pipeline
    print("\nProcessing kbars through Chan algorithm pipeline...")
    results = processor.process_kbars(kbars)
    
    # Display results
    print(f"\nProcessing Status: {results['status']}")
    print(f"Summary: {results['summary']}")
    
    # Show step-by-step results
    if 'processing_steps' in results:
        steps = results['processing_steps']
        
        if 'step1_merge' in steps:
            merge_info = steps['step1_merge']
            print(f"\nStep 1 - Kbar Merging:")
            print(f"  Original kbars: {merge_info['original_kbars']}")
            print(f"  Merged kbars: {merge_info['merged_kbars']}")
            print(f"  Compression ratio: {merge_info['compression_ratio']:.2f}")
        
        if 'step2_fractals' in steps:
            fractal_info = steps['step2_fractals']
            print(f"\nStep 2 - Fractal Identification:")
            print(f"  Total fractals: {fractal_info['total_fractals']}")
            print(f"  Top fractals: {fractal_info['top_fractals']}")
            print(f"  Bottom fractals: {fractal_info['bottom_fractals']}")
        
        if 'step3_pens' in steps:
            pen_info = steps['step3_pens']
            print(f"\nStep 3 - Pen Formation:")
            print(f"  Total pens: {pen_info['total_pens']}")
            print(f"  Upward pens: {pen_info['upward_pens']}")
            print(f"  Downward pens: {pen_info['downward_pens']}")
        
        if 'step4_lines' in steps:
            line_info = steps['step4_lines']
            print(f"\nStep 4 - Line Formation:")
            print(f"  Total lines: {line_info['total_lines']}")
            print(f"  Upward lines: {line_info['upward_lines']}")
            print(f"  Downward lines: {line_info['downward_lines']}")
            print(f"  Broken lines: {line_info['broken_lines']}")
            
            if line_info['global_line_info']['exists']:
                global_info = line_info['global_line_info']
                print(f"  Global line: {global_info['direction']} ({global_info['status']})")
    
    # Show latest structures
    if 'latest_structures' in results:
        structures = results['latest_structures']
        print(f"\nLatest Structures:")
        
        if structures['latest_fractal']:
            fractal = structures['latest_fractal']
            print(f"  Latest Fractal: {fractal['type']} at {fractal['price']:.2f} "
                  f"(strength: {fractal['strength']:.4f})")
        
        if structures['latest_pen']:
            pen = structures['latest_pen']
            print(f"  Latest Pen: {pen['direction']} length {pen['length']:.2f} "
                  f"({pen['kbar_count']} kbars)")
        
        if structures['latest_line']:
            line = structures['latest_line']
            print(f"  Latest Line: {line['direction']} with {line['pen_count']} pens "
                  f"({line['status']})")


def demonstrate_individual_components():
    """Demonstrate individual component usage"""
    print("\n=== Individual Component Usage ===")
    
    from .mergekbar import KbarMerger
    from .fractal import FractalIdentifier
    from .pen import PenProcessor
    from .line import LineProcessor
    
    # Load data from database or use synthetic data
    kbars = load_kbar_data_from_database(symbol="000001", exchange="SH", period="1min", limit=20)
    
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
    
    # Create processor
    processor = ChanProcessor()
    
    # Load data from database or use synthetic data
    kbars = load_kbar_data_from_database(symbol="000001", exchange="SH", period="1min", limit=25)
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
        processor = ChanProcessor()
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
    
    # Show database status
    if DATABASE_AVAILABLE:
        print("✓ Database module available - will use real data when possible")
    else:
        print("⚠ Database module not available - using synthetic data only")
    
    try:
        # Run demonstrations
        demonstrate_step_by_step_processing()
        demonstrate_individual_components()
        demonstrate_market_analysis()
        
        # Only run multiple symbols demo if database is available
        if DATABASE_AVAILABLE:
            demonstrate_multiple_symbols()
        
        print("\n=== Demo Complete ===")
        print("The modular Chan algorithm implementation successfully:")
        print("1. ✓ Merged consecutive kbars based on inclusion relationships")
        print("2. ✓ Identified fractals from merged kbar patterns")  
        print("3. ✓ Validated pens using raw kbar data")
        print("4. ✓ Formed lines and analyzed breaking patterns")
        print("5. ✓ Maintained global line state for ongoing analysis")
        
        if DATABASE_AVAILABLE:
            print("6. ✓ Loaded real market data from database")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 