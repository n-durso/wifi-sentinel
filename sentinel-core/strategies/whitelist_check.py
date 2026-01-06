class WhitelistStrategy:
    def analyze(self, net, whitelist):
        
        ssid = net.get('ssid')
        bssid = net.get('bssid')
        channel = net.get('channel')

        # Se la rete non è nella whitelist, ritorniamo None, quindi la ignoriamo
        if ssid not in whitelist:
            return None

        known_data = whitelist[ssid]
        allowed_bssids = known_data.get('bssids', [])
        allowed_channels = known_data.get('channels', [])

        # 1. Controllo EVIL TWIN
        if bssid not in allowed_bssids:
            return {
                "score": 1.0,
                "type": "EVIL_TWIN",
                "message": f"EVIL TWIN RILEVATO! La rete '{ssid}' sta trasmettendo dal MAC sconosciuto {bssid} (Atteso: {allowed_bssids})"
            }

        # 2. Controllo anomalia canale
        if allowed_channels and channel not in allowed_channels:
            return {
                "score": 0.4,
                "type": "Sospetta",
                "message": f"Anomalia canale per la rete '{ssid}': Rilevato su Ch {channel}, atteso {allowed_channels}"
            }

        return None  # Rete nella whitelist senza anomalie