from fortuna_stream_sinks.Transaction import Transaction


class FortunaConversion:
    def __init__(self, transaction: Transaction, address: str, amount: int, from_version: int, to_version: int):
        self.transaction = transaction
        self.address = address
        self.amount = amount
        self.from_version = from_version
        self.to_version = to_version