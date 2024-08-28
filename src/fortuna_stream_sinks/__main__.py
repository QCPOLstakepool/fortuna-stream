from dotenv import load_dotenv
load_dotenv()

import logging
import os
import typer
from http.server import HTTPServer
from fortuna_stream_sinks.HttpRequestHandler import HttpRequestHandler

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=os.environ.get("LOG_LEVEL", "INFO"),
)

def main(host: str, port: int):
    server = HTTPServer((host, port), HttpRequestHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()

if __name__ == "__main__":
    typer.run(main)