import sqlite3

conn = sqlite3.connect('myproject.db')
c = conn.cursor()

# Jar column NULL asel tar 0 kar
c.execute("UPDATE users SET is_blocked=0 WHERE is_blocked IS NULL")
c.execute("UPDATE users SET is_email_verified=0 WHERE is_email_verified IS NULL")
c.execute("UPDATE users SET is_mobile_verified=0 WHERE is_mobile_verified IS NULL")
c.execute("UPDATE users SET trust_score=100 WHERE trust_score IS NULL")

# Admin la verify kar
c.execute("UPDATE users SET is_email_verified=1, is_mobile_verified=1, is_blocked=0, role='admin' WHERE username='Pratiksha Jadhav' OR email='pratikshaj1113@gmail.com'")

print(f"Fixed {c.rowcount} users")
conn.commit()
conn.close()
print("✅ DB Fixed")