"""
Example usage of the database wrapper system.

This file demonstrates how to use the unified database manager for
storing and retrieving both K-bar data and meta data.
"""

import pandas as pd
from datetime import datetime, timedelta
from db import create_database_manager, DEFAULT_KBAR_CONFIG, DEFAULT_META_CONFIG


def main():
    """Example usage of the database system."""
    
    # Configuration for both databases
    kbar_config = DEFAULT_KBAR_CONFIG.copy()
    kbar_config.update({
        'host': 'localhost',
        'port': 6030,
        'user': 'root',
        'password': 'taosdata',
        'database': 'stock_kbar'
    })
    
    meta_config = DEFAULT_META_CONFIG.copy()
    meta_config.update({
        'database_path': 'data/stock_meta.db'
    })
    
    # Create database manager
    with create_database_manager(kbar_config, meta_config) as db_manager:
        
        print("=" * 60)
        print("Database Manager Example")
        print("=" * 60)
        
        # Check what databases are available
        stats = db_manager.get_database_stats()
        print(f"K-bar DB available: {stats['kbar_db_available']}")
        print(f"Meta DB available: {stats['meta_db_available']}")
        
        if not stats['meta_db_available']:
            print("ERROR: Meta database not available. Cannot continue.")
            return
        
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
        
        # 2. Store sample K-bar data (only if TDengine is available)
        if stats['kbar_db_available']:
            print("\n2. Storing K-bar data...")
            
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
            
            # 3. Query K-bar data
            print("\n3. Querying K-bar data...")
            
            # Get latest 10 records
            recent_data = db_manager.get_kbar_data(
                symbol='000001',
                exchange='SH',
                period='1min',
                limit=10
            )
            print(f"   Retrieved {len(recent_data)} recent records")
            if not recent_data.empty:
                print("   Sample data:")
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
            print(f"   Retrieved {len(hourly_data)} records for last hour")
            
            # Get latest timestamp
            latest_ts = db_manager.get_latest_timestamp('000001', 'SH', '1min')
            if latest_ts:
                print(f"   Latest data timestamp: {latest_ts}")
        else:
            print("\n2. K-bar data operations skipped (TDengine not available)")
            print("   To enable K-bar data storage:")
            print("   - Install and start TDengine server")
            print("   - Ensure TDengine is running on localhost:6030")
        
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
                print(f"   Sync status: {sync_status['sync_status']}")
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
        
        # 7. Get database statistics
        print("\n7. Database statistics:")
        final_stats = db_manager.get_database_stats()
        print(f"   K-bar DB available: {final_stats['kbar_db_available']}")
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
        
        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)
        
        if not stats['kbar_db_available']:
            print("\nNOTE: Some features were limited due to TDengine unavailability.")
            print("To enable full functionality, install and start TDengine server.")


if __name__ == "__main__":
    main() 