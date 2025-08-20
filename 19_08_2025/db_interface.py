import os
from typing import Optional 
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

def connect_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


def get_latest_log(order_id=None, container_id=None):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    if order_id:
        cursor.execute("SELECT * FROM cms_logs WHERE order_id = %s ORDER BY response_timestamp DESC LIMIT 1", (order_id,))
    elif container_id:
        cursor.execute("SELECT * FROM cms_logs WHERE container_id = %s ORDER BY response_timestamp DESC LIMIT 1", (container_id,))
    else:
        return None

    print("ORDER ID:", order_id)
    print("CONTAINER ID:", container_id)

    result = cursor.fetchone()
    conn.close()
    return result

def find_known_failure_match(response_payload):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT pattern, workaround, failure_type  FROM known_failures")
    failures = cursor.fetchall()
    conn.close()

    # Handle null payload first
    if response_payload is None:
        for failure in failures:
            if failure["pattern"] is None:  # Matches NULL pattern in DB
                return failure
        return None

    # Normal matching for non-null payload
    for failure in failures:
        if failure["pattern"] is None:
            continue  # Skip null patterns for non-null payloads

        cleaned_pattern = failure["pattern"].replace('%', '').strip().lower()
        if cleaned_pattern in response_payload.lower():
            return failure

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
        SET status = %s
        WHERE incident_id = %s
    """, (status, incident_id))  # ✅ Removed updated_at

    conn.commit()
    conn.close()


def get_workaround_by_label(label):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT workaround FROM known_failures WHERE label = %s", (label,))
    row = cursor.fetchone()
    conn.close()

    return row['workaround'] if row else None


# --- ADD in db_interface.py ---

def get_incident_by_id(incident_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM incident_logs WHERE incident_id = %s LIMIT 1", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def order_exists(order_id):
    if not order_id:
        return False
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM cms_logs WHERE order_id = %s LIMIT 1", (order_id,))
    found = cursor.fetchone() is not None
    conn.close()
    return found

def container_exists(container_id):
    if not container_id:
        return False
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM cms_logs WHERE container_id = %s LIMIT 1", (container_id,))
    found = cursor.fetchone() is not None
    conn.close()
    return found

def get_latest_incident_by_order_or_container(order_id=None, container_id=None):
    if not order_id and not container_id:
        return None
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    if order_id and container_id:
        cursor.execute("""
            SELECT * FROM incident_logs
            WHERE order_id = %s OR container_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (order_id, container_id))
    elif order_id:
        cursor.execute("""
            SELECT * FROM incident_logs
            WHERE order_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (order_id,))
    else:
        cursor.execute("""
            SELECT * FROM incident_logs
            WHERE container_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (container_id,))
    row = cursor.fetchone()
    conn.close()
    return row



def get_all_incidents_by_order_or_container(order_id: Optional[str] = None, container_id: Optional[str] = None):
    """
    Returns a list of all incidents matching the given order_id or container_id.
    Each incident is a dict with keys: incident_id, status, order_id, container_id, etc.
    """

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM incident_logs WHERE 1=1"
    params = []

    if order_id:
        query += " AND order_id = %s"
        params.append(order_id)
    if container_id:
        query += " AND container_id = %s"
        params.append(container_id)

    query += " ORDER BY created_at DESC"  # Or incident_id DESC

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    # Convert rows to list of dicts
    incidents = [dict(row) for row in rows]
    return incidents
