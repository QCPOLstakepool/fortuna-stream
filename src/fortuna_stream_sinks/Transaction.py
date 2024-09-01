class Transaction:
    VERSION = 1

    def __init__(self, hash: str, validity_from: int, validity_to: int, version: int, raw_json: str):
        self.hash = hash
        self.validity_from = validity_from
        self.validity_to = validity_to
        self.version = version
        self.raw_json = raw_json