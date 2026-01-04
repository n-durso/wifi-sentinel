import psycopg2
import os
from strategies.whitelist_check import WhitelistStrategy

class Evaluator:
    def __init__(self):
        self.strategies = [WhitelistStrategy()]

    def get_whitelist_from_db(self):
        
        whitelist_dict = {}
        conn = None
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"), 
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"), 
                password=os.getenv("DB_PASSWORD"),
                port=int(os.getenv("DB_PORT", 5432))
            )
            cur = conn.cursor()
            
            cur.execute("SELECT ssid, bssid, channel FROM wifi_whitelist")
            rows = cur.fetchall()
            
            for row in rows:
                ssid, bssid, channel = row

                if bssid: bssid = bssid.upper()
                
                if ssid not in whitelist_dict:
                    whitelist_dict[ssid] = {'bssids': [], 'channels': []}
                
                if bssid and bssid not in whitelist_dict[ssid]['bssids']:
                    whitelist_dict[ssid]['bssids'].append(bssid)
                
                if channel and channel not in whitelist_dict[ssid]['channels']:
                    whitelist_dict[ssid]['channels'].append(channel)

            cur.close()
        except Exception as e:
            print(f"[EVALUATOR] ❌ Errore lettura whitelist DB: {e}")
        finally:
            if conn: conn.close()
        
        return whitelist_dict

    def analyze(self, networks):
        """Metodo principale chiamato ogni volta che arrivano nuovi dati dallo sniffer"""
        
        current_whitelist = self.get_whitelist_from_db()
        
        max_score = 0.0
        final_status = "SAFE"
        all_details = []

        if not networks:
            return "SAFE", 0.0, None

        # Analizza ogni rete rilevata
        for net in networks:
            if 'bssid' in net: net['bssid'] = net['bssid'].upper()

            for strategy in self.strategies:
                result = strategy.analyze(net, current_whitelist)
                
                if result:
                    # Abbiamo trovato una minaccia!
                    all_details.append(result['message'])
                    print(f"[EVALUATOR] ⚠️ {result['message']}") # Log console per debug
                    
                    # Se il rischio è più alto di quello trovato finora, aggiorniamo lo status generale
                    if result['score'] > max_score:
                        max_score = result['score']
                        final_status = result['type']

        # Uniamo i messaggi per il DB
        details_str = " | ".join(all_details) if all_details else None
        
        return final_status, max_score, details_str