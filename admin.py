from database import get_db
from werkzeug.security import generate_password_hash

conn = get_db()
c = conn.cursor()

username = "Pratiksha Jadhav"
password = "pratikshaj@123"     
email = "pratikshaj1113@gmail.com"
mobile = "9226630571"

user = c.execute(
    "SELECT * FROM users WHERE username = ? OR email = ?",
    (username, email)
).fetchone()

if user:
    print("❌ User already exists!")
    # Agar exist karta hai to usko admin + verified kar do
    c.execute("""
        UPDATE users 
        SET role='admin', is_email_verified=1, is_mobile_verified=1 
        WHERE username=? OR email=?
    """, (username, email))
    conn.commit()
    print("✅ Existing user ko admin + verified kar diya")
else:
    c.execute("""
        INSERT INTO users
        (name, username, email, mobile, password, role, is_email_verified, is_mobile_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Pratiksha", # name
        username,
        email,
        mobile,
        generate_password_hash(password),
        "admin",
        1, # is_email_verified
        1  # is_mobile_verified
    ))

    conn.commit()
    print("✅ Admin created successfully!")
    print("Username:", username)
    print("Password:", password)

conn.close()