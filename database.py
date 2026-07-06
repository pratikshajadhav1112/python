import os
import sqlite3
from werkzeug.security import generate_password_hash

# Absolute path - Always with app.py folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'myproject.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users Table - Navin fields sobat
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            mobile TEXT UNIQUE,
            name TEXT,
            role TEXT DEFAULT 'student',

            -- Verification
            is_mobile_verified INTEGER DEFAULT 0,
            is_email_verified INTEGER DEFAULT 0,
            mobile_otp TEXT,
            otp_generated_at TEXT,

            -- Identity Proof - Aadhar/PAN nako
            profile_photo TEXT,
            id_proof_type TEXT,
            id_proof_number TEXT,
            id_proof_photo TEXT,
            is_id_verified INTEGER DEFAULT 0,

            -- Tracking & Moderation
            signup_ip TEXT,
            signup_user_agent TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_blocked INTEGER DEFAULT 0,
            trust_score INTEGER DEFAULT 100
        )
    ''')

    # Entries Table - Complaint sathi navin fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            college_name TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            report_date TEXT,
            description TEXT,

            -- Incident Location
            incident_state TEXT,
            incident_district TEXT,
            incident_city TEXT,
            incident_college TEXT,
            incident_address TEXT,

            -- Multiple Files - JSON madhe store karu
            photos TEXT,
            videos TEXT,
            audios TEXT,

            -- Admin
            admin_remark TEXT,
            is_dummy INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,

            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Entry Files Table - Optional, jar JSON nako asel tar
    c.execute('''
        CREATE TABLE IF NOT EXISTS entry_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            filename TEXT,
            file_type TEXT, -- 'photo', 'video', 'audio'
            FOREIGN KEY (entry_id) REFERENCES entries (id)
        )
    ''')

    # Default Admin User banav - Ekda ch
    admin_exists = c.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
    if not admin_exists:
        hashed_pw = generate_password_hash('admin123')
        c.execute('''INSERT INTO users
                     (username, password, name, email, role, is_mobile_verified)
                     VALUES (?,?,?,?,?,?)''',
                  ('admin', hashed_pw, 'Admin', 'admin@linkkiwi.com', 'admin', 1))

    conn.commit()
    conn.close()
    print("✅ Database ready with new schema!")

def drop_table():
    """All tables delete karnyasathi - Navin schema sathi"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS entry_files')
    cursor.execute('DROP TABLE IF EXISTS entries')
    cursor.execute('DROP TABLE IF EXISTS users')
    conn.commit()
    conn.close()
    print("Old tables dropped!")

if __name__ == '__main__':
    # Pahile juni tables delete kar, mag navin banav
    drop_table()
    init_db()