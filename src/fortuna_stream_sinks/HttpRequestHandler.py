import json
import logging
import os
import base64
import binascii
import sys
from http.server import BaseHTTPRequestHandler
from TwitterAPI import TwitterAPI
from charset_normalizer.api import logger

from fortuna_stream_sinks.config import X_API_KEY
from fortuna_stream_sinks.config import X_API_KEY_SECRET
from fortuna_stream_sinks.config import X_ACCESS_TOKEN
from fortuna_stream_sinks.config import X_ACCESS_TOKEN_SECRET
from fortuna_stream_sinks.Process import Process

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
        HttpRequestHandler.logger.debug(f"P={"outputs" in post_body_json}")
        if "outputs" in post_body_json:
            outputs = list(filter(lambda output: "assets" in output, post_body_json["outputs"]))
            HttpRequestHandler.logger.debug(f"A={json.dumps(outputs)}")
            for output in outputs:
                outputs_assets = list(filter(lambda _output: "assets" in _output, output["assets"]))
                HttpRequestHandler.logger.debug(f"B={json.dumps(outputs_assets)}")
                for outputs_asset in outputs_assets:
                    outputs_assets_assets = list(filter(lambda _output: "name" in _output and _output["name"] == "VFVOQQ==", outputs_asset["assets"]))
                    HttpRequestHandler.logger.debug(f"C={json.dumps(outputs_assets_assets)}")
                    if len(outputs_assets_assets) == 1:
                        HttpRequestHandler.logger.debug(f"address={output["address"]}")
                        HttpRequestHandler.logger.debug(f"address b64decode={base64.b64decode(output["address"])}")
                        HttpRequestHandler.logger.debug(f"address hexlify={binascii.hexlify(base64.b64decode(output["address"]))}")
                        HttpRequestHandler.logger.debug(f"address hexlify decode={binascii.hexlify(base64.b64decode(output["address"])).decode()}")
                        address = Process.run("bech32 addr1", binascii.hexlify(base64.b64decode(output["address"])).decode())
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
            message = f"Block {block_number} mined by {address} (rewards: {mint_asset_amount / 100000000})"
            HttpRequestHandler.logger.info(message)

            x_response = HttpRequestHandler.x_api.request("tweets", {"text": message}, method_override="POST")

            HttpRequestHandler.logger.debug(f"X response: {x_response.text}")

            self.send_response(201)
            self.end_headers()

            sys.exit()
        else:
            self.send_response(204)
            self.end_headers()

    def not_found(self):
        self.send_response(404)
        self.end_headers()

    def bad_request(self):
        self.send_response(400)
        self.end_headers()
