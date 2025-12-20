import os
import psycopg2

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )

def save_snapshot(timestamp, networks_json, status, score, details):
    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        query = """
        INSERT INTO wifi_snapshots (timestamp, snapshot, status, score, details)
        VALUES (%s, %s, %s, %s, %s)
        """

        cur.execute(query, (timestamp, networks_json, status, score, details))

        conn.commit()
    except Exception as e:
        print("[DB] Errore nel salvataggio:", e)
    finally:
        if cur: cur.close()
        if conn: conn.close()

