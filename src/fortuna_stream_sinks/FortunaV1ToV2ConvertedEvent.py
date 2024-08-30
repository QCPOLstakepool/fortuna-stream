class FortunaV1ToV2ConvertedEvent:
    def __init__(self, address: str, amount: int):
        self.address = address
        self.amount = amount

    def get_message(self):
        return f"{self.address[:12]}..{self.address[-4:]} converted {self.amount / 100000000} V1 $TUNA."
