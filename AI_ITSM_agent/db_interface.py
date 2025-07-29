import os
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

def connect_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB")
    )


def get_latest_log(order_id=None, container_id=None):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    if order_id:
        cursor.execute("SELECT * FROM cms_logs WHERE order_id = %s ORDER BY response_ts DESC LIMIT 1", (order_id,))
    elif container_id:
        cursor.execute("SELECT * FROM cms_logs WHERE container_id = %s ORDER BY response_ts DESC LIMIT 1", (container_id,))
    else:
        return None

    result = cursor.fetchone()
    conn.close()
    return result


def find_known_failure_match(response_payload):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT label, pattern, workaround FROM known_failures")
    failures = cursor.fetchall()

    for failure in failures:
        if failure["pattern"].lower() in response_payload.lower():
            return failure

    conn.close()
    return None


def log_incident(order_id, container_id, issue_summary):
    conn = connect_db()
    cursor = conn.cursor()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    incident_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    cursor.execute("""
        INSERT INTO incident_logs (incident_id, order_id, container_id, issue_summary, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (incident_id, order_id, container_id, issue_summary, 'In Progress', timestamp))

    conn.commit()
    conn.close()

    return incident_id


def update_incident_status(incident_id, status):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE incident_logs
        SET status = %s, updated_at = %s
        WHERE incident_id = %s
    """, (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), incident_id))

    conn.commit()
    conn.close()


def get_workaround_by_label(label):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT workaround FROM known_failures WHERE label = %s", (label,))
    row = cursor.fetchone()
    conn.close()

    return row['workaround'] if row else None
