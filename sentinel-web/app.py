import os
import psycopg2
import json
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, Response

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
            
            # Statistiche
            cur.execute("SELECT COUNT(*) FROM wifi_snapshots")
            stats["total"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM wifi_snapshots WHERE status != 'SAFE'")
            stats["alert"] = cur.fetchone()[0]
            stats["safe"] = stats["total"] - stats["alert"]
            
            # Query Elenco ultimi 20 snapshot
            query = """
                SELECT 
                    id, 
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
                snap_id, dt, snapshot_blob, status, score, details = row
                
                # Gestione JSON per contare le reti
                if isinstance(snapshot_blob, str):
                    networks = json.loads(snapshot_blob)
                else:
                    networks = snapshot_blob
                
                net_count = len(networks) if isinstance(networks, list) else 0
                if details is None: details = ""

                snapshots_list.append({
                    "id": snap_id,
                    "time": dt.strftime("%H:%M:%S"),
                    "net_count": net_count,
                    "status": status,
                    "score": score,
                    "details": details 
                })
            
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[WEB] Errore query index: {e}")
    
    return render_template('index.html', snapshots=snapshots_list, stats=stats)

# --- PAGINA DI DETTAGLI ---
@app.route('/snapshot/<int:snapshot_id>')
def view_snapshot(snapshot_id):
    conn = get_db_connection()
    snapshot_data = None
    
    if conn:
        try:
            cur = conn.cursor()
            query = """
                SELECT 
                    to_timestamp(timestamp) as data_ora,
                    snapshot, 
                    status, 
                    score, 
                    details
                FROM wifi_snapshots 
                WHERE id = %s
            """
            cur.execute(query, (snapshot_id,))
            row = cur.fetchone()
            
            if row:
                dt, snapshot_blob, status, score, details = row
                
                if isinstance(snapshot_blob, str):
                    networks = json.loads(snapshot_blob)
                else:
                    networks = snapshot_blob
                
                snapshot_data = {
                    "time": dt.strftime("%H:%M:%S - %d/%m/%Y"),
                    "status": status,
                    "score": score,
                    "details": details or "Nessun dettaglio rilevante",
                    "networks": networks 
                }
            
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[WEB] Errore query snapshot: {e}")

    if not snapshot_data:
        return redirect(url_for('index'))

    return render_template('snapshot.html', data=snapshot_data)

# --- FUNZIONE RESET ---
@app.route('/reset', methods=['POST'])
def reset_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("TRUNCATE TABLE wifi_snapshots RESTART IDENTITY;")
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[WEB] Errore reset: {e}")
    return redirect(url_for('index'))

# -- ESPORTA CSV ---
@app.route('/download_report')
def download_report():
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
    
    # Creazione CSV in memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Intestazione del CSV
    writer.writerow(['ID', 'Data e Ora', 'Stato', 'Score', 'Dettagli', 'Numero Reti'])
    
    try:
        cur = conn.cursor()
        query = """
            SELECT id, to_timestamp(timestamp), status, score, details, snapshot
            FROM wifi_snapshots 
            ORDER BY timestamp DESC
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        for row in rows:
            snap_id, dt, status, score, details, snapshot_blob = row
            
            # Calcolo numero reti
            if isinstance(snapshot_blob, str):
                networks = json.loads(snapshot_blob)
            else:
                networks = snapshot_blob
            net_count = len(networks) if isinstance(networks, list) else 0
            
            # Scrittura riga CSV
            writer.writerow([
                snap_id, 
                dt.strftime("%Y-%m-%d %H:%M:%S"), 
                status, 
                score, 
                details or "", 
                net_count
            ])
            
        cur.close()
        conn.close()
        
        # Creiamo la risposta come file scaricabile
        output.seek(0)
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=sentinel_report.csv"}
        )

    except Exception as e:
        print(f"[WEB] Errore export: {e}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)