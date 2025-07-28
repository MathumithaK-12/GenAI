import os
import random
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MySQL DB Config from .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Valid and invalid postcodes
VALID_POSTCODES = ["560001", "110001", "400001", "700001"]
INVALID_POSTCODES = ["000000", "999999", "ABCDE1", "123", "XYZ999"]

# XML builders
def build_request_xml(order_id, container_id, sku_id, qty, postcode):
    return f"""
    <Request>
        <OrderID>{order_id}</OrderID>
        <ContainerID>{container_id}</ContainerID>
        <SKU>{sku_id}</SKU>
        <Quantity>{qty}</Quantity>
        <Postcode>{postcode}</Postcode>
    </Request>
    """.strip()

def build_response_xml(status, failure_type=None):
    if status == "success":
        carrier = random.choice(["FedEx", "UPS", "DHL", "BlueDart"])
        return f"<Response><Carrier>{carrier} allocated to order successfully. Label generated.</Carrier></Response>"
    else:
        if failure_type == "Null Payload":
            return ""
        elif failure_type == "Invalid Postcode":
            return "<Response><Error>Selected postcode is not valid/deliverable</Error></Response>"
        elif failure_type == "Hazmat Issue":
            return "<Response><Error>Issue with Hazmat ID/Class associated with the SKU</Error></Response>"

# Generate synthetic records
def generate_cms_logs(num_records=500):
    records = []
    base_time = datetime.now()

    for i in range(num_records):
        order_id = f"ORD{random.randint(10000,99999)}"
        container_id = f"CONT{random.randint(1000,9999)}"
        sku_id = f"SKU{random.randint(100,999)}"
        qty = random.randint(1, 10)

        request_time = base_time - timedelta(seconds=random.randint(30, 300))
        response_time = request_time + timedelta(seconds=random.randint(1, 5))

        # Determine status and failure_type - 60% success, 40% failure
        if i < int(num_records * 0.6):
            status = "success"
            failure_type = None
            postcode = random.choice(VALID_POSTCODES)
        else:
            status = "failure"
            failure_type = random.choice(["Invalid Postcode", "Null Payload", "Hazmat Issue"])
            postcode = (
                random.choice(INVALID_POSTCODES) if failure_type == "Invalid Postcode"
                else random.choice(VALID_POSTCODES)
            )

        request_xml = build_request_xml(order_id, container_id, sku_id, qty, postcode)
        response_xml = build_response_xml(status, failure_type)

        records.append((
            order_id,
            container_id,
            request_time.strftime("%Y-%m-%d %H:%M:%S"),
            response_time.strftime("%Y-%m-%d %H:%M:%S"),
            status,
            request_xml,
            response_xml
        ))
    #Shuffle the records to mix success and failure
    random.shuffle(records)
    return records

# Insert into MySQL
def insert_into_mysql(records):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cms_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id VARCHAR(20),
                container_id VARCHAR(20),
                request_timestamp DATETIME,
                response_timestamp DATETIME,
                status VARCHAR(10),
                request_xml TEXT,
                response_xml TEXT
            )
        """)

        insert_query = """
            INSERT INTO cms_logs (
                order_id, container_id, request_timestamp,
                response_timestamp, status, request_xml, response_xml
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, records)
        conn.commit()

        print(f"{cursor.rowcount} records inserted into cms_logs table.")
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")

# Main entry
if __name__ == "__main__":
    synthetic_data = generate_cms_logs(500)
    insert_into_mysql(synthetic_data)
