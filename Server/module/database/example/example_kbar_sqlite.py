"""
Example usage of SQLite K-bar Database

This script demonstrates how to use the SQLite-based K-bar database
for storing and retrieving stock data.
"""

import logging
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path to find kbar_db_sqlite module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kbar_db_sqlite import KbarDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)

def example_usage():
    """Example of using SQLite K-bar database."""
    
    # Database configuration for SQLite
    config = {
        'database_path': 'data/kbar_data.db',  # SQLite database file path
        'create_dir': True                      # Create directory if it doesn't exist
    }
    
    # Initialize database
    with KbarDatabase(config) as db:
        print("=== SQLite K-bar Database Example ===")
        
        # Example 1: Insert single record
        print("\n1. Inserting single record...")
        single_data = {
            'timestamp': datetime(2024, 1, 1, 9, 30, 0),
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'amount': 102500000.0,
            'pre_close': 101.0,
            'change_rate': 1.98
        }
        db.insert_kbar_data(single_data, symbol='000001', exchange='SZ', period='1min')
        
        # Example 2: Insert batch data
        print("\n2. Inserting batch data...")
        batch_data = []
        base_time = datetime(2024, 1, 1, 9, 31, 0)
        for i in range(5):
            batch_data.append({
                'timestamp': base_time + timedelta(minutes=i),
                'open': 103.0 + i,
                'high': 107.0 + i,
                'low': 102.0 + i,
                'close': 105.0 + i,
                'volume': 800000 + i * 10000,
                'amount': 84000000.0 + i * 1000000,
                'pre_close': 103.0,
                'change_rate': 1.5 + i * 0.1
            })
        db.insert_kbar_data(batch_data, symbol='000001', exchange='SZ', period='1min')
        
        # Example 3: Insert DataFrame
        print("\n3. Inserting DataFrame...")
        df_data = {
            'timestamp': [datetime(2024, 1, 1, 9, 36, 0) + timedelta(minutes=i) for i in range(3)],
            'open': [108.0, 109.0, 110.0],
            'high': [112.0, 113.0, 114.0],
            'low': [107.0, 108.0, 109.0],
            'close': [111.0, 112.0, 113.0],
            'volume': [900000, 950000, 1000000],
            'amount': [99900000.0, 106400000.0, 113000000.0],
            'pre_close': [103.0, 103.0, 103.0],
            'change_rate': [7.77, 8.74, 9.71]
        }
        df = pd.DataFrame(df_data)
        db.insert_kbar_data(df, symbol='000001', exchange='SZ', period='1min')
        
        # Example 4: Query data
        print("\n4. Querying data...")
        result_df = db.query_kbar_data(
            symbol='000001', 
            exchange='SZ', 
            period='1min',
            start_time=datetime(2024, 1, 1, 9, 30, 0),
            end_time=datetime(2024, 1, 1, 9, 40, 0)
        )
        print(f"Retrieved {len(result_df)} records")
        print(result_df.head())
        
        # Example 5: Get latest timestamp
        print("\n5. Getting latest timestamp...")
        latest_ts = db.get_latest_timestamp(symbol='000001', exchange='SZ', period='1min')
        print(f"Latest timestamp: {latest_ts}")
        
        # Example 6: Get symbols
        print("\n6. Getting all symbols...")
        symbols = db.get_symbols()
        print(f"Symbols in database: {symbols}")
        
        # Example 7: Get data count
        print("\n7. Getting data count...")
        count = db.get_data_count(symbol='000001', exchange='SZ', period='1min')
        print(f"Total records for 000001.SZ (1min): {count}")
        
        # Example 8: Database info
        print("\n8. Database information...")
        db_info = db.get_database_info()
        for key, value in db_info.items():
            print(f"{key}: {value}")
        
        # Example 9: Add data for another symbol
        print("\n9. Adding data for another symbol...")
        db.insert_kbar_data(single_data, symbol='000002', exchange='SZ', period='5min')
        
        symbols = db.get_symbols()
        print(f"Updated symbols list: {symbols}")

def performance_test():
    """Test performance with larger dataset."""
    print("\n=== Performance Test ===")
    
    config = {
        'database_path': 'data/kbar_performance_test.db',
        'create_dir': True
    }
    
    with KbarDatabase(config) as db:
        # Generate test data
        print("Generating test data...")
        test_data = []
        base_time = datetime(2024, 1, 1, 9, 30, 0)
        
        for i in range(1000):  # 1000 records
            test_data.append({
                'timestamp': base_time + timedelta(minutes=i),
                'open': 100.0 + (i % 10),
                'high': 105.0 + (i % 10),
                'low': 95.0 + (i % 10),
                'close': 102.0 + (i % 10),
                'volume': 1000000 + i * 1000,
                'amount': 102000000.0 + i * 102000,
                'pre_close': 101.0,
                'change_rate': (i % 20) * 0.1
            })
        
        # Insert performance test
        print(f"Inserting {len(test_data)} records...")
        start_time = datetime.now()
        db.insert_kbar_data(test_data, symbol='TEST001', exchange='SZ', period='1min')
        insert_time = (datetime.now() - start_time).total_seconds()
        print(f"Insert time: {insert_time:.2f} seconds")
        
        # Query performance test
        print("Querying data...")
        start_time = datetime.now()
        result = db.query_kbar_data(
            symbol='TEST001', 
            exchange='SZ', 
            period='1min',
            limit=500
        )
        query_time = (datetime.now() - start_time).total_seconds()
        print(f"Query time: {query_time:.2f} seconds")
        print(f"Retrieved {len(result)} records")

if __name__ == "__main__":
    example_usage()
    performance_test() 