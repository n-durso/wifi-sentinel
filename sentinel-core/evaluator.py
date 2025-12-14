from strategies.ssid_clone import SSIDCloneStrategy

class Evaluator:
    def __init__(self):
        self.strategies = [
            SSIDCloneStrategy(),
            # other strategies
        ]
        self.history = []

    def evaluate_event(self, event):
        scores = []
        reasons = []

        for s in self.strategies:
            result = s.evaluate(event, self.history)
            scores.append(result["score"])
            
            # CORREZIONE QUI: uso .get() invece dell'accesso diretto con []
            # Se la chiave 'reason' non esiste, restituisce None e non crasha.
            if result.get("reason"):
                reasons.append(result["reason"])

        total = sum(scores)

        if total >= 1.2:
            status = "EVIL_TWIN"
        elif total >= 0.5:
            status = "SUSPICIOUS"
        else:
            status = "SAFE"

        self.history.append(event)

        return {
            "status": status,
            "score": total,
            "reasons": reasons
        }