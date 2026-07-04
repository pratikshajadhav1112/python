import sqlite3

def get_db():
    """Create and return database connection"""
    conn = sqlite3.connect('myproject.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    # FIX 1: entries table madhe user_id ani is_dummy add kela
    conn.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            college_name TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            report_date TEXT,
            description TEXT,
            is_dummy INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Users table - FIX 2: role chya pudhcha extra comma kadhla
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    ''')

    # entry_files table pan pahije view_report sathi
    conn.execute('''
        CREATE TABLE IF NOT EXISTS entry_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            filename TEXT,
            FOREIGN KEY (entry_id) REFERENCES entries (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database ready!")

def drop_table():
    """entries table delete karnyasathi"""
    conn = sqlite3.connect('myproject.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS entries')
    cursor.execute('DROP TABLE IF EXISTS reports')
    cursor.execute('DROP TABLE IF EXISTS subjects')
    cursor.execute('DROP TABLE IF EXISTS entry_files')
    cursor.execute('DROP TABLE IF EXISTS users')
    conn.commit()
    conn.close()
    print("Old tables dropped!")

if __name__ == '__main__':
    init_db()