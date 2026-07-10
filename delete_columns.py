import sqlite3

conn = sqlite3.connect("myproject.db")
cursor = conn.cursor()

print("Checking and adding columns to 'users' table...")

columns = [
    "name TEXT",
    "mobile TEXT",
    "email TEXT",
    "role TEXT DEFAULT 'student'",
    "is_mobile_verified INTEGER DEFAULT 0",
    "is_email_verified INTEGER DEFAULT 0", # Email verify sathi
    "mobile_otp TEXT",
    "otp_generated_at TEXT",
    "is_blocked INTEGER DEFAULT 0" # <-- Admin panel sathi he pan add kela
]

for col in columns:
    col_name = col.split()[0]
    try:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {col}")
        print(f"✅ {col_name} column added")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"⏭️ {col_name}: Already exists")
        else:
            print(f"❌ Error in {col_name}: {e}")

# Admin ko verified kar do warna login nahi hoga
try:
    cursor.execute("UPDATE users SET is_email_verified=1, is_mobile_verified=1, role='admin' WHERE username='admin'")
    if cursor.rowcount > 0:
        print("✅ Admin verified successfully")
    else:
        print("⚠️ 'admin' username not found. Please create admin user first")
except Exception as e:
    print(f"❌ Admin update error: {e}")

conn.commit()
conn.close()

print("\nDone! Now restart app.py")