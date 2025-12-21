"""
Test database connection to Neon PostgreSQL
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn_string = os.getenv("DATABASE_URL")

print("=" * 60)
print("🧪 Testing Neon Database Connection")
print("=" * 60)

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    
    # Get tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
    tables = cur.fetchall()
    
    print("✅ Database Connection Successful!")
    print(f"📊 Tables Created: {len(tables)}")
    print("\nTables in Database:")
    for table in tables:
        print(f"  ✓ {table[0]}")
    
    # Get row counts
    print("\nTable Row Counts:")
    for table in tables:
        table_name = table[0]
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        print(f"  {table_name}: {count} rows")
    
    conn.close()
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Connection Error: {e}")
    print("\nPlease check:")
    print("  1. DATABASE_URL is set correctly in .env")
    print("  2. Neon database is reachable")
    print("  3. Network/firewall allows connection")
