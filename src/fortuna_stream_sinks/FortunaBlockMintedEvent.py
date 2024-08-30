import json


class FortunaBlockMintedEvent:
    def __init__(self, number: int, address: str, rewards: int, leading_zeroes: int, difficulty: int):
        self.number = number
        self.address = address
        self.rewards = rewards
        self.leading_zeroes = leading_zeroes
        self.difficulty = difficulty

    def get_message(self) -> str:
        with open("pools.json", "r") as pools_file:
            pools = json.load(pools_file)

        pool = list(filter(lambda _pool: _pool["address"] == self.address, pools))

        if len(pool) == 1:
            return f"Block {self.number} mined by pool {pool[0]["name"]}."
        else:
            return f"Block {self.number} mined by {self.address[:12]}..{self.address[-4:]}."
