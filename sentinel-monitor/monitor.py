import subprocess
import time
import json
from mqtt_publisher import MqttPublisher

class WifiMonitor:
    def scan(self):
        cmd = ['nmcli', '-t', '-f', 'SSID,BSSID,CHAN,SIGNAL', 'dev', 'wifi']

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print("[MONITOR] ERRORE nmcli:", result.stderr)
                return []

            networks = []
            for line in result.stdout.splitlines():
                try:
                    parts = line.split(":")

                    if len(parts) < 4:
                        print("[MONITOR] Riga ignorata (troppo corta):", line)
                        continue

                    ssid = parts[0]
                    signal = parts[-1]
                    chan = parts[-2]

                    # ricostruzione robusta del BSSID
                    bssid = ":".join(parts[1:-2])

                    networks.append({
                        "ssid": ssid,
                        "bssid": bssid,
                        "channel": int(chan),
                        "rssi": int(signal)
                    })

                except Exception as e:
                    print("[MONITOR] Errore parsing:", line, e)


            return networks

        except Exception as e:
            print("[MONITOR] Eccezione:", e)
            return []

if __name__ == "__main__":
    monitor = WifiMonitor()
    publisher = MqttPublisher()

    while True:
        nets = monitor.scan()

        snapshot = {
            "timestamp": time.time(),
            "networks": nets
        }

        print("[MONITOR] Payload inviato:", json.dumps(snapshot, indent=2))


        publisher.publish_event(snapshot)
        print("[MONITOR] Inviato snapshot con", len(nets), "reti")

        time.sleep(10) # Attendi 10 secondi prima della prossima scansione
