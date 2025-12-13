from strategies.base_strategy import Strategy
class SSIDCloneStrategy(Strategy):
    def evaluate(self, event, history):
        same_ssid = [h for h in history if h["ssid"] == event["ssid"]
                     and h["bssid"] != event["bssid"]]

        if same_ssid:
            return {
                "score": 0.6,
                "reason": "SSID duplicate with different BSSID"
            }

        return {"score": 0.0, "reason": ""}