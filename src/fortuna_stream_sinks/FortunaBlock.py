from fortuna_stream_sinks.Transaction import Transaction


class FortunaBlock:
    def __init__(self, transaction: Transaction, number: int, miner: str, rewards: int, leading_zeroes: int, difficulty: int):
        self.transaction = transaction
        self.number = number
        self.miner = miner
        self.rewards = rewards
        self.leading_zeroes = leading_zeroes
        self.difficulty = difficulty
