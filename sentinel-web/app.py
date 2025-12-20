import os
import psycopg2
import json
from flask import Flask, render_template, request, redirect, url_for

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
    snapshots_list = []
    stats = {"safe": 0, "alert": 0, "total": 0}
    
    if conn:
        try:
            cur = conn.cursor()
            
            # 1. Statistiche totali
            cur.execute("SELECT COUNT(*) FROM wifi_snapshots")
            stats["total"] = cur.fetchone()[0]
            
            # Statistiche allarmi escludendo quelli SAFE
            cur.execute("SELECT COUNT(*) FROM wifi_snapshots WHERE status != 'SAFE'")
            stats["alert"] = cur.fetchone()[0]
            stats["safe"] = stats["total"] - stats["alert"]
            
            # 2. Preleva i dati degli ultimi 20 snapshot
            query = """
                SELECT 
                    to_timestamp(timestamp) as data_ora,
                    snapshot,
                    status, 
                    score,
                    details
                FROM wifi_snapshots 
                ORDER BY timestamp DESC 
                LIMIT 20;
            """
            cur.execute(query)
            rows = cur.fetchall()
            
            for row in rows:
                
                dt, snapshot_blob, status, score, details = row
                
                # Gestione JSON per contare le reti
                if isinstance(snapshot_blob, str):
                    networks = json.loads(snapshot_blob)
                else:
                    networks = snapshot_blob # Psycopg2 converte JSON automaticamente
                
                net_count = len(networks) if isinstance(networks, list) else 0
                
                # Se details è None mettiamo stringa vuota
                if details is None:
                    details = ""

                snapshots_list.append({
                    "time": dt.strftime("%H:%M:%S"),
                    "net_count": net_count,
                    "status": status,
                    "score": score,
                    "details": details 
                })
                
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[WEB] Errore query: {e}")
    
    return render_template('index.html', snapshots=snapshots_list, stats=stats)

@app.route('/reset', methods=['POST'])
def reset_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Cancella tutto e riavvia i contatori ID da 1
            cur.execute("TRUNCATE TABLE wifi_snapshots RESTART IDENTITY;")
            conn.commit()
            cur.close()
            conn.close()
            print("[WEB] Database resettato con successo.")
        except Exception as e:
            print(f"[WEB] Errore reset DB: {e}")

    # Ricarica la pagina principale pulita
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)