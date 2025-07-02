import sqlite3
import os

# Get the correct path to the database
db_path = r'C:\Users\lhe\Documents\github\qautil\QAutils\Server\tdx_db\stock_kbar.db'

print(f"Trying to connect to: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    print("Database file not found!")
    exit(1)

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check for 2120 symbol variants
    cursor.execute("SELECT DISTINCT symbol, exchange, period FROM kbar_data WHERE symbol LIKE '%2120%' OR symbol LIKE '%002120%' LIMIT 10")
    results = cursor.fetchall()

    print("\nSymbol formats in database matching 2120:")
    for r in results:
        print(f"symbol='{r[0]}', exchange='{r[1]}', period='{r[2]}'")

    # Also check what symbols are actually in the database
    cursor.execute("SELECT DISTINCT symbol, exchange, period FROM kbar_data LIMIT 20")
    all_results = cursor.fetchall()

    print("\nFirst 20 symbols in database:")
    for r in all_results:
        print(f"symbol='{r[0]}', exchange='{r[1]}', period='{r[2]}'")

    conn.close()
    print("\nDatabase query completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    if 'conn' in locals():
        conn.close() 