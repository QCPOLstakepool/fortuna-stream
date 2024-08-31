from functools import partial

from dotenv import load_dotenv

from fortuna_stream_sinks.Database import Database

load_dotenv()

import logging
import typer
from http.server import HTTPServer
from fortuna_stream_sinks.HttpRequestHandler import HttpRequestHandler

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

def main(host: str, port: int):
    database = Database("fortuna_stream.db")
    database.migrate()

    handler = partial(HttpRequestHandler, database)
    server = HTTPServer((host, port), handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()

if __name__ == "__main__":
    typer.run(main)