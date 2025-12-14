import collections

class SSIDCloneStrategy:
    # Canali 1-14 sono 2.4GHz. Canali > 14 (es. 36, 100) sono 5GHz.
    CHAN_2_4_GHZ_MAX = 14
    
    def evaluate(self, event, history):
        networks = event.get("networks", [])
        
        # Raggruppa le reti per SSID
        ssid_map = collections.defaultdict(list)
        for net in networks:
            ssid_map[net["ssid"]].append(net)
            
        score = 0.0
        reasons = []

        for ssid, nets in ssid_map.items():
            # Se c'è solo una rete con questo nome nesssun problema
            if len(nets) < 2:
                continue
            
            # --- ANALISI DEL DUPLICATO ---
            bssid_count = len(nets)
            
            # Controllo se è un router Dual-Band legittimo
            is_dual_band = False
            if bssid_count == 2:
                chan_1 = nets[0]["channel"]
                chan_2 = nets[1]["channel"]
                
                # Verifica se uno è 2.4GHz e l'altro è 5GHz
                is_band_1_24 = chan_1 <= self.CHAN_2_4_GHZ_MAX
                is_band_2_24 = chan_2 <= self.CHAN_2_4_GHZ_MAX
                
                if is_band_1_24 != is_band_2_24:
                    is_dual_band = True
            
            # --- DECISIONE ---
            if is_dual_band:
                # È un router moderno legittimo --> Nessun allarme --> punteggio 0 --> SAFE
                score += 0.0
            else:
                # CASO EVIL TWIN / CLONE
                risk = 1.5 # Supera la soglia di 1.2 -> EVIL_TWIN
                score += risk
                
                # Stringa per spiegare chi è sospetto
                reasons.append(f"Rete '{ssid}': Rilevati {bssid_count} access point sospetti (BSSID multipli non compatibili con Dual-Band)")

        return {
            "score": score,
            "reason": "; ".join(reasons) if reasons else None
        }