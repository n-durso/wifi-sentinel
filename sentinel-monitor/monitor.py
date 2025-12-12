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
                    ssid, bssid, chan, signal = line.split(":")
                    networks.append({
                        "ssid": ssid,
                        "bssid": bssid,
                        "channel": int(chan),
                        "rssi": int(signal)
                    })
                except:
                    pass

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

        publisher.publish_event(snapshot)
        print("[MONITOR] Inviato snapshot con", len(nets), "reti")

        time.sleep(5)
