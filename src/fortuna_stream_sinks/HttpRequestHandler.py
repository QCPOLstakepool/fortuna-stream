import json
import logging
import os
import base64
import binascii
from http.server import BaseHTTPRequestHandler
from TwitterAPI import TwitterAPI
from pycardano import VerificationKeyHash, Address, Network

from fortuna_stream_sinks.config import X_API_KEY
from fortuna_stream_sinks.config import X_API_KEY_SECRET
from fortuna_stream_sinks.config import X_ACCESS_TOKEN
from fortuna_stream_sinks.config import X_ACCESS_TOKEN_SECRET

class HttpRequestHandler(BaseHTTPRequestHandler):
    logger = logging.getLogger("HttpRequestHandler")
    logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
    x_api = TwitterAPI(X_API_KEY, X_API_KEY_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, api_version="2")

    def do_POST(self):
        if self.path == "/api/events":
            content_length = int(self.headers.get('Content-Length'))
            post_body_json = json.loads(self.rfile.read(content_length))

            HttpRequestHandler.logger.debug(post_body_json)

            if HttpRequestHandler.is_mint(post_body_json):
                HttpRequestHandler.post_mint(post_body_json)

                self.created()
            elif HttpRequestHandler.is_conversion(post_body_json):
                HttpRequestHandler.post_conversion(post_body_json)

                self.created()
            else:
                self.no_content()
        else:
            self.not_found()

    @staticmethod
    def is_mint(post_body_json) -> bool:
        if "mint" not in post_body_json:
            return False

        mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode to asset1up3fehe0dwpuj4awgcuvl0348vnsexd573fjgq
        if len(mint_assets_policy) != 1:
            return False

        mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ==", mint_assets_policy[0]["assets"]))
        if len(mint_assets) != 1:
            return False

        if "outputs" not in post_body_json:
            return False

        outputs_datum = list(filter(lambda output: "datumHash" in output, post_body_json["outputs"]))
        if len(outputs_datum) != 1:
            return False

        output_datum = outputs_datum[0]

        return "datum" in output_datum and \
            "constr" in output_datum["datum"] and \
            "fields" in output_datum["datum"]["constr"] and \
            len(output_datum["datum"]["constr"]["fields"]) == 7 and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][0] and \
            "int" in output_datum["datum"]["constr"]["fields"][0]["bigInt"] and \
            "boundedBytes" in output_datum["datum"]["constr"]["fields"][1] and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][2] and \
            "int" in output_datum["datum"]["constr"]["fields"][2]["bigInt"] and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][3] and \
            "int" in output_datum["datum"]["constr"]["fields"][3]["bigInt"] and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][4] and \
            "int" in output_datum["datum"]["constr"]["fields"][4]["bigInt"] and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][5] and \
            "int" in output_datum["datum"]["constr"]["fields"][5]["bigInt"] and \
            "boundedBytes" in output_datum["datum"]["constr"]["fields"][6]

    @staticmethod
    def is_conversion(post_body_json) -> bool:
        return False

    @staticmethod
    def post_mint(post_body_json):
        address = HttpRequestHandler.get_mint_miner_address(post_body_json)
        mint_asset_amount = HttpRequestHandler.get_mint_amount(post_body_json)
        block_number, leading_zeroes, difficulty = HttpRequestHandler.get_mint_data(post_body_json)

        with open("pools.json", "r") as pools_file:
            pools = json.load(pools_file)

        pool = list(filter(lambda _pool: _pool["address"] == address, pools))

        if len(pool) == 1:
            message = f"Block {block_number} mined by pool {pool[0]["name"]} ({pool[0]["website"]}) (rewards: {mint_asset_amount / 100000000})."
        else:
            message = f"Block {block_number} mined by solo miner {address[:12]}...{address[-4:]} (rewards: {mint_asset_amount / 100000000})."

        HttpRequestHandler.logger.info(message)

        x_response = HttpRequestHandler.x_api.request("tweets", {"text": message}, method_override="POST")

        HttpRequestHandler.logger.debug(f"X response: {x_response.text}")

    @staticmethod
    def post_conversion(post_body_json):
        pass

    @staticmethod
    def get_mint_miner_address(post_body_json) -> str:
        outputs = list(filter(lambda output: "assets" in output, post_body_json["outputs"]))

        for output in outputs:
            outputs_assets = list(filter(lambda _output: "assets" in _output, output["assets"]))

            for outputs_asset in outputs_assets:
                outputs_assets_assets = list(filter(lambda _output: "name" in _output and _output["name"] == "VFVOQQ==", outputs_asset["assets"]))

                if len(outputs_assets_assets) == 1:
                    address_hex = binascii.hexlify(base64.b64decode(output["address"])).decode()

                    if len(address_hex) == 114:
                        payment_hash = VerificationKeyHash(bytes.fromhex(address_hex[2:58]))
                        stake_hash = VerificationKeyHash(bytes.fromhex(address_hex[58:]))
                        return Address(payment_part=payment_hash, staking_part=stake_hash, network=Network.MAINNET).encode()
                    elif len(address_hex) == 58:
                        payment_hash = VerificationKeyHash(bytes.fromhex(address_hex[2:]))
                        return Address(payment_part=payment_hash, network=Network.MAINNET).encode()

        return "unknown address"

    @staticmethod
    def get_mint_amount(post_body_json) -> int:
        mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode to asset1up3fehe0dwpuj4awgcuvl0348vnsexd573fjgq
        mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ==", mint_assets_policy[0]["assets"]))  # TODO decode

        return int(mint_assets[0]["mintCoin"])

    @staticmethod
    def get_mint_data(post_body_json) -> (int, int, int):
        outputs_datum = list(filter(lambda output: "datumHash" in output, post_body_json["outputs"]))

        return int(outputs_datum[0]["datum"]["constr"]["fields"][0]["bigInt"]["int"]), \
            int(outputs_datum[0]["datum"]["constr"]["fields"][3]["bigInt"]["int"]), \
            int(outputs_datum[0]["datum"]["constr"]["fields"][4]["bigInt"]["int"])

    def created(self):
        self.send_response(201)
        self.end_headers()

    def no_content(self):
        self.send_response(204)
        self.end_headers()

    def not_found(self):
        self.send_response(404)
        self.end_headers()

    def bad_request(self):
        self.send_response(400)
        self.end_headers()
