import os
import psycopg2
from flask import Flask, render_template

app = Flask(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except Exception as e:
        print(f"[WEB] ❌ Errore connessione DB: {e}")
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    count = 0
    status = "Offline 🔴"
    
    if conn:
        try:
            cur = conn.cursor()
            # Contiamo quanti snapshot abbiamo salvato finora
            cur.execute('SELECT COUNT(*) FROM wifi_snapshots;')
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            status = "Online 🟢"
        except Exception as e:
            status = f"Errore Query: {e}"
    
    return render_template('index.html', count=count, status=status)

if __name__ == '__main__':
    # Debug=True permette di vedere gli errori nel browser
    app.run(debug=True, host='0.0.0.0', port=5000)