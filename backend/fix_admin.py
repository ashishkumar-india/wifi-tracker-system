"""Script to setup admin user with proper bcrypt hash."""
import sys
sys.path.insert(0, '.')

import bcrypt
from sqlalchemy import create_engine, text

# Generate hash
password = "admin123"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
print(f"Generated hash: {hashed}")

# Update database
engine = create_engine("mysql+pymysql://root:@localhost:3306/wifi_tracker")
with engine.connect() as conn:
    # First check if user exists
    result = conn.execute(text("SELECT id, password_hash FROM users WHERE username='admin'"))
    row = result.fetchone()
    if row:
        print(f"Current hash in DB: {row[1]}")
        conn.execute(text(f"UPDATE users SET password_hash=:hash WHERE username='admin'"), {"hash": hashed})
        conn.commit()
        print("Password updated successfully!")
    else:
        print("Admin user not found!")
