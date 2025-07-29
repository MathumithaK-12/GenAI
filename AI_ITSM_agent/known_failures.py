import os
import mysql.connector
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'port': int(os.getenv("DB_PORT", 3306)),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}

# Known failure patterns and workarounds
known_failures = [
    {
        "failure_type": "Invalid Postcode",
        "pattern": "%postcode is not valid%",
        "workaround": "Please verify the delivery postcode and ensure it is serviceable."
    },
    {
        "failure_type": "Hazmat Issue",
        "pattern": "%Hazmat ID/Class%",
        "workaround": "Check SKU hazmat ID and classification and remove restricted items before retrying."
    },
    {
        "failure_type": "Null Payload",
        "pattern": "",
        "workaround": "Kindly try repacking the container into a new container."
    }
]

def insert_known_failures():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS known_failures (
                id INT AUTO_INCREMENT PRIMARY KEY,
                failure_type VARCHAR(100),
                pattern TEXT,
                workaround TEXT
            )
        """)

        # Insert known failure records
        for error in known_failures:
            cursor.execute("""
                INSERT INTO known_failures (failure_type, pattern, workaround)
                VALUES (%s, %s, %s)
            """, (error["failure_type"], error["pattern"], error["workaround"]))

        conn.commit()
        print(f"{len(known_failures)} known failures inserted.")

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    insert_known_failures()
