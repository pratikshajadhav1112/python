from database import get_db
from werkzeug.security import generate_password_hash

conn = get_db()

username = "Pratiksha Jadhav"
password = "pratikshaj@123"     
email = "pratikshaj1113@gmail.com"
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
        ( username, email, mobile, password, role)
        VALUES ( ?, ?, ?, ?, ?)
    """, (
        username,
        email,
        mobile,
        generate_password_hash(password),
        "admin"
        
    ))

    conn.commit()
    print("✅ Admin created successfully!")
    print("Username:", username)
    print("Password:", password)

conn.close()