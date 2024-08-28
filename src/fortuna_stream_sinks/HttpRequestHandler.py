import json
import logging
import os
import base64
import binascii
import sys
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
        if self.path == "/api/mints":
            self.post_mints()
        else:
            self.not_found()

    def post_mints(self):
        content_length = int(self.headers.get('Content-Length'))
        post_body_json = json.loads(self.rfile.read(content_length))

        HttpRequestHandler.logger.debug(post_body_json)

        address = None
        mint_asset_amount = -1
        block_number = -1
        leading_zeroes = -1
        difficulty = -1

        if "mint" in post_body_json:
            mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode

            if len(mint_assets_policy) == 1:
                mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ==", mint_assets_policy[0]["assets"]))  # TODO decode

                if len(mint_assets) == 1:
                    mint_asset_amount = int(mint_assets[0]["mintCoin"])

        if "outputs" in post_body_json:
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
                            address = Address(payment_part=payment_hash, staking_part=stake_hash, network=Network.MAINNET)
                        elif len(address_hex) == 58:
                            payment_hash = VerificationKeyHash(bytes.fromhex(address_hex[2:]))
                            address = Address(payment_part=payment_hash, network=Network.MAINNET)

                        break

                if address is not None:
                    break

            outputs_datum = list(filter(lambda output: "datumHash" in output, post_body_json["outputs"]))

            if len(outputs_datum) == 1:
                if "datum" in outputs_datum[0] and "constr" in outputs_datum[0]["datum"] and "fields" in outputs_datum[0]["datum"]["constr"] and "bigInt" in outputs_datum[0]["datum"]["constr"]["fields"][0]:
                    block_number = int(outputs_datum[0]["datum"]["constr"]["fields"][0]["bigInt"]["int"])
                    leading_zeroes = int(outputs_datum[0]["datum"]["constr"]["fields"][3]["bigInt"]["int"])
                    difficulty = int(outputs_datum[0]["datum"]["constr"]["fields"][4]["bigInt"]["int"])

        if mint_asset_amount > 0 and block_number > 0:
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

            self.send_response(201)
            self.end_headers()
        else:
            self.send_response(204)
            self.end_headers()

    def not_found(self):
        self.send_response(404)
        self.end_headers()

    def bad_request(self):
        self.send_response(400)
        self.end_headers()
