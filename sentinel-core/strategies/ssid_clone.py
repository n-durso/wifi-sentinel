from strategies.base_strategy import Strategy
class SSIDCloneStrategy:
    def evaluate(self, event, history):
        alerts = []

        # scorre le reti presenti nello snapshot
        for net in event.get("networks", []):
            ssid = net.get("ssid")
            bssid = net.get("bssid")

            # controlla se in passato esiste stesso SSID ma BSSID diverso
            same_ssid = [
                h for h in history 
                for prev in h.get("networks", [])
                if prev["ssid"] == ssid and prev["bssid"] != bssid
            ]

            if same_ssid:
                alerts.append(f"SSID clone rilevato per {ssid}")

        return {
            "status": "ALERT" if alerts else "SAFE",
            "score": 1.0 if alerts else 0.0,
            "reasons": alerts
        }
