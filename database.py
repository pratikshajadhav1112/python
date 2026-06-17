# Import sqlite3 library for database operations
import sqlite3

def get_db():
    """
    Create and return database connection
    Uses Row factory to access columns by name
    """
    # Connect to the database file
    conn = sqlite3.connect('myproject.db')
    # Set row factory to return Row objects instead of tuples for easier column access
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_name TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            college_name TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            report_date TEXT,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()
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