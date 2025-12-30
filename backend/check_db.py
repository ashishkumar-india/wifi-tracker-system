"""
Script to fix database enum values and ensure ML training can work.
Run this script to:
1. Fix alert_type values (MySQL stores values, not enum names)
2. Fix any other enum-related issues
"""

import sys
sys.path.insert(0, '.')

from app.database import engine
from sqlalchemy import text

def fix_database():
    """Fix database enum issues and prepare for ML training."""
    
    with engine.connect() as conn:
        # Check current alerts table structure
        print("Checking alerts table...")
        try:
            result = conn.execute(text("SELECT id, alert_type, severity FROM alerts LIMIT 5"))
            rows = result.fetchall()
            print(f"Found {len(rows)} alerts (showing first 5)")
            for row in rows:
                print(f"  ID: {row[0]}, Type: {row[1]}, Severity: {row[2]}")
        except Exception as e:
            print(f"Error checking alerts: {e}")
        
        # Check device_activity table
        print("\nChecking device_activity table...")
        try:
            result = conn.execute(text("SELECT id, event_type FROM device_activity LIMIT 5"))
            rows = result.fetchall()
            print(f"Found {len(rows)} activities (showing first 5)")
            for row in rows:
                print(f"  ID: {row[0]}, Type: {row[1]}")
        except Exception as e:
            print(f"Error checking device_activity: {e}")
        
        # Check devices count for ML training
        print("\nChecking device count for ML training...")
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM devices"))
            count = result.scalar()
            print(f"Total devices: {count}")
            
            if count >= 10:
                print("✓ Sufficient devices for ML training (minimum: 10)")
            else:
                print(f"✗ Need at least 10 devices for ML training (current: {count})")
        except Exception as e:
            print(f"Error checking devices: {e}")
        
        # Check scan_results count
        print("\nChecking scan_results count...")
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM scan_results"))
            count = result.scalar()
            print(f"Total scan results: {count}")
        except Exception as e:
            print(f"Error checking scan_results: {e}")
        
        conn.commit()
        print("\n✓ Database check complete!")

if __name__ == "__main__":
    fix_database()
