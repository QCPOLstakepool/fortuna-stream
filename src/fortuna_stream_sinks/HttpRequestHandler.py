import json
import logging
from http.server import BaseHTTPRequestHandler
from TwitterAPI import TwitterAPI
from fortuna_stream_sinks.config import X_API_KEY
from fortuna_stream_sinks.config import X_API_KEY_SECRET
from fortuna_stream_sinks.config import X_ACCESS_TOKEN
from fortuna_stream_sinks.config import X_ACCESS_TOKEN_SECRET


class HttpRequestHandler(BaseHTTPRequestHandler):
    logger = logging.getLogger("fortuna_stream_sinks")
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
            outputs_datum = list(filter(lambda output: "datumHash" in output, post_body_json["outputs"]))

            if len(outputs_datum) == 1:
                if "datum" in outputs_datum[0] and "constr" in outputs_datum[0]["datum"] and "fields" in outputs_datum[0]["datum"]["constr"]:
                    block_number = int(outputs_datum[0]["datum"]["constr"]["fields"][0]["bigInt"]["int"])
                    leading_zeroes = int(outputs_datum[0]["datum"]["constr"]["fields"][3]["bigInt"]["int"])
                    difficulty = int(outputs_datum[0]["datum"]["constr"]["fields"][4]["bigInt"]["int"])

        if mint_asset_amount > 0 and block_number > 0:
            HttpRequestHandler.logger.info(f"Block {block_number} mined by (rewards: {mint_asset_amount})")
            x_response = HttpRequestHandler.x_api.request("tweets", {"text": f"New block mined: {block_number}. Rewards: {mint_asset_amount / 100000000} $TUNA."}, method_override="POST")

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
