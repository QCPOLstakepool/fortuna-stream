import json
import sys

import typer
from http.server import HTTPServer, BaseHTTPRequestHandler
from TwitterAPI import TwitterAPI
from config import X_API_KEY
from config import X_API_KEY_SECRET
from config import X_ACCESS_TOKEN
from config import X_ACCESS_TOKEN_SECRET

x_api = TwitterAPI(X_API_KEY, X_API_KEY_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, api_version="2")

class HttpRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/mints":
            self.post_mints()
        else:
            self.not_found()

    def post_mints(self):
        content_length = int(self.headers.get('Content-Length'))
        post_body_json = json.loads(self.rfile.read(content_length))

        mint_asset_amount = -1
        block_number = -1

        if "mint" in post_body_json:
            mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode

            if len(mint_assets_policy) == 1:
                mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ====", mint_assets_policy[0]["assets"]))  # TODO decode

                if len(mint_assets) == 1:
                    mint_asset_amount = mint_assets[0]["mintCoin"]

        if "outputs" in post_body_json:
            outputs_datum = list(filter(lambda output: "datumHash" in output, post_body_json["outputs"]))

            if len(outputs_datum) == 1:
                if "datum" in outputs_datum[0] and "constr" in outputs_datum[0]["datum"] and "fields" in outputs_datum[0]["datum"]["constr"]:
                    block_number = int(outputs_datum[0]["datum"]["constr"]["fields"][0]["bigInt"]["int"])

        if mint_asset_amount > 0 and block_number > 0:
            x_api.request("tweets", {"text": f"New block miner: {block_number}. Rewards: {mint_asset_amount / 100000000} $TUNA."}, method_override="POST")

            self.send_response(204)
            self.end_headers()

            sys.exit()
        else:
            self.bad_request()

    def not_found(self):
        self.send_response(404)
        self.end_headers()

    def bad_request(self):
        self.send_response(400)
        self.end_headers()



def main(host: str, port: int):
    server = HTTPServer((host, port), HttpRequestHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()

if __name__ == "__main__":
    typer.run(main)