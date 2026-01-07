import os
import psycopg2
import json
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, Response, flash
import secrets

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Se uno non loggato prova ad accedere a pagine protette, viene reindirizzato qui

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
        print(f"[WEB] Errore connessione DB: {e}")
        return None

# Classe Utente per Flask-Login
class User(UserMixin):
    def __init__(self, id, username, telegram_chat_id, is_admin):
        self.id = id
        self.username = username
        self.telegram_chat_id = telegram_chat_id
        self.is_admin = is_admin
    
# Loader utente per Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = None
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, username, telegram_chat_id, is_admin FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                user = User(id=row[0], username=row[1], telegram_chat_id=row[2], is_admin=row[3])
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[WEB] Errore caricamento utente: {e}")
    return user

# Rotte autenticazione (Login, Registrazione, Logout)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password, telegram_chat_id, is_admin FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        conn.close()

        # Verifica credenziali
        if row and check_password_hash(row[2], password):
            user = User(id=row[0], username=row[1], telegram_chat_id=row[3], is_admin=row[4])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Credenziali non valide", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_password)
            )
            conn.commit()
            
            flash("Utente registrato con successo!", "success")
        except Exception as e:
            print(f"[WEB] Errore registrazione utente: {e}")
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sei stato disconnesso.", "info")
    return redirect(url_for('login'))

@app.route('/')
@login_required
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

# --- INTEGRAZIONE TELEGRAM ---
@app.route('/connect_telegram')
@login_required
def connect_telegram():
    #Genera un token sicuro
    token = secrets.token_urlsafe(16)
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Salva il token nel DB che serve al bot per associare l'utente
            cur.execute(
                "UPDATE users SET verification_token = %s WHERE id = %s",
                (token, current_user.id)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            # Reindirizza su Telegram
            # Quando viene cliccato "Avvia" nel bot, riceverà "/start <token>
            bot_name = "Sentinel_sapd_bot"
            return redirect(f"https://t.me/{bot_name}?start={token}")
            
        except Exception as e:
            print(f"[WEB] Errore Telegram Token: {e}")
            flash("Errore durante la connessione a Telegram.", "danger")
            
    return redirect(url_for('index'))

# --- PAGINA DI DETTAGLI ---
@app.route('/snapshot/<int:snapshot_id>')
@login_required
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
@login_required
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
@login_required
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

# --- AGGIUNTA RAPIDA WHITELIST ---
@app.route('/whitelist/quick_add', methods=['POST'])
@login_required
def quick_add_whitelist():
    # Solo admin possono accedere
    if not current_user.is_admin:
        flash("Accesso negato: solo amministratori.", "danger")
        return redirect(request.referrer or url_for('index'))

    # Recupera i dati dal form nascosto
    ssid = request.form.get('ssid', '')
    bssid = request.form.get('bssid', '').strip().upper()
    channel = request.form.get('channel', '')

    if not ssid or not bssid:
        flash("SSID e BSSID sono obbligatori.", "danger")
        return redirect(request.referrer)
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Controllo se la rete è già in whitelist
            cur.execute(
                "SELECT id, bssid FROM wifi_whitelist WHERE ssid = %s",
                (ssid,)
            )
            existing = cur.fetchall()

            # Se esiste, controlliamo se il MAC è uguale
            is_duplicate = False
            for row in existing:
                if row[1] == bssid:
                    is_duplicate = True
                    break

            if is_duplicate:
                flash(f"La rete '{ssid}' con MAC {bssid} è già in whitelist.", "warning")
            else:
                # Inserisce la nuova rete in whitelist
                cur.execute(
                    "INSERT INTO wifi_whitelist (ssid, bssid, channel, description) VALUES (%s, %s, %s, %s)",
                    (ssid, bssid, channel, "Aggiunta rapida da Snaphsot")
                )
                conn.commit()
                flash(f"Rete '{ssid}' aggiunta alla whitelist.", "success")

            cur.close()
            conn.close()
        except Exception as e:
            print(f"[WEB] Errore aggiunta rapida whitelist: {e}")
            flash("Errore durante l'aggiunta alla whitelist.", "danger")

    return redirect(request.referrer)

# --- GESTIONE WHITELIST ---
@app.route('/whitelist', methods=['GET', 'POST'])
@login_required
def manage_whitelist():
    # Solo admin possono accedere
    if not current_user.is_admin:
        flash("Accesso negato: solo amministratori.", "danger")
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        return "Errore connessione DB", 500

    # Gestione richieste POST (Aggiungi/Rimuovi rete)
    if request.method == 'POST':
        #1. Aggiungi rete
        if 'add' in request.form:
            ssid = request.form.get('ssid')
            bssid = request.form['bssid'].strip().upper()
            channel = request.form.get('channel')
            desc = request.form.get('description', '')

            try:
                cur = conn.cursor()
                # Controllo duplicati
                cur.execute("SELECT id FROM wifi_whitelist WHERE ssid = %s AND bssid = %s", (ssid, bssid))
                duplicate = cur.fetchone()

                if duplicate:
                    flash(f"Attenzione: La rete '{ssid}' con MAC {bssid} è già presente nella whitelist!", "warning")
                else:
                    cur.execute(
                        "INSERT INTO wifi_whitelist (ssid, bssid, channel, description) VALUES (%s, %s, %s, %s)",
                        (ssid, bssid, channel, desc)
                    )
                    conn.commit()
                    flash(f"Rete '{ssid}' aggiunta correttamente alla whitelist.", "success")
                
                cur.close()
            except Exception as e:
                print(f"[WEB] Errore aggiunta whitelist: {e}")
                flash("Errore interno durante il salvataggio.", "danger")
        
        #2. Rimuovi rete esistente
        elif 'delete' in request.form:
            try:
                item_id = request.form['item_id']
                cur = conn.cursor()
                cur.execute("DELETE FROM wifi_whitelist WHERE id = %s", (item_id,))
                conn.commit()
                cur.close()
                flash("Rete rimossa dalla whitelist.", "info")
            except Exception as e:
                print(f"[WEB] Errore rimozione whitelist: {e}")
                flash("Errore durante la rimozione.", "danger")
        
        return redirect(url_for('manage_whitelist'))

    # Gestione richieste GET (Visualizza whitelist)
    cur = conn.cursor()
    cur.execute("SELECT id, ssid, bssid, channel, description FROM wifi_whitelist ORDER BY ssid ASC")
    whitelist_items = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('whitelist.html', items=whitelist_items)


# --- INIZIALIZZAZIONE DEL DATABASE ---
def init_db():
    # Crea le tabelle e l'utente admin se non esistono.
    print("[WEB] Verifica inizializzazione Database...")
    conn = get_db_connection()
    if not conn:
        print("[WEB] Impossibile connettersi al DB per l'init.")
        return

    try:
        cur = conn.cursor()

        # CREAZIONE TABELLE (Se non esistono)
        # Tabella Users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                telegram_chat_id VARCHAR(50),
                verification_token VARCHAR(50),
                is_admin BOOLEAN DEFAULT FALSE
            );
        """)

        # Tabella Snapshots
        cur.execute("""
            CREATE TABLE IF NOT EXISTS wifi_snapshots (
                id SERIAL PRIMARY KEY,
                timestamp FLOAT NOT NULL,
                snapshot JSONB,
                status VARCHAR(20),
                score FLOAT,
                details TEXT
            );
        """)

        # Tabella Whitelist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS wifi_whitelist (
                id SERIAL PRIMARY KEY,
                ssid VARCHAR(100) NOT NULL,
                bssid VARCHAR(17) NOT NULL,
                channel INTEGER,
                description TEXT,
                CONSTRAINT unique_ssid_bssid UNIQUE (ssid, bssid)
            );
        """)

        # CREAZIONE ADMIN DI DEFAULT
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            print("[WEB] Primo avvio rilevato: Creo utente 'admin'...")
            # Genera hash della password "admin"
            hashed_pw = generate_password_hash("admin")
            cur.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",
                ('admin', hashed_pw, True)
            )
            print("[WEB] Utente 'admin' creato (Password: admin).")
        else:
            print("[WEB] Utente admin già presente.")

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"[WEB] Errore durante init_db: {e}")

if __name__ == '__main__':

    # Inizializzo DB prima di partire
    init_db()

    app.run(debug=True, host='0.0.0.0', port=5000)