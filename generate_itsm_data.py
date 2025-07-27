import sqlite3
import random
from datetime import datetime, timedelta

# Known errors and workarounds
known_errors = [
    ("CMS not responding", "Restart CMS service"),
    ("CMS timeout", "Increase CMS timeout setting"),
    ("CMS authentication failed", "Re-enter CMS credentials"),
    ("CMS database locked", "Unlock CMS database"),
    ("CMS returns invalid data", "Validate CMS data format"),
    ("CMS service unavailable", "Check CMS server status"),
    ("CMS API rate limit exceeded", "Wait and retry later"),
    ("CMS returns 500 error", "Contact CMS admin"),
    ("CMS returns 404 error", "Verify CMS endpoint URL"),
    ("CMS returns 403 error", "Check CMS access permissions"),
    ("Printer out of paper", "Refill paper tray"),
    ("Printer jammed", "Clear printer jam"),
    ("Printer offline", "Power on printer"),
    ("Printer driver error", "Reinstall printer driver"),
    ("Printer queue full", "Clear print queue"),
]

unknown_errors = [
    "Unexpected barcode format",
    "Label size mismatch",
    "Network cable unplugged",
    "Power supply interrupted",
    "Firmware update required",
    "Device overheating",
    "Memory overflow",
    "Unrecognized printer model",
    "Print head failure",
    "Spooler service crashed",
    "Data packet loss",
    "Security policy violation",
    "Disk space full",
    "User permission denied",
    "Unknown system error",
]

success_reasons = [
    "Label printed successfully",
    "Order processed without errors",
    "Container label generated",
    "Print job completed",
    "No issues detected",
]

# Connect to SQLite
conn = sqlite3.connect("itsm_synthetic_data.db")
c = conn.cursor()

# Create table
c.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    container_id TEXT,
    timestamp TEXT,
    error_response TEXT,
    response_reason TEXT,
    workaround TEXT
)
""")

# Generate synthetic data
total_records = 500
failure_count = int(total_records * 0.7)
success_count = total_records - failure_count
known_error_count = failure_count // 2
unknown_error_count = failure_count - known_error_count

records = []

# Helper to generate random timestamp within last 60 days
def random_timestamp():
    now = datetime.now()
    delta = timedelta(days=random.randint(0, 60), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return (now - delta).strftime("%Y-%m-%dT%H:%M:%S")

# Generate known error failures
for i in range(known_error_count):
    order_id = f"ORD{str(random.randint(1000, 9999)).zfill(4)}"
    container_id = f"CONT{str(random.randint(1000, 9999)).zfill(4)}"
    timestamp = random_timestamp()
    error, workaround = random.choice(known_errors)
    records.append((order_id, container_id, timestamp, "failure", error, workaround))

# Generate unknown error failures
for i in range(unknown_error_count):
    order_id = f"ORD{str(random.randint(1000, 9999)).zfill(4)}"
    container_id = f"CONT{str(random.randint(1000, 9999)).zfill(4)}"
    timestamp = random_timestamp()
    error = random.choice(unknown_errors)
    records.append((order_id, container_id, timestamp, "failure", error, None))

# Generate successes
for i in range(success_count):
    order_id = f"ORD{str(random.randint(1000, 9999)).zfill(4)}"
    container_id = f"CONT{str(random.randint(1000, 9999)).zfill(4)}"
    timestamp = random_timestamp()
    reason = random.choice(success_reasons)
    records.append((order_id, container_id, timestamp, "success", reason, None))

# Shuffle records for randomness
random.shuffle(records)

# Insert into DB
c.executemany("""
INSERT INTO incidents (order_id, container_id, timestamp, error_response, response_reason, workaround)
VALUES (?, ?, ?, ?, ?, ?)
""", records)

conn.commit()
conn.close()

print("Synthetic data generation complete. 500 records inserted.")
