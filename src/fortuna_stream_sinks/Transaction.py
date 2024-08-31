class Transaction:
    def __init__(self, hash: str, validity_from: int, validity_to: int):
        self.hash = hash
        self.validity_from = validity_from
        self.validity_to = validity_to