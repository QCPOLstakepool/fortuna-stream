import json
import logging
import os
from http.server import BaseHTTPRequestHandler
from typing import Union
from TwitterAPI import TwitterAPI, TwitterResponse
from fortuna_stream_sinks.FortunaBlockMintedEvent import FortunaBlockMintedEvent
from fortuna_stream_sinks.FortunaConversionEventHandler import FortunaConversionEventHandler
from fortuna_stream_sinks.FortunaMintEventHandler import FortunaMintEventHandler
from fortuna_stream_sinks.FortunaV1ToV2ConvertedEvent import FortunaV1ToV2ConvertedEvent
from fortuna_stream_sinks.config import X_ENABLED
from fortuna_stream_sinks.config import X_API_KEY
from fortuna_stream_sinks.config import X_API_KEY_SECRET
from fortuna_stream_sinks.config import X_ACCESS_TOKEN
from fortuna_stream_sinks.config import X_ACCESS_TOKEN_SECRET


class HttpRequestHandler(BaseHTTPRequestHandler):
    logger = logging.getLogger("HttpRequestHandler")
    logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
    x_api = TwitterAPI(X_API_KEY, X_API_KEY_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, api_version="2") if X_ENABLED else None
    events_queue: list[Union[FortunaBlockMintedEvent, FortunaV1ToV2ConvertedEvent]] = []

    def do_POST(self):
        if self.path == "/api/events":
            content_length = int(self.headers.get('Content-Length'))
            post_body_json = json.loads(self.rfile.read(content_length))

            HttpRequestHandler.logger.debug(post_body_json)

            if FortunaMintEventHandler.is_mint(post_body_json):
                event = FortunaMintEventHandler.process_mint(post_body_json)

                HttpRequestHandler.events_queue.append(event)

                HttpRequestHandler.logger.info(f"Mint: number={event.number}, miner={event.address}, amount={event.rewards}, leading zeroes={event.leading_zeroes}, difficulty={event.difficulty}")

                self.created()
            elif FortunaConversionEventHandler.is_conversion(post_body_json):
                event = FortunaConversionEventHandler.process_conversion(post_body_json)

                HttpRequestHandler.events_queue.append(event)

                HttpRequestHandler.logger.info(f"Conversion: address={event.address}, amount={event.amount}")

                self.created()
            else:
                HttpRequestHandler.logger.debug("Transaction type not supported.")

                self.no_content()
        elif self.path == "/api/events/queued/send":
            HttpRequestHandler.send_queued_events()

            self.created()
        else:
            self.not_found()

    @staticmethod
    def send_queued_events():
        if len(HttpRequestHandler.events_queue) == 0:
            HttpRequestHandler.logger.debug("Nothing in queue to send.")

            return

        x_post = ""

        for event in reversed(HttpRequestHandler.events_queue):
            x_post += event.get_message() + "\n"

        x_post = "In the last 30 minutes:\n" + x_post[:-1]

        if len(x_post) > 280:
            x_post = x_post[0:277] + "..."

        HttpRequestHandler.events_queue = []
        HttpRequestHandler.send_x_post(x_post)

    @staticmethod
    def send_x_post(message: str) -> None:
        if HttpRequestHandler.x_api is None:
            HttpRequestHandler.logger.debug(f"X is disabled. The following message was not sent: {message}")
        else:
            x_response: TwitterResponse = HttpRequestHandler.x_api.request("tweets", {"text": message}, method_override="POST")

            HttpRequestHandler.logger.debug(f"X response headers: {json.dumps(dict(x_response.headers))}")
            HttpRequestHandler.logger.debug(f"X response: {x_response.text}")


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
