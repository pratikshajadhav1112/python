from database import get_db
from werkzeug.security import generate_password_hash

conn = get_db()

username = "Pratiksha Jadhav"
password = "pratiksha@123"     
name = "Pratiksha Jadhav"
email = "pratikshaj@gmail.com"
mobile = "9226630571"

user = conn.execute(
    "SELECT * FROM users WHERE username = ?",
    (username,)
).fetchone()

if user:
    print("❌ Admin already exists!")
else:
    conn.execute("""
        INSERT INTO users
        (name, username, email, mobile, password, role)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        username,
        email,
        mobile,
        generate_password_hash(password),
        "admin"
        1
        
    ))

    conn.commit()
    print("✅ Admin created successfully!")
    print("Username:", username)
    print("Password:", password)

conn.close()