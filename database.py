import sqlite3

def get_db():
    """
    Create and return database connection
    Uses Row factory to access columns by name
    """
    conn = sqlite3.connect('myproject.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize database and create entries table
    Fields match form.html: exam_name, subject_name, college_name, 
    status, report_date, description
    """
    conn = sqlite3.connect('myproject.db')
    cursor = conn.cursor()
    
    # Create entries table with all form fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_name TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            college_name TEXT NOT NULL,
            status TEXT NOT NULL,
            report_date TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")
    print("Table 'entries' created with fields: exam_name, subject_name, college_name, status, report_date, description")

def drop_table():
    """
    Utility function to drop table if you need to reset database
    WARNING: This will delete all existing data
    """
    conn = sqlite3.connect('myproject.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS entries')
    conn.commit()
    conn.close()
    print("Table 'entries' dropped successfully!")

if __name__ == '__main__':
    # Run this file directly to initialize database
    init_db()