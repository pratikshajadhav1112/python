import os
import sqlite3
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'myproject.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON") # foreign key on kela
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            mobile TEXT UNIQUE,
            name TEXT,
            role TEXT DEFAULT 'student',
            is_mobile_verified INTEGER DEFAULT 0,
            is_email_verified INTEGER DEFAULT 0,
            email_otp TEXT,
            otp_generated_at TEXT,
            profile_photo TEXT,
            signup_ip TEXT,
            signup_user_agent TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_blocked INTEGER DEFAULT 0,
            trust_score INTEGER DEFAULT 100
        )
    ''')

    # Entries Table
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
            incident_state TEXT,
            incident_district TEXT,
            incident_city TEXT,
            photos TEXT,
            videos TEXT, -- add kele
            audios TEXT, -- add kele
            urgency_score INTEGER DEFAULT 0,
            ai_summary TEXT,
            category TEXT,
            sentiment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Settings Table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    ai_model TEXT DEFAULT 'llama-3.1-8b-instant',
                    maintenance_mode INTEGER DEFAULT 0,
                    registration_open INTEGER DEFAULT 1,
                    max_daily_complaints INTEGER DEFAULT 5
                )''')
    c.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")

    # Notifications Table - FIXED
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT,
                    message TEXT,
                    link TEXT,
                    is_read INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')

    # Entry_files Table - tuza code madhe use aahe
    c.execute('''CREATE TABLE IF NOT EXISTS entry_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT,
                    FOREIGN KEY(entry_id) REFERENCES entries(id)
                )''')

    # Admin user
    admin_exists = c.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
    if not admin_exists:
        hashed_pw = generate_password_hash('admin123')
        c.execute('''INSERT INTO users
                     (username, password, name, email, role, is_email_verified)
                     VALUES (?,?,?,?,?,?)''',
                  ('admin', hashed_pw, 'Admin', 'admin@linkkiwi.com', 'admin', 1))
   
    conn.commit()
    conn.close()
    print("✅ Database ready!")
   