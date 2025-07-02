"""
Example usage of the database wrapper system.

This file demonstrates how to use the unified database manager for
storing and retrieving both K-bar data and meta data using either
TDengine or SQLite for K-bar data storage.
"""

import pandas as pd
from datetime import datetime, timedelta
from db import (
    create_database_manager, 
    DEFAULT_KBAR_CONFIG_TDENGINE, 
    DEFAULT_KBAR_CONFIG_SQLITE,
    DEFAULT_META_CONFIG
)


def run_example_with_kbar_type(kbar_type='sqlite'):
    """Run example with specified K-bar database type."""
    
    print(f"\n{'='*80}")
    print(f"Database Manager Example - Using {kbar_type.upper()} for K-bar data")
    print(f"{'='*80}")
    
    # Configuration for both databases
    if kbar_type == 'tdengine':
        kbar_config = DEFAULT_KBAR_CONFIG_TDENGINE.copy()
        kbar_config.update({
            'host': 'localhost',
            'port': 6030,
            'user': 'root',
            'password': 'taosdata',
            'database': 'stock_kbar'
        })
    else:  # sqlite
        kbar_config = DEFAULT_KBAR_CONFIG_SQLITE.copy()
        kbar_config.update({
            'database_path': 'data/stock_kbar_example.db',
            'create_dir': True
        })
    
    meta_config = DEFAULT_META_CONFIG.copy()
    meta_config.update({
        'database_path': 'data/stock_meta_example.db'
    })
    
    # Create database manager with specified K-bar type
    with create_database_manager(kbar_config, meta_config, kbar_type) as db_manager:
        
        # Check what databases are available
        stats = db_manager.get_database_stats()
        print(f"K-bar DB ({kbar_type}) available: {stats['kbar_db_available']}")
        print(f"Meta DB available: {stats['meta_db_available']}")
        
        if not stats['meta_db_available']:
            print("ERROR: Meta database not available. Cannot continue.")
            return False
        
        # 1. Setup exchanges and stocks
        print("\n1. Setting up stocks...")
        
        # Setup Shanghai Exchange stocks
        stock_id_1 = db_manager.setup_stock(
            symbol='000001',
            exchange='SH',
            name='平安银行',
            sector='Banking',
            industry='Commercial Banks',
            currency='CNY',
            country='CN',
            exchange_name='Shanghai Stock Exchange',
            timezone='Asia/Shanghai'
        )
        print(f"   Created stock: 000001.SH (ID: {stock_id_1})")
        
        # Setup Shenzhen Exchange stocks
        stock_id_2 = db_manager.setup_stock(
            symbol='000002',
            exchange='SZ',
            name='万科A',
            sector='Real Estate',
            industry='Real Estate Development',
            currency='CNY',
            country='CN',
            exchange_name='Shenzhen Stock Exchange',
            timezone='Asia/Shanghai'
        )
        print(f"   Created stock: 000002.SZ (ID: {stock_id_2})")
        
        # 2. Store sample K-bar data
        if stats['kbar_db_available']:
            print(f"\n2. Storing K-bar data using {kbar_type.upper()}...")
            
            # Sample K-bar data for 000001.SH
            sample_data = []
            base_time = datetime.now().replace(second=0, microsecond=0)
            
            for i in range(100):
                timestamp = base_time - timedelta(minutes=i)
                sample_data.append({
                    'timestamp': timestamp,
                    'open': 10.0 + i * 0.01,
                    'high': 10.1 + i * 0.01,
                    'low': 9.9 + i * 0.01,
                    'close': 10.05 + i * 0.01,
                    'volume': 1000000 + i * 1000,
                    'amount': 10000000.0 + i * 10000,
                    'pre_close': 10.0 + (i-1) * 0.01,
                    'change_rate': 0.01
                })
            
            # Store 1-minute data
            db_manager.store_kbar_data('000001', 'SH', '1min', sample_data)
            print("   Stored 1-minute K-bar data for 000001.SH")
            
            # Convert to DataFrame and store as 5-minute data
            df = pd.DataFrame(sample_data)
            db_manager.store_kbar_data('000001', 'SH', '5min', df)
            print("   Stored 5-minute K-bar data for 000001.SH")
            
            # Store data for second stock
            sample_data_2 = []
            for i in range(50):
                timestamp = base_time - timedelta(minutes=i*2)
                sample_data_2.append({
                    'timestamp': timestamp,
                    'open': 25.0 + i * 0.02,
                    'high': 25.2 + i * 0.02,
                    'low': 24.8 + i * 0.02,
                    'close': 25.1 + i * 0.02,
                    'volume': 500000 + i * 500,
                    'amount': 12500000.0 + i * 12500,
                    'pre_close': 25.0 + (i-1) * 0.02,
                    'change_rate': 0.02
                })
            
            db_manager.store_kbar_data('000002', 'SZ', '1min', sample_data_2)
            print("   Stored 1-minute K-bar data for 000002.SZ")
            
            # 3. Query K-bar data
            print(f"\n3. Querying K-bar data from {kbar_type.upper()}...")
            
            # Get latest 10 records
            recent_data = db_manager.get_kbar_data(
                symbol='000001',
                exchange='SH',
                period='1min',
                limit=10
            )
            print(f"   Retrieved {len(recent_data)} recent records for 000001.SH")
            if not recent_data.empty:
                print("   Sample data (first 3 rows):")
                print(recent_data.head(3).to_string(index=False))
            
            # Get data for specific time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            hourly_data = db_manager.get_kbar_data(
                symbol='000001',
                exchange='SH',
                period='1min',
                start_time=start_time,
                end_time=end_time
            )
            print(f"   Retrieved {len(hourly_data)} records for 000001.SH in last hour")
            
            # Query data for second stock
            sz_data = db_manager.get_kbar_data(
                symbol='000002',
                exchange='SZ',
                period='1min',
                limit=5
            )
            print(f"   Retrieved {len(sz_data)} records for 000002.SZ")
            
            # Get latest timestamp
            latest_ts = db_manager.get_latest_timestamp('000001', 'SH', '1min')
            if latest_ts:
                print(f"   Latest data timestamp for 000001.SH: {latest_ts}")
                
            # Get symbols with data
            symbols_with_data = db_manager.get_symbols_with_data()
            print(f"   Total symbols with K-bar data: {len(symbols_with_data)}")
            for symbol_info in symbols_with_data[:5]:  # Show first 5
                print(f"     - {symbol_info['symbol']}.{symbol_info['exchange']} ({symbol_info.get('period', 'N/A')})")
                
        else:
            print(f"\n2. K-bar data operations skipped ({kbar_type.upper()} not available)")
            if kbar_type == 'tdengine':
                print("   To enable TDengine K-bar data storage:")
                print("   - Install and start TDengine server")
                print("   - Ensure TDengine is running on localhost:6030")
            else:
                print("   SQLite K-bar database should be available by default.")
        
        # 4. Query stock information (always available with meta DB)
        print("\n4. Querying stock information...")
        
        stock_info = db_manager.get_stock_info('000001', 'SH')
        if stock_info:
            print(f"   Stock: {stock_info['name']} ({stock_info['symbol']}.{stock_info['exchange_code']})")
            print(f"   Sector: {stock_info['sector']}, Industry: {stock_info['industry']}")
        
        # Get all stocks
        all_stocks = db_manager.get_all_stocks()
        print(f"   Total stocks in database: {len(all_stocks)}")
        
        # 5. Check sync status
        if stats['kbar_db_available']:
            print("\n5. Checking sync status...")
            sync_status = db_manager.get_sync_status('000001', 'SH', 'kbar', '1min')
            if sync_status:
                print(f"   Sync status for 000001.SH: {sync_status['sync_status']}")
                print(f"   Last sync: {sync_status['last_sync_time']}")
        
        # 6. Store dividend information
        print("\n6. Storing dividend information...")
        
        db_manager.store_dividend(
            symbol='000001',
            exchange='SH',
            ex_date='2024-06-15',
            amount=0.5,
            currency='CNY',
            type='cash'
        )
        print("   Stored dividend information for 000001.SH")
        
        # Store stock split
        db_manager.store_split(
            symbol='000002',
            exchange='SZ',
            ex_date='2024-07-01',
            ratio=2.0
        )
        print("   Stored stock split information for 000002.SZ")
        
        # 7. Get database statistics
        print("\n7. Database statistics:")
        final_stats = db_manager.get_database_stats()
        print(f"   K-bar DB ({kbar_type}) available: {final_stats['kbar_db_available']}")
        print(f"   Meta DB available: {final_stats['meta_db_available']}")
        print(f"   Total stocks: {final_stats['total_stocks']}")
        print(f"   Symbols with data: {final_stats['total_symbols_with_data']}")
        print(f"   Exchanges: {[ex['code'] for ex in final_stats['exchanges']]}")
        
        # 8. Custom queries
        print("\n8. Running custom queries...")
        
        # Get stocks by sector
        banking_stocks = db_manager.execute_meta_query(
            "SELECT symbol, name FROM stocks WHERE sector = ?",
            ('Banking',)
        )
        print(f"   Banking stocks: {len(banking_stocks)}")
        for stock in banking_stocks:
            print(f"     - {stock['symbol']}: {stock['name']}")
        
        # Get stocks by exchange
        sh_stocks = db_manager.execute_meta_query(
            "SELECT s.symbol, s.name FROM stocks s JOIN exchanges e ON s.exchange_id = e.id WHERE e.code = ?",
            ('SH',)
        )
        print(f"   Shanghai Exchange stocks: {len(sh_stocks)}")
        
        print(f"\n{'='*80}")
        print(f"Example with {kbar_type.upper()} completed successfully!")
        print(f"{'='*80}")
        
        return stats['kbar_db_available']


def main():
    """Main function demonstrating both database types."""
    
    print("Database Manager Example - Multiple K-bar Database Types")
    print("This example demonstrates using both SQLite and TDengine for K-bar data storage.")
    
    # Try SQLite first (default and most likely to work)
    print("\n" + "="*100)
    print("PART 1: Demonstrating SQLite K-bar Database")
    print("="*100)
    
    sqlite_success = run_example_with_kbar_type('sqlite')
    
    # Try TDengine (may not be available)
    print("\n" + "="*100)
    print("PART 2: Demonstrating TDengine K-bar Database")
    print("="*100)
    
    tdengine_success = run_example_with_kbar_type('tdengine')
    
    # Summary
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"SQLite K-bar database: {'✓ Available' if sqlite_success else '✗ Not available'}")
    print(f"TDengine K-bar database: {'✓ Available' if tdengine_success else '✗ Not available'}")
    
    if sqlite_success:
        print("\n✓ SQLite K-bar database is working and recommended for:")
        print("  - Development and testing")
        print("  - Small to medium datasets")
        print("  - Simple deployment without external dependencies")
        print("  - File-based storage with good performance")
        
    if tdengine_success:
        print("\n✓ TDengine K-bar database is working and recommended for:")
        print("  - Production environments with large datasets")
        print("  - High-frequency time series data")
        print("  - Advanced time series analytics")
        print("  - Distributed storage and processing")
    
    if not tdengine_success:
        print("\n! TDengine not available. To enable TDengine:")
        print("  1. Install TDengine server")
        print("  2. Start TDengine service")
        print("  3. Ensure it's running on localhost:6030")
        print("  4. Install Python TDengine client (taospy)")
    
    print("\nBoth database types use the same unified API, so you can switch between them")
    print("by simply changing the 'kbar_type' parameter in create_database_manager().")


if __name__ == "__main__":
    main() 