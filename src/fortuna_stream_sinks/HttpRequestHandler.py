import json
import logging
import os
from http.server import BaseHTTPRequestHandler
from TwitterAPI import TwitterAPI, TwitterResponse
from fortuna_stream_sinks.FortunaBlock import FortunaBlock
from fortuna_stream_sinks.FortunaConversion import FortunaConversion
from fortuna_stream_sinks.FortunaConversionEventHandler import FortunaConversionEventHandler
from fortuna_stream_sinks.FortunaMintEventHandler import FortunaMintEventHandler
from fortuna_stream_sinks.config import X_ENABLED
from fortuna_stream_sinks.config import X_API_KEY
from fortuna_stream_sinks.config import X_API_KEY_SECRET
from fortuna_stream_sinks.config import X_ACCESS_TOKEN
from fortuna_stream_sinks.config import X_ACCESS_TOKEN_SECRET


class HttpRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, database, *args, **kwargs):
        self.database = database
        self.logger = logging.getLogger("HttpRequestHandler")
        self.logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
        self.x_api = TwitterAPI(X_API_KEY, X_API_KEY_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, api_version="2") if X_ENABLED else None

        super().__init__(*args, **kwargs)

    def do_POST(self):
        if self.path == "/api/events":
            content_length = int(self.headers.get('Content-Length'))
            post_body_json = json.loads(self.rfile.read(content_length))

            self.logger.debug(post_body_json)

            if FortunaMintEventHandler.is_mint(post_body_json):
                fortuna_block = FortunaMintEventHandler.process_mint(post_body_json)

                self.database.insert_block(fortuna_block)

                self.logger.info(f"[Mint] Number={fortuna_block.number}, miner={fortuna_block.miner}, amount={fortuna_block.rewards}, leading zeroes={fortuna_block.leading_zeroes}, difficulty={fortuna_block.difficulty}")

                self.created()
            elif FortunaConversionEventHandler.is_conversion(post_body_json):
                fortuna_v1_to_v2_conversion = FortunaConversionEventHandler.process_conversion(post_body_json)

                self.database.insert_v1_to_v2_conversion(fortuna_v1_to_v2_conversion)

                self.logger.info(f"[Conversion V1 -> V2] Address={fortuna_v1_to_v2_conversion.address}, amount={fortuna_v1_to_v2_conversion.amount}")

                self.created()
            else:
                self.logger.debug("Transaction type not supported.")

                self.no_content()
        elif self.path == "/api/events/queued/send":
            self.send_queued_events()

            self.created()
        else:
            self.not_found()

    def send_queued_events(self):
        blocks: list[FortunaBlock] = self.database.get_blocks_not_posted_on_x()
        conversions: list[FortunaConversion] = self.database.get_conversions_not_posted_on_x()
        pools = {}

        if len(blocks) == 0 and len(conversions) == 0:
            self.logger.debug("Nothing in queue to send.")

            return

        if len(blocks) > 0:
            self.database.set_blocks_posted_on_x(blocks[0].number)

            with open("pools.json", "r") as pools_file:
                pools = json.load(pools_file)

        if len(conversions) > 0:
            self.database.set_conversions_posted_on_x(conversions[0].transaction.hash)

        blocks_per_address = {}
        for block in blocks:
            if block.miner not in blocks_per_address:
                blocks_per_address[block.miner] = []

            blocks_per_address[block.miner].append(block)

        conversions_per_address = {}
        for conversion in conversions:
            if conversion.address not in conversions_per_address:
                conversions_per_address[conversion.address] = 0

            conversions_per_address[conversion.address] += conversion.amount

        x_post = ""

        for address, address_blocks in blocks_per_address.items():
            address_block_numbers = list(map(lambda address_block: str(address_block.number), address_blocks))
            address_block_numbers_str = f"{address_block_numbers[0]}" if len(address_block_numbers) == 1 else f"{", ".join(address_block_numbers[:-1])} and {address_block_numbers[-1]}"

            if address in pools:
                x_post += f"Pool {pools[address]["name"]} mined block{"s" if len(blocks) > 1 else ""} {address_block_numbers_str}.\n"
            else:
                x_post += f"Miner {address[:9]}..{address[-4:]} mined block{"s" if len(blocks) > 1 else ""} {address_block_numbers_str}.\n"

        for address in conversions_per_address:
            x_post += f"{address[:9]}..{address[-4:]} converted {conversions_per_address[address]/100000000} $TUNA.\n"

        if len(x_post) > 280:
            x_post = x_post[0:277] + "..."

        self.send_x_post(x_post)

    def send_x_post(self, message: str) -> None:
        if self.x_api is None:
            self.logger.debug(f"X is disabled. The following message was not sent: {message}")
        else:
            x_response: TwitterResponse = self.x_api.request("tweets", {"text": message}, method_override="POST")

            self.logger.debug(f"X response headers: {json.dumps(dict(x_response.headers))}")
            self.logger.debug(f"X response: {x_response.text}")

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
