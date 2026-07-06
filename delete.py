from database import get_db

conn = get_db()

conn.execute("DELETE FROM users")
conn.execute("DELETE FROM sqlite_sequence WHERE name='users'")

conn.commit()
conn.close()

print("All users deleted successfully.")