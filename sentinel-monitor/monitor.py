import subprocess
import time
import json
import re
from mqtt_publisher import MqttPublisher


class WifiMonitor:
    def scan(self):
        # Usiamo 'iw' invece di 'nmcli' perché è nativo e leggero su RPi Lite
        # NOTA: Richiede permessi sudo o configurazione sudoers
        cmd = ['sudo', 'iw', 'dev', 'wlan0', 'scan']

        try:
            # Eseguiamo il comando
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print("[MONITOR] ERRORE iw:", result.stderr)
                return []

            networks = []
            current_net = {}

            # Parsing dell'output di iw riga per riga
            for line in result.stdout.splitlines():
                line = line.strip()

                # Inizio di una nuova rete (BSS)
                if line.startswith("BSS "):
                    # Se c'è una rete precedente salvata, aggiungila alla lista
                    if current_net:
                        # Gestione reti nascoste (SSID vuoto)
                        if "ssid" not in current_net:
                            current_net["ssid"] = "--Hidden--"
                        networks.append(current_net)

                    # Estrae il BSSID (MAC Address) rimuovendo '(on wlan0)' se presente
                    bssid_raw = line.split('(')[0].replace("BSS ", "").strip()

                    # Inizializza il nuovo oggetto rete
                    current_net = {
                        "bssid": bssid_raw,
                        "ssid": "",  # Default vuoto
                        "channel": 0,  # Default
                        "rssi": -100  # Default segnale basso
                    }

                # Estrazione SSID
                elif line.startswith("SSID: "):
                    # Prende tutto dopo "SSID: "
                    current_net["ssid"] = line.replace("SSID: ", "").strip()

                # Estrazione Segnale (es. "signal: -68.00 dBm")
                elif line.startswith("signal: "):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            # Prende il valore numerico (es. -68.00) convertito a intero
                            current_net["rssi"] = int(float(parts[1]))
                        except ValueError:
                            pass

                # Estrazione Canale (DS Parameter set) - 2.4GHz
                elif "DS Parameter set: channel" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        current_net["channel"] = int(parts[4])

                # Estrazione Canale (primary channel) - 5GHz
                elif "* primary channel:" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        current_net["channel"] = int(parts[3])

            # Aggiunge l'ultima rete trovata dopo la fine del loop
            if current_net:
                if "ssid" not in current_net:
                    current_net["ssid"] = "--Hidden--"
                networks.append(current_net)

            return networks

        except Exception as e:
            print("[MONITOR] Eccezione durante scansione:", e)
            return []


if __name__ == "__main__":
    # Assicurati che il broker sia attivo o gestisci l'errore di connessione nella classe MqttPublisher
    monitor = WifiMonitor()
    try:
        publisher = MqttPublisher(broker_host="localhost")
    except Exception as e:
        print(f"[ERROR] Impossibile connettersi a MQTT: {e}")
        exit(1)

    print("[MONITOR] Avvio scansione loop...")

    while True:
        nets = monitor.scan()

        snapshot = {
            "timestamp": time.time(),
            "networks": nets
        }

        # Stampa di debug formattata
        print(f"[MONITOR] Trovate {len(nets)} reti. Invio dati...")

        # Invio MQTT
        try:
            publisher.publish_event(snapshot)
            # Opzionale: stampa il JSON solo se serve debug approfondito
            # print(json.dumps(snapshot, indent=2))
        except Exception as e:
            print(f"[MONITOR] Errore invio MQTT: {e}")

        time.sleep(10)  # Attesa