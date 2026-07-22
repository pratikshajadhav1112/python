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
            email_otp TEXT,
            otp_generated_at TEXT,

            -- Identity Proof 
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

    # Entries Table - Fakt ekdach
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

            -- AI fields
            category TEXT,
            urgency_score INTEGER DEFAULT 0,
            ai_summary TEXT,
            sentiment TEXT,
            fake_status TEXT,
            admin_remark TEXT,
            is_dummy INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,

            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Entry Files Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS entry_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            filename TEXT,
            file_type TEXT, -- 'photo', 'video', 'audio'
            FOREIGN KEY (entry_id) REFERENCES entries (id)
        )
    ''')
    
    # Notifications Table
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT,
                    message TEXT,
                    link TEXT,
                    is_read INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Admin user banav
    admin_exists = c.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
    if not admin_exists:
        hashed_pw = generate_password_hash('admin123')
        c.execute('''INSERT INTO users
                     (username, password, name, email, role, is_mobile_verified, is_email_verified)
                     VALUES (?,?,?,?,?,?,?)''',
                  ('admin', hashed_pw, 'Admin', 'admin@linkkiwi.com', 'admin', 1, 1))
   
    conn.commit()  # <- Sagla commit ithach
    conn.close()   # <- Mag close
    print("✅ Database ready with new schema!")