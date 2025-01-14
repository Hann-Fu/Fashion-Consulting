from dbutils.pooled_db import PooledDB
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
# Configuration for the connection pool
POOL = PooledDB(
    creator=pymysql,                  # The database module to use
    maxconnections=10,                # Maximum number of connections allowed
    mincached=2,                      # Minimum number of idle connections
    maxcached=10,                      # Maximum number of idle connections
    maxshared=3,                      # Maximum number of shared connections
    blocking=True,                    # Block when no connection is available
    maxusage=None,                    # Unlimited reuse of a single connection
    setsession=[],                    # List of SQL commands to prepare the session
    ping=1,                           # Check if connection is alive (1: whenever possible)
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    port=int(os.getenv('DB_PORT', 3306)),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor  # Optional: Return results as dictionaries
)


def get_connection():
    """
    Retrieve a connection from the pool.
    """
    return POOL.connection()

def execute_query(query:str, params=None) -> dict:
    """
    Execute a SELECT query and return the results.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        print(f"Error executing query: {e}")
        raise
    finally:
        conn.close()  # Returns the connection to the pool

def execute_non_query(query:str, params=None):
    """
    Execute an INSERT/UPDATE/DELETE query.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error executing non-query: {e}")
        raise
    finally:
        conn.close()  # Returns the connection to the pool

# Example Usage
# select_query = "SELECT * FROM users WHERE id = %s"
# user = execute_query(select_query, (1,))

# INSERT example
# insert_query = "INSERT INTO users (name, email) VALUES (%s, %s)"
# execute_non_query(insert_query, ("John Doe", "john@example.com"))
