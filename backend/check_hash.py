"""Verify password hash in database."""
import sys
sys.path.insert(0, '.')

import bcrypt
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://root:@localhost:3306/wifi_tracker")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, username, password_hash FROM users WHERE username='admin'"))
    row = result.fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"Username: {row[1]}")
        print(f"Hash (len={len(row[2])}): {row[2]}")
        
        # Test verification
        password = "admin123"
        try:
            is_valid = bcrypt.checkpw(password.encode('utf-8'), row[2].encode('utf-8'))
            print(f"Password valid: {is_valid}")
        except Exception as e:
            print(f"Verification error: {e}")
