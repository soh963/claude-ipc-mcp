import sqlite3

db_path = r'C:\Users\lovecat\.claude-ipc-data\messages.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List of instances to delete
instances_to_delete = [
    'gemini-test',
    'codex-test',
    'claude-sender',
    'gemini-receiver',
    'claude-test'
]

print("Deleting instances...")
for instance_id in instances_to_delete:
    # Delete from instances table
    cursor.execute("DELETE FROM instances WHERE instance_id = ?", (instance_id,))
    print(f"  Deleted: {instance_id}")

# Also delete related sessions
cursor.execute("DELETE FROM sessions WHERE instance_id IN ({})".format(
    ','.join('?' * len(instances_to_delete))
), instances_to_delete)

# Also delete related messages (sent or received)
cursor.execute("DELETE FROM messages WHERE from_id IN ({}) OR to_id IN ({})".format(
    ','.join('?' * len(instances_to_delete)),
    ','.join('?' * len(instances_to_delete))
), instances_to_delete + instances_to_delete)

conn.commit()

# Verify deletion
cursor.execute("SELECT instance_id, last_seen FROM instances")
remaining = cursor.fetchall()
print(f"\nRemaining instances ({len(remaining)}):")
for instance in remaining:
    print(f"  - {instance[0]} (last seen: {instance[1]})")

conn.close()
print("\n✅ Deletion complete!")
