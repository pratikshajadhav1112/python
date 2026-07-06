import sqlite3

conn = sqlite3.connect("myproject.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
    print("✅ name column added")
except Exception as e:
    print("name:", e)

try:
    cursor.execute("ALTER TABLE users ADD COLUMN mobile TEXT")
    print("✅ mobile column added")
except Exception as e:
    print("mobile:", e)

try:
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    print("✅ email column added")
except Exception as e:
    print("email:", e)
try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_mobile_verified INTEGER DEFAULT 0")
    print("✅ is_mobile_verified column added")
except Exception as e:
    print(e)

conn.commit()
conn.close()

print("Done!")