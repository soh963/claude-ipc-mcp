import sqlite3

db_path = r'C:\Users\lovecat\.claude-ipc-data\messages.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# Check instances
try:
    cursor.execute("SELECT * FROM instances")
    instances = cursor.fetchall()
    print("\nInstances:", instances)
except Exception as e:
    print(f"\nError querying instances: {e}")

# Check messages
try:
    cursor.execute("SELECT * FROM messages LIMIT 5")
    messages = cursor.fetchall()
    print("\nMessages:", messages)
except Exception as e:
    print(f"\nError querying messages: {e}")

conn.close()
