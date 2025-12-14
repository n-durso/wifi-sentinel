import subprocess
import time
import json
import csv
import sys
from mqtt_publisher import MqttPublisher

class WifiMonitor:
    def scan(self):
        # --rescan yes serve per forzare una nuova scansione e non usare cache
        cmd = ['nmcli', '-t', '-f', 'SSID,BSSID,CHAN,SIGNAL', 'dev', 'wifi', 'list', '--rescan', 'yes']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[MONITOR] ERRORE nmcli: {result.stderr}", file=sys.stderr)
                return []

            networks = []
            
            reader = csv.reader(result.stdout.splitlines(), delimiter=':', escapechar='\\')

            for row in reader:
                # row sarà una lista tipo: ['SKYWIFI', 'D4:F0:4A:1C:57:CD', '6', '100']
                try:
                    if len(row) < 4:
                        continue

                    ssid = row[0]
                    bssid = row[1]
                    chan = row[2]
                    signal = row[3]

                    # Ignora reti senza SSID (spesso reti nascoste)
                    if not ssid:
                        continue

                    networks.append({
                        "ssid": ssid,
                        "bssid": bssid,
                        "channel": int(chan),
                        "rssi": int(signal)
                    })

                except ValueError:
                    print(f"[MONITOR] Errore conversione dati riga: {row}")
                except Exception as e:
                    print(f"[MONITOR] Errore generico riga: {row} -> {e}")

            return networks

        except Exception as e:
            print(f"[MONITOR] Eccezione critica durante la scansione: {e}")
            return []

if __name__ == "__main__":
    monitor = WifiMonitor()
    publisher = MqttPublisher()

    print("[MONITOR] Avvio scansione ciclica...")

    while True:
        start_time = time.time()
        nets = monitor.scan()

        if nets:
            snapshot = {
                "timestamp": start_time,
                "networks": nets
            }
            
            # Pubblica
            publisher.publish_event(snapshot)
            
            # Log con solo il numero di reti per non avere troppo output
            print(f"[MONITOR] Inviato snapshot: {len(nets)} reti rilevate.")
        else:
            print("[MONITOR] Nessuna rete rilevata o errore scansione.")

        time.sleep(10)