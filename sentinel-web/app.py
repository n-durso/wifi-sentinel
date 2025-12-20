import os
import psycopg2
import json
from flask import Flask, render_template
from datetime import datetime

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
    snapshots = []
    stats = {"safe": 0, "alert": 0, "total": 0}
    
    if conn:
        try:
            cur = conn.cursor()
            
            # 1. Statistiche veloci
            cur.execute("SELECT COUNT(*) FROM wifi_snapshots")
            stats["total"] = cur.fetchone()[0]
            
            # 2. Preleviamo gli ultimi 20 scan ordinati per tempo (dal più recente)
            # Usiamo to_timestamp per convertire quel "numeraccio" in una data leggibile direttamente da SQL
            query = """
                SELECT 
                    to_timestamp(timestamp) as data_ora,
                    networks,
                    status,
                    score
                FROM wifi_snapshots 
                ORDER BY timestamp DESC 
                LIMIT 20;
            """
            cur.execute(query)
            rows = cur.fetchall()
            
            # Formattiamo i dati per l'HTML
            for row in rows:
                dt, net_json, status, score = row
                
                # Parsing del JSON delle reti se è una stringa, altrimenti lo usiamo così
                if isinstance(net_json, str):
                    networks = json.loads(net_json)
                else:
                    networks = net_json # Psycopg2 converte JSONB automaticamente in dict/list
                
                # Contiamo quante reti c'erano in quello scan
                net_count = len(networks) if isinstance(networks, list) else 0

                snapshots.append({
                    "time": dt.strftime("%H:%M:%S - %d/%m"), # Formattiamo l'ora
                    "net_count": net_count,
                    "status": status,
                    "score": score
                })
                
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Errore query: {e}")
    
    return render_template('index.html', snapshots=snapshots, stats=stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)