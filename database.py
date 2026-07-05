   
import os
import sqlite3
from flask import Flask, render_template, request, flash
app = Flask(__name__)
app.secret_key = "linkkiwi2026"  # Needed for flashing messages 

#Absoulute path - Always with app.py folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'myproject.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)  #
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    ''')
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
    conn = get_db()  # Ithe pan get_db() vapraycha
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