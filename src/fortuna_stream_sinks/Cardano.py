import base64
import binascii
from pycardano import ScriptHash, VerificationKeyHash, Address, Network, TransactionId


class Cardano:
    @staticmethod
    def get_transaction_hash(transaction_hash_base64_encoded_bytes: str) -> str:
        hash_bytes = base64.b64decode(transaction_hash_base64_encoded_bytes)
        transaction = TransactionId(hash_bytes)

        return str(transaction)

    @staticmethod
    def get_bech32_payment_address(base64_encoded_hex: str) -> str:
        return Address(payment_part=Cardano._get_address(base64_encoded_hex).payment_part, network=Network.MAINNET).encode()

    @staticmethod
    def get_bech32_address(base64_encoded_hex: str) -> str:
        try:
            return Cardano._get_address(base64_encoded_hex).encode()
        except Exception:
            return "unknown address"

    @staticmethod
    def _get_address(base64_encoded_hex: str) -> Address:
        address_hex = binascii.hexlify(base64.b64decode(base64_encoded_hex)).decode()

        if len(address_hex) == 114:
            if address_hex[0] == "1":
                payment_hash = ScriptHash(bytes.fromhex(address_hex[2:58]))
                stake_hash = VerificationKeyHash(bytes.fromhex(address_hex[58:]))
            elif address_hex[0] == "2":
                payment_hash = VerificationKeyHash(bytes.fromhex(address_hex[2:58]))
                stake_hash = ScriptHash(bytes.fromhex(address_hex[58:]))
            elif address_hex[0] == "3":
                payment_hash = ScriptHash(bytes.fromhex(address_hex[2:58]))
                stake_hash = ScriptHash(bytes.fromhex(address_hex[58:]))
            else:
                payment_hash = VerificationKeyHash(bytes.fromhex(address_hex[2:58]))
                stake_hash = VerificationKeyHash(bytes.fromhex(address_hex[58:]))

            return Address(payment_part=payment_hash, staking_part=stake_hash, network=Network.MAINNET)
        elif len(address_hex) == 58:
            if address_hex[0] == "7":
                payment_hash = ScriptHash(bytes.fromhex(address_hex[2:]))
            else:
                payment_hash = VerificationKeyHash(bytes.fromhex(address_hex[2:]))

            return Address(payment_part=payment_hash, network=Network.MAINNET)

        raise Exception(f"invalid address: {base64_encoded_hex}")