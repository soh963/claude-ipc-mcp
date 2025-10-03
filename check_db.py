import sqlite3

conn = sqlite3.connect('.ipc/state/messages.db')
cur = conn.cursor()

# Get all tables
cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [row[0] for row in cur.fetchall()]
print('Tables:', tables)

# Count rows in each table
print('\n--- Row Counts ---')
for table in tables:
    if not table.startswith('sqlite_'):
        cur.execute(f'SELECT COUNT(*) FROM {table}')
        count = cur.fetchone()[0]
        print(f'{table}: {count}')

# Show all instances
print('\n--- Instances ---')
cur.execute('SELECT * FROM instances')
instances = cur.fetchall()
print(instances if instances else 'Empty')

# Show all sessions
print('\n--- Sessions ---')
cur.execute('SELECT * FROM sessions')
sessions = cur.fetchall()
print(sessions if sessions else 'Empty')

# Check database file size vs actual data
import os
file_size = os.path.getsize('.ipc/state/messages.db')
print(f'\n--- Database File Size ---')
print(f'File size: {file_size} bytes ({file_size/1024:.1f} KB)')

conn.close()
