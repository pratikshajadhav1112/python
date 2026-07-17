import sqlite3

conn = sqlite3.connect("myproject.db")
cursor = conn.cursor()

print("Checking and adding columns to 'entries' table...")

columns = [
    "category TEXT DEFAULT 'Other'",
    "ai_summary TEXT DEFAULT ''",
    "urgency_score INTEGER DEFAULT 0",
    "sentiment TEXT DEFAULT 'Normal'"
]

for col in columns:
    col_name = col.split()[0]
    try:
        cursor.execute(f"ALTER TABLE entries ADD COLUMN {col}")
        print(f"✅ {col_name} column added")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"⏭️ {col_name}: Already exists")
        else:
            print(f"❌ Error in {col_name}: {e}")

conn.commit()
conn.close()

print("\nDone! Now restart app.py")