import sqlite3
import sys

# Windows CMD la UTF-8 support dyaycha
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("myproject.db")
cursor = conn.cursor()

print("Checking and adding columns to 'users' table...")

columns = [
    "username TEXT UNIQUE",
    "name TEXT",
    "mobile TEXT",
    "email TEXT",
    "password TEXT",
    "state TEXT",
    "district TEXT",
    "signup_ip TEXT",
    "signup_user_agent TEXT",
    "role TEXT DEFAULT 'student'",
    "is_mobile_verified INTEGER DEFAULT 0",
    "is_email_verified INTEGER DEFAULT 0",
    "mobile_otp TEXT",
    "otp_generated_at TEXT",
    "is_blocked INTEGER DEFAULT 0"
]

for col in columns:
    col_name = col.split()[0]
    try:
        # SQLite madhe IF NOT EXISTS direct ALTER madhe nahi chalat
        cursor.execute(f"ALTER TABLE users ADD COLUMN {col}")
        print(f"[OK] {col_name} column added")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"[SKIP] {col_name}: Already exists")
        else:
            print(f"[ERROR] {col_name}: {e}")

# Admin update
try:
    cursor.execute("UPDATE users SET is_email_verified=1, is_mobile_verified=1, role='admin' WHERE username='admin'")
    if cursor.rowcount > 0:
        print("[OK] Admin verified successfully")
    else:
        print("[INFO] 'admin' username not found. Please create admin user first")
except Exception as e:
    print(f"[ERROR] Admin update error: {e}")

conn.commit()
conn.close()

print("\nDone! Now run app.py")