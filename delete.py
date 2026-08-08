import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'myproject.db')

def delete_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("DROP TABLE IF EXISTS notifications")
        conn.commit()
        print("SUCCESS: 'notifications' table delete zala")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    delete_table()