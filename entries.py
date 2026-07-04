import sqlite3
import os

# App.py chya folder madhli DB ghe
db_path = os.path.join(os.path.dirname(__file__), 'myproject.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# entries table madhe user_id add kar
try:
    cursor.execute("ALTER TABLE entries ADD COLUMN user_id INTEGER;")
    print("✅ entries table madhe user_id add jhala")
except:
    print("user_id aadhi pasun ahe")

# Sagle june reports user id 1 la de. 1 = pratiksha jadhav
cursor.execute("UPDATE entries SET user_id = 1 WHERE user_id IS NULL;")
print("✅ June reports pratiksha la dile")

conn.commit()
conn.close()
print("Done! Ata server start kar.")