from fortuna_stream_sinks.Transaction import Transaction


class FortunaSundaeSwapV3OrderBuy:
    def __init__(self, transaction: Transaction, address: str, in_amount_lovelace: int, min_out_amount_tuna: int):
        self.transaction = transaction
        self.address = address
        self.in_amount_lovelace = in_amount_lovelace
        self.min_out_amount_tuna = min_out_amount_tuna