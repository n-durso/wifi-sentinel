class Strategy:
    def evaluate(self, event, history):
        """
        event: nuovo evento WiFi
        history: ultimi eventi visti dal sentinel
        return: dict con score e motivazione
        """
        raise NotImplementedError