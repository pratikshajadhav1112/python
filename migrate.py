import sqlite3

conn = sqlite3.connect('myproject.db')
c = conn.cursor()

# Settings table add kar
c.execute('''CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                ai_model TEXT DEFAULT 'llama-3.1-8b-instant',
                maintenance_mode INTEGER DEFAULT 0,
                registration_open INTEGER DEFAULT 1,
                max_daily_complaints INTEGER DEFAULT 5
            )''')

# Default row insert
c.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")

conn.commit()
conn.close()
print("Settings table added successfully!")